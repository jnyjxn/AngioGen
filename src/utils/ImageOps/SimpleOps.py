import copy
import numpy as np
import skimage.transform

from PIL import Image

from ..MatrixCalculator import MatrixCalculator

def crop(image, depth, matrix, **config):
	aspect_ratio = config.get("aspect_ratio")
	x = config.get("x")
	y = config.get("y")
	scale_y = config.get("scale_y")
	scale_x = config.get("scale_x")

	initial_image_width, initial_image_height = image.shape[1], image.shape[0]
	initial_aspect_ratio = initial_image_width/initial_image_height

	assert not (aspect_ratio is None and x is None and y is None), f"Crop must have either (x and y) or (aspect_ratio)"
	assert x is None or x <= initial_image_width, f"Crop 'x' value cannot be greater than image width ({x} vs {initial_image_width})"
	assert y is None or y <= initial_image_height, f"Crop 'y' value cannot be greater than image height ({y} vs {initial_image_height})"
	assert not (x is not None and scale_x is not None), 'Crop must have only either "x" or "scale_x" but it has both'
	assert not (y is not None and scale_y is not None), 'Crop must have only either "y" or "scale_y" but it has both'
	assert aspect_ratio is None or aspect_ratio > 0, f"Crop 'aspect_ratio' must be greater than 0"

	if aspect_ratio is not None and x is None and y is None:
		if aspect_ratio <= initial_aspect_ratio:
			y = initial_image_height

			# Aspect ratio of 1 is often strongly required (e.g. deep learning)
			#   so enforce it strongly
			if aspect_ratio == 1:
				x = y
			else:
				x = int(y*aspect_ratio)
		else:
			x = initial_image_width

			if aspect_ratio == 1:
				y = x
			else:
				y = int(x/aspect_ratio)
	elif x is None and aspect_ratio is not None:
		x = int(y*aspect_ratio)
		assert x <= initial_image_width, f"Crop with 'aspect_ratio' of {aspect_ratio} leads to x > image shape ({x} vs {initial_image_width})"
	elif y is None and aspect_ratio is not None:
		y = int(x/aspect_ratio)
		assert y <= initial_image_height, f"Crop with 'aspect_ratio' of {aspect_ratio} leads to y > image shape ({y} vs {initial_image_height})"

	if x is None:
		x = initial_image_width
	if y is None:
		y = initial_image_height

	x = x if x > 0 else 1
	y = y if y > 0 else 1

	from_x = (initial_image_width - x)//2
	from_y = (initial_image_height - y)//2

	to_x = from_x + x
	to_y = from_y + y

	'''Image'''
	im_was_flat = len(image.shape) == 2

	# Make sure it is 3D
	if im_was_flat:
		image = image.reshape(initial_image_width,initial_image_height,-1)

	image = image[from_y:to_y,from_x:to_x,:]

	if im_was_flat:
		image = np.squeeze(image)


	'''Depth'''
	dpt_was_flat = len(image.shape) == 2

	# Make sure it is 3D
	if dpt_was_flat:
		depth = depth.reshape(initial_image_width,initial_image_height,-1)

	depth = depth[from_y:to_y,from_x:to_x,:]

	if im_was_flat:
		depth = np.squeeze(depth)


	'''Matrix'''
	# Speed things up if all intrinsic matrices are the same (i.e. the camera hasn't e.g. changed zoom during sequence)
	if np.all(matrix["K"].T == matrix["K"][:,:,0].T):
		intrinsic_params = MatrixCalculator.intrinsicToParams(matrix["K"][:,:,0])
		new_K = MatrixCalculator.camParamsToIntrinsic(fx=intrinsic_params["fx"],fy=intrinsic_params["fy"],image_dims=(x,y))
		matrix["K"] = np.dstack([new_K]*matrix["K"].shape[2])
	else:
		new_K_stack = []
		for i in range(matrix["K"].shape[2]):
			intrinsic_params = MatrixCalculator.intrinsicToParams(matrix["K"][:,:,i])
			new_K = MatrixCalculator.camParamsToIntrinsic(fx=intrinsic_params["fx"],fy=intrinsic_params["fy"],image_dims=(x,y))
			new_K_stack.append(new_K)
		matrix["K"] = np.dstack(new_K_stack)

	return image, depth, matrix

def resize(image, depth, matrix, **config):
	keep_aspect_ratio = config.get("keep_aspect_ratio", False)
	x = config.get("x")
	y = config.get("y")
	scale = config.get("scale")
	scale_x = config.get("scale_x")
	scale_y = config.get("scale_y")
	interpolation_order = config.get("interpolation_order", 1)

	initial_image_width, initial_image_height = image.shape[1], image.shape[0]
	initial_aspect_ratio = initial_image_width/initial_image_height

	assert x is not None or y is not None or scale_x is not None or scale_y is not None or scale is not None, 'Resize is not doing anything as it is missing x, y or scale'
	assert not (x is not None and scale_x is not None), 'Resize must have only either "x" or "scale_x" but it has both'
	assert not (y is not None and scale_y is not None), 'Resize must have only either "y" or "scale_y" but it has both'
	assert not (scale is not None and (scale_x is not None or scale_y is not None)), f'Resize cannot use both "scale" and "scale_{"x" if scale_x is not None else "y"}"'

	if scale is not None:
		scale_x, scale_y = scale, scale

	# If scale_x and scale_y are being used, get x and y from them
	if scale_x is not None: x = scale_x * initial_image_width
	if scale_y is not None: y = scale_y * initial_image_height

	# If x and y are being used, get scale_x and scale_y from them
	if scale_x is None: scale_x = x / initial_image_width if x is not None else 1
	if scale_y is None: scale_y = y / initial_image_height if y is not None else 1


	# We can't keep aspect ratio if the x and y values are both given and have a different aspect ratio
	if keep_aspect_ratio and x is not None and y is not None:
		assert x/y == initial_aspect_ratio, f"Resize cannot keep aspect ratio with given x and y ({initial_aspect_ratio} vs {x/y})"

	# If we should keep the aspect ratio, calculate x and y to do so
	if keep_aspect_ratio:
		if x is None:
			x = int(y*initial_aspect_ratio)
		if y is None:
			y = int(x/initial_aspect_ratio)

	# If x/y weren't set by the user, scale_x/y, nor by keeping aspect ratio, they shouldn't change
	if x is None: x = initial_image_width
	if y is None: y = initial_image_height


	'''Image'''
	im_was_flat = len(image.shape) == 2

	# Make sure it is 3D
	if im_was_flat:
		image = image.reshape(initial_image_data_width,initial_image_data_height,-1)

	min_before = image[np.nonzero(image)].min()
	image_max_before = image.max()
	image = skimage.transform.resize(image, (y,x,image.shape[2]), order=interpolation_order)
	image_max_after = image.max()
	image *= image_max_before/image_max_after

	image[image < min_before] = 0

	if im_was_flat:
		image = np.squeeze(image)


	'''Depth'''
	dpt_was_flat = len(depth.shape) == 2

	# Make sure it is 3D
	if dpt_was_flat:
		depth = depth.reshape(initial_image_data_width,initial_image_data_height,-1)

	min_before = depth[np.nonzero(depth)].min()
	image_max_before = depth.max()
	depth = skimage.transform.resize(depth, (y,x,depth.shape[2]), order=interpolation_order)
	image_max_after = depth.max()
	depth *= image_max_before/image_max_after

	depth[depth < min_before] = 0

	if dpt_was_flat:
		depth = np.squeeze(depth)


	'''Matrix'''
	# Speed things up if all intrinsic matrices are the same (i.e. the camera hasn't e.g. changed zoom during sequence)
	if np.all(matrix["K"].T == matrix["K"][:,:,0].T):
		intrinsic_params = MatrixCalculator.intrinsicToParams(matrix["K"][:,:,0])
		new_K = MatrixCalculator.camParamsToIntrinsic(fx=intrinsic_params["fx"],fy=intrinsic_params["fy"],image_dims=(x,y))
		matrix["K"] = np.dstack([new_K]*matrix["K"].shape[2])
	else:
		new_K_stack = []
		for i in range(matrix["K"].shape[2]):
			intrinsic_params = MatrixCalculator.intrinsicToParams(matrix["K"][:,:,i])
			new_K = MatrixCalculator.camParamsToIntrinsic(fx=intrinsic_params["fx"],fy=intrinsic_params["fy"],image_dims=(x,y))
			new_K_stack.append(new_K)
		matrix["K"] = np.dstack(new_K_stack)

	return image, depth, matrix
