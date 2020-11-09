import pyrender
import numpy as np

from utils.MatrixCalculator import MatrixCalculator

class Renderer(object):
	def __init__(self, cfg):
		self.config = cfg

		self.scene = None
		self.camera = None
		self.light = None
		self.mesh = None
		self.renderer = None

		self.configuration = {
			"angle": [0, 0],        #[Posi]ioner Primary Angle, Positioner Secondary Angle)
			"position": [0, 0, 0]   #(TableX, TableY, TableZ)
		}

		self._init_pyrender()

	def _init_pyrender(self):
		self.scene = pyrender.Scene()
		self.light = self.scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=1.0), self.pose)
		self.renderer = pyrender.OffscreenRenderer(*self.image_size)
		self.camera = self.scene.add(
			pyrender.IntrinsicsCamera(
				fx=self.SID/self.pixel_size[0],
				fy=self.SID/self.pixel_size[1],
				cx=0.5*self.image_size[0],
				cy=0.5*self.image_size[1],
				zfar=100000000000000 # `Infinite` clipping
			), 
			self.pose
		)

	@property
	def SID(self):
		return self.config.get_config("equipment/fluoroscope/specifications/source_to_image_distance")

	@property
	def pixel_size(self):
		return (
			self.config.get_config("equipment/fluoroscope/specifications/pixel_size/x"),
			self.config.get_config("equipment/fluoroscope/specifications/pixel_size/y")
		)

	@property
	def image_size(self):
		return (
			self.config.get_config("equipment/fluoroscope/specifications/image_dimensions/width"),
			self.config.get_config("equipment/fluoroscope/specifications/image_dimensions/height")
		)

	@property
	def pose(self):
		return MatrixCalculator.DICOMtoPose(
			self.configuration["angle"][0],
			self.configuration["angle"][1],
			self.SID,
			self.configuration["position"]
		)

	@property
	def cameraMatrix(self):
		return MatrixCalculator.camParamsToIntrinsic(
			fx=self.SID/self.pixel_size[0],
			fy=self.SID/self.pixel_size[1],
			image_dims=self.image_size
		)

	def get_image(self):
		image_rgb, depth = self.renderer.render(self.scene)

		# Convert to single channel (greyscale)
		image = np.array(image_rgb[:, :, 0])*.299 + np.array(image_rgb[:, :, 1])*.587 + np.array(image_rgb[:, :, 2])*.114
		return image.astype(np.uint8), depth

	def generate_data(self, mesh):
		mesh_obj = self.scene.add(mesh)

		protocol = self.config.get_config("operation/protocol")
		images = []
		depths = []
		matrices = {"K": [], "P": [], "R": [], "t": []}

		for item in protocol:
			if "capture" in item:
				self.scene.set_pose(self.light, self.pose)
				self.scene.set_pose(self.camera, self.pose)	

				im, dp = self.get_image()

				images += [im]
				depths += [dp]

				mats = MatrixCalculator.poseToExtrinsics(self.pose)
				matrices["K"] += [self.cameraMatrix]
				matrices["P"] += [self.pose]
				matrices["R"] += [mats["R"]]
				matrices["t"] += [mats["t"]]

			if "centre" in item:
				cx, cy, cz = mesh.centroid
				self.configuration["position"] = [-cx, -cy, -cz]
			
			if "fluoroscope" in item:
				self.configuration["angle"][0] = item["fluoroscope"].get("ppa", self.configuration["angle"][0])
				self.configuration["angle"][1] = item["fluoroscope"].get("psa", self.configuration["angle"][1])

			if "table" in item:
				self.configuration["position"][0] = item["table"].get("x", self.configuration["position"][0])
				self.configuration["position"][1] = item["table"].get("y", self.configuration["position"][1])
				self.configuration["position"][2] = item["table"].get("z", self.configuration["position"][2])

		self.scene.remove_node(mesh_obj)

		for matrix in matrices:
			matrices[matrix] = np.dstack(matrices[matrix])

		return np.dstack(images), np.dstack(depths), matrices