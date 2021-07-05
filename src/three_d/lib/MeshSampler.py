# Copyright 2019 Lars Mescheder, Michael Oechsle, Michael Niemeyer, Andreas Geiger, Sebastian Nowozin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import trimesh
import numpy as np
from pathlib import Path
from scipy import ndimage

from .triangle_hasher.triangle_hash import TriangleHash as _TriangleHash
from .libvoxelize.voxelize import voxelize_mesh_


class MeshSampler(object):
	@classmethod
	def sample(cls, path, get_points=True, get_pointcloud=True, get_voxels=True, points_size=100000, points_uniform_ratio=0.9, pointcloud_size=2048, voxels_res=32, resize=True, overwrite=False):
		points, occupancies, pointcloud, voxels, normalised_mesh, loc, scale = cls.get_data(
			path, 
			get_points=get_points,
			get_pointcloud=get_pointcloud,
			get_voxels=get_voxels,
			points_size=points_size, 
			points_uniform_ratio=points_uniform_ratio,
			pointcloud_size=pointcloud_size,
			voxels_res=voxels_res, 
			resize=resize, 
			overwrite=overwrite
		)

		cls.save_data(path, points, occupancies, pointcloud, voxels, normalised_mesh, loc, scale)

	@classmethod
	def get_data(cls, path, get_points=True, get_pointcloud=True, get_voxels=True,resize=False,bbox_padding=0,
						rotate_xz=0, voxels_res=32, points_size=100000, points_uniform_ratio=1., pointcloud_size=2048, overwrite=False):
		if not overwrite and (path / "points.npz").exists():
			get_points = False
		
		if not overwrite and (path / "pointcloud.npy").exists():
			get_pointcloud = False

		if not overwrite and (path / "model.binvox").exists():
			get_voxels = False

		if not get_points and not get_pointcloud and not get_voxels: return (None,) * 7

		mesh = trimesh.load(path / "mesh.ply",process=False)
		if not mesh.is_watertight:
			print(f"WARNING: Mesh {path}/mesh.ply is not watertight. Consider reducing mesh resolution.")

		# Determine bounding box
		if not resize:
			# Standard bounding boux
			loc = np.zeros(3)
			scale = 1.
		else:
			bbox = mesh.bounding_box.bounds

			# Compute location and scale
			loc = (bbox[0]+bbox[1])/2
			scale = (bbox[1]-bbox[0]).max()/(1-bbox_padding)

			# Transform input mesh
			mesh.apply_translation(-loc)
			mesh.apply_scale(1 / scale)

			if rotate_xz != 0:
				angle = rotate_xz / 180 * np.pi
				R = trimesh.transformations.rotation_matrix(angle,[0,1,0])
				mesh.apply_transform(R)

		try:
			voxels = cls.get_voxels(mesh,loc,scale,voxels_res=voxels_res) if get_voxels else None
			points, occupancies = cls.get_points(mesh,loc,scale,points_size=points_size,points_uniform_ratio=points_uniform_ratio) if get_points else (None, None)
			pointcloud = cls.get_pointcloud(mesh, pointcloud_size) if get_pointcloud else None
		except Exception as e:
			print(f"Error with item {ply_file}: {e}")
			return (None,) * 7

		return points, occupancies, pointcloud, voxels, mesh, loc, scale

	@classmethod
	def save_data(cls, path, points=None, occupancies=None, pointcloud=None, voxels=None, normalised_mesh=None, loc=None, scale=None):

		if voxels is not None:
			with open(path / "model.binvox","wb") as f:
				voxels.write(f)

		if points is not None:
			np.savez(path / "points.npz", points=points, occupancies=occupancies, loc=loc, scale=scale)
		
		if pointcloud is not None:
			np.save(path / "pointcloud.npy", pointcloud)

		if normalised_mesh is not None:
			normalised_mesh.export(path / "normalised_mesh.ply")
			normalised_mesh.export(path / "normalised_mesh.stl")

	@classmethod
	def get_voxels(cls, mesh, loc, scale, voxels_res=32):
		res = voxels_res
		voxels_occ = cls.voxelize_ray(mesh, res)

		voxels_out = Voxels(voxels_occ, (res,) * 3,
									  translate=loc, scale=scale,
									  axis_order='xyz')

		return voxels_out

	@classmethod
	def get_points(cls, mesh, loc, scale, points_size=100000, points_uniform_ratio=1.,
							points_padding=0.1, points_sigma=0.01):

		n_points_uniform = int(points_size * points_uniform_ratio)
		n_points_surface = points_size - n_points_uniform

		boxsize = 1 + points_padding
		np.random.seed(1)
		points_uniform = np.random.rand(n_points_uniform, 3)
		points_uniform = boxsize * (points_uniform - 0.5)
		points_surface = mesh.sample(n_points_surface)
		points_surface += points_sigma * np.random.randn(n_points_surface, 3)
		points = np.concatenate([points_uniform, points_surface], axis=0)

		occupancies = cls.check_mesh_contains(mesh, points)

		points = points.astype(np.float32)
		return points, occupancies

	@classmethod
	def get_pointcloud(cls, mesh, pointcloud_size=2048):
		return mesh.sample(pointcloud_size)

	@classmethod
	def check_mesh_contains(cls, mesh, points, hash_resolution=512):
		intersector = MeshIntersector(mesh, hash_resolution)
		contains = intersector.query(points)
		return contains

	@classmethod
	def voxelize_ray(cls, mesh, resolution):
		occ_surface = cls.voxelize_surface(mesh, resolution)
		# TODO: use surface voxels here?
		occ_interior = cls.voxelize_interior(mesh, resolution).transpose([1,0,2])
		occ = (occ_interior | occ_surface)
		# occ = occ_interior
		return occ

	@classmethod
	def voxelize_fill(cls, mesh, resolution):
		bounds = mesh.bounds
		if (np.abs(bounds) >= 0.5).any():
			raise ValueError('voxelize fill is only supported if mesh is inside [-0.5, 0.5]^3/')

		occ = cls.voxelize_surface(mesh, resolution)
		occ = ndimage.morphology.binary_fill_holes(occ)
		return occ

	@classmethod
	def voxelize_surface(cls, mesh, resolution):
		vertices = mesh.vertices
		faces = mesh.faces

		vertices = (vertices + 0.5) * resolution

		face_loc = vertices[faces]
		occ = np.full((resolution,) * 3, 0, dtype=np.int32)
		face_loc = face_loc.astype(np.float32)

		voxelize_mesh_(occ, face_loc)
		occ = (occ != 0)

		return occ

	@classmethod
	def voxelize_interior(cls, mesh, resolution):
		shape = (resolution,) * 3
		bb_min = (0.5,) * 3
		bb_max = (resolution - 0.5,) * 3
		# Create points. Add noise to break symmetry
		points = cls.make_3d_grid(bb_min, bb_max, shape=shape)
		points = points + 0.1 * (np.random.rand(*points.shape) - 0.5)
		points = (points / resolution - 0.5)
		occ = cls.check_mesh_contains(mesh, points)
		occ = occ.reshape(shape)
		return occ

	@classmethod
	def make_3d_grid(cls, bb_min, bb_max, shape):
		''' Makes a 3D grid.

		Args:
			bb_min (tuple): bounding box minimum
			bb_max (tuple): bounding box maximum
			shape (tuple): output shape
		'''

		size = shape[0] * shape[1] * shape[2]

		pxs = np.linspace(bb_min[0], bb_max[0], shape[0])
		pys = np.linspace(bb_min[1], bb_max[1], shape[1])
		pzs = np.linspace(bb_min[2], bb_max[2], shape[2])

		p = np.vstack(np.meshgrid(pxs,pys,pzs)).reshape(3,-1).T

		return p


class MeshIntersector:
	def __init__(self, mesh, resolution=512):
		triangles = mesh.vertices[mesh.faces].astype(np.float64)
		n_tri = triangles.shape[0]

		# scale = (resolution - 1) / (mesh.bounds[1] - mesh.bounds[0])
		# translate = 0.5 - scale * mesh.bounds[0]
		# print(scale, translate)

		self.resolution = resolution
		self.bbox_min = triangles.reshape(3 * n_tri, 3).min(axis=0)
		self.bbox_max = triangles.reshape(3 * n_tri, 3).max(axis=0)
		# Tranlate and scale it to [0.5, self.resolution - 0.5]^3
		self.scale = (resolution - 1) / (self.bbox_max - self.bbox_min)
		self.translate = 0.5 - self.scale * self.bbox_min

		self._triangles = triangles = self.rescale(triangles)
		# assert(np.allclose(triangles.reshape(-1, 3).min(0), 0.5))
		# assert(np.allclose(triangles.reshape(-1, 3).max(0), resolution - 0.5))

		triangles2d = triangles[:, :, :2]
		self._tri_intersector2d = TriangleIntersector2d(
			triangles2d, resolution)

	def query(self, points):
		# Rescale points
		points = self.rescale(points)

		# placeholder result with no hits we'll fill in later
		contains = np.zeros(len(points), dtype=np.bool)

		# cull points outside of the axis aligned bounding box
		# this avoids running ray tests unless points are close
		inside_aabb = np.all(
			(0 <= points) & (points <= self.resolution), axis=1)
		if not inside_aabb.any():
			return contains

		# Only consider points inside bounding box
		mask = inside_aabb
		points = points[mask]

		# Compute intersection depth and check order
		points_indices, tri_indices = self._tri_intersector2d.query(points[:, :2])

		triangles_intersect = self._triangles[tri_indices]
		points_intersect = points[points_indices]

		depth_intersect, abs_n_2 = self.compute_intersection_depth(
			points_intersect, triangles_intersect)

		# Count number of intersections in both directions
		smaller_depth = depth_intersect >= points_intersect[:, 2] * abs_n_2
		bigger_depth = depth_intersect < points_intersect[:, 2] * abs_n_2
		points_indices_0 = points_indices[smaller_depth]
		points_indices_1 = points_indices[bigger_depth]

		nintersect0 = np.bincount(points_indices_0, minlength=points.shape[0])
		nintersect1 = np.bincount(points_indices_1, minlength=points.shape[0])

		# Check if point contained in mesh
		contains1 = (np.mod(nintersect0, 2) == 1)
		contains2 = (np.mod(nintersect1, 2) == 1)
		if (contains1 != contains2).any():
			print('Warning: contains1 != contains2 for some points.')
		contains[mask] = (contains1 & contains2)
		return contains

	def compute_intersection_depth(self, points, triangles):
		t1 = triangles[:, 0, :]
		t2 = triangles[:, 1, :]
		t3 = triangles[:, 2, :]

		v1 = t3 - t1
		v2 = t2 - t1
		# v1 = v1 / np.linalg.norm(v1, axis=-1, keepdims=True)
		# v2 = v2 / np.linalg.norm(v2, axis=-1, keepdims=True)

		normals = np.cross(v1, v2)
		alpha = np.sum(normals[:, :2] * (t1[:, :2] - points[:, :2]), axis=1)

		n_2 = normals[:, 2]
		t1_2 = t1[:, 2]
		s_n_2 = np.sign(n_2)
		abs_n_2 = np.abs(n_2)

		mask = (abs_n_2 != 0)

		depth_intersect = np.full(points.shape[0], np.nan)
		depth_intersect[mask] = \
			t1_2[mask] * abs_n_2[mask] + alpha[mask] * s_n_2[mask]

		# Test the depth:
		# TODO: remove and put into tests
		# points_new = np.concatenate([points[:, :2], depth_intersect[:, None]], axis=1)
		# alpha = (normals * t1).sum(-1)
		# mask = (depth_intersect == depth_intersect)
		# assert(np.allclose((points_new[mask] * normals[mask]).sum(-1),
		#                    alpha[mask]))
		return depth_intersect, abs_n_2

	def rescale(self, array):
		array = self.scale * array + self.translate
		return array


class TriangleIntersector2d:
	def __init__(self, triangles, resolution=128):
		self.triangles = triangles
		self.tri_hash = _TriangleHash(triangles, resolution)

	def query(self, points):
		point_indices, tri_indices = self.tri_hash.query(points)
		point_indices = np.array(point_indices, dtype=np.int64)
		tri_indices = np.array(tri_indices, dtype=np.int64)
		points = points[point_indices]
		triangles = self.triangles[tri_indices]
		mask = self.check_triangles(points, triangles)
		point_indices = point_indices[mask]
		tri_indices = tri_indices[mask]
		return point_indices, tri_indices

	def check_triangles(self, points, triangles):
		contains = np.zeros(points.shape[0], dtype=np.bool)
		A = triangles[:, :2] - triangles[:, 2:]
		A = A.transpose([0, 2, 1])
		y = points - triangles[:, 2]

		detA = A[:, 0, 0] * A[:, 1, 1] - A[:, 0, 1] * A[:, 1, 0]

		mask = (np.abs(detA) != 0.)
		A = A[mask]
		y = y[mask]
		detA = detA[mask]

		s_detA = np.sign(detA)
		abs_detA = np.abs(detA)

		u = (A[:, 1, 1] * y[:, 0] - A[:, 0, 1] * y[:, 1]) * s_detA
		v = (-A[:, 1, 0] * y[:, 0] + A[:, 0, 0] * y[:, 1]) * s_detA

		sum_uv = u + v
		contains[mask] = (
			(0 < u) & (u < abs_detA) & (0 < v) & (v < abs_detA)
			& (0 < sum_uv) & (sum_uv < abs_detA)
		)
		return contains


class Voxels(object):
	""" Holds a binvox model.
	data is either a three-dimensional numpy boolean array (dense representation)
	or a two-dimensional numpy float array (coordinate representation).

	dims, translate and scale are the model metadata.

	dims are the voxel dimensions, e.g. [32, 32, 32] for a 32x32x32 model.

	scale and translate relate the voxels to the original model coordinates.

	To translate voxel coordinates i, j, k to original coordinates x, y, z:

	x_n = (i+.5)/dims[0]
	y_n = (j+.5)/dims[1]
	z_n = (k+.5)/dims[2]
	x = scale*x_n + translate[0]
	y = scale*y_n + translate[1]
	z = scale*z_n + translate[2]

	"""
	def __iter__(self):
		for attr, value in self.__dict__.iteritems():
			yield attr, value

	def __init__(self, data, dims, translate, scale, axis_order):
		self.data = data
		self.dims = dims
		self.translate = translate
		self.scale = scale
		assert (axis_order in ('xzy', 'xyz'))
		self.axis_order = axis_order

	def clone(self):
		data = self.data.copy()
		dims = self.dims[:]
		translate = self.translate[:]
		return Voxels(data, dims, translate, self.scale, self.axis_order)

	def write(self, fp):
		""" Write binary binvox format.

		Note that when saving a model in sparse (coordinate) format, it is first
		converted to dense format.

		Doesn't check if the model is 'sane'.

		"""

		if self.data.ndim==2:
			# TODO avoid conversion to dense
			dense_voxel_data = sparse_to_dense(self.data, self.dims)
		else:
			dense_voxel_data = self.data

		fp.write(b'#binvox 1\n')
		fp.write(str.encode('dim '+' '.join(map(str, self.dims))+'\n'))
		fp.write(str.encode('translate '+' '.join(map(str, self.translate))+'\n'))
		fp.write(str.encode('scale '+str(self.scale)+'\n'))
		fp.write(b'data\n')
		if not self.axis_order in ('xzy', 'xyz'):
			raise ValueError('Unsupported voxel model axis order')

		if self.axis_order=='xzy':
			voxels_flat = dense_voxel_data.flatten()
		elif self.axis_order=='xyz':
			voxels_flat = np.transpose(dense_voxel_data, (0, 2, 1)).flatten()

		# keep a sort of state machine for writing run length encoding
		state = voxels_flat[0]
		ctr = 0
		for c in voxels_flat:
			if c==state:
				ctr += 1
				# if ctr hits max, dump
				if ctr==255:
					fp.write(bytes([state]))
					fp.write(bytes([ctr]))
					ctr = 0
			else:
				# if switch state, dump
				fp.write(bytes([state]))
				fp.write(bytes([ctr]))
				state = c
				ctr = 1
		# flush out remainders
		if ctr > 0:
			fp.write(bytes([state]))
			fp.write(bytes([ctr]))
