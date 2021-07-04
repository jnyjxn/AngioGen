import sys
import math
import numpy as np

try:
	import bpy
	import bmesh
except ImportError:
	pass
	
class MeshBuilder(object):
	def __init__(self, root_directory, id, mesh_resolution=0.8):
		self.path = root_directory
		self.id = id
		self.mesh_resolution = mesh_resolution

		if 'bpy' not in sys.modules:
			raise ImportError("This class cannot be used using Python. It must be run inside Blender as a script. Exiting.")

	def read_segments_from_file (self, swc_file_name):
		# Read in the data
		segments = []

		num_nodes_in_file = 0
		num_total_segments = 0

		# Read SWC Format
		# SWC format has explicit connections, but they're not needed with metaballs
		# Note that the SWC format could define cyclic references,
		#   However, since we just need to generate segments, this is not a problem.
		#   This is done by making each segment only one line (from parent to child)

		# Start by reading all the points into a dictionary keyed by their label n

		f = open ( swc_file_name, 'r' )
		lines = f.readlines();
		point_dict = {}
		for l in lines:
			l = l.strip()
			if len(l) > 0:
				if l[0] != "#":
					fields = l.split()
					point_dict[fields[0]] = fields

		point_keys = sorted ( [ k for k in point_dict.keys() ] )
		num_lines_in_file = len(point_keys)
		num_nodes_in_file = len(point_keys)

		min_radius = 1e6

		# Next create the list of segments - one for each child that has a parent
		for k in point_keys:
			child_fields = point_dict[k]
			if child_fields[6] in point_keys:
				# This point has a parent, so make a segment from parent to child
				parent_fields = point_dict[child_fields[6]]
				px = float(parent_fields[2])
				py = float(parent_fields[3])
				pz = float(parent_fields[4])
				pr = float(parent_fields[5])
				cx = float(child_fields[2])
				cy = float(child_fields[3])
				cz = float(child_fields[4])
				cr = float(child_fields[5])
				segments = segments + [ [ [px, py, pz, pr], [cx, cy, cz, cr] ] ]
				num_total_segments += 1
				if cr < min_radius:
					min_radius = cr

		num_segs_limit = 0
		if num_segs_limit > 0:
			# Limit the number of segments
			segments = segments[0:self.num_segs_limit]
			num_total_segments = len(segments)

		data = {
			"segments": segments,
			"min_radius": min_radius,
			"num_segments": num_total_segments
		}

		return data

	def build_vessel_from_segments(self, data):
		mesh_resolution = data["min_radius"]*self.mesh_resolution
		scale_file_data = 1.
		min_forced_radius = 0.
		meta_ball_scale_factor = 1.

		# Create the object to hold the metaballs
		scene = bpy.context.scene
		mball = bpy.data.metaballs.new(f'vessel{self.id}')
		mball.resolution = self.mesh_resolution
		
		mball.render_resolution = self.mesh_resolution
		obj = bpy.data.objects.new(f'Vessel{self.id}',mball)
		# scene.collection.objects.link(obj)

		# Generate the metashape segments from the branch segments
		seg_num = 1
		obj_name = None
		for seg in data["segments"]:
			seg_num += 1
			lc = None
			for c in seg:
				if (lc != None):  # and (seg_num < 20):

					x1 = float(lc[0]) * scale_file_data
					y1 = float(lc[1]) * scale_file_data
					z1 = float(lc[2]) * scale_file_data
					r1 = float(lc[3]) * scale_file_data
					x2 = float(c[0]) * scale_file_data
					y2 = float(c[1]) * scale_file_data
					z2 = float(c[2]) * scale_file_data
					r2 = float(c[3]) * scale_file_data

					# Make the segment from a series of meta balls
					segment_length = math.sqrt( math.pow(x2-x1, 2) + math.pow(y2-y1, 2) + math.pow(z2-z1, 2) )

					dr = r2 - r1
					dx = x2 - x1
					dy = y2 - y1
					dz = z2 - z1
					r = r1
					x = x1
					y = y1
					z = z1

					length_so_far = 0
					while length_so_far < segment_length:
						# Make a sphere at this point
						ele = mball.elements.new()
						ele.radius = r * meta_ball_scale_factor
						ele.co = (x, y, z)
						ele.type = "ELLIPSOID"
						ele.stiffness = 10
						# ele.size_x = ele.radius

						# Move x, y, z, and r to the next point
						length_so_far += r/2
						r = r1 + (length_so_far * dr / segment_length)
						x = x1 + (length_so_far * dx / segment_length)
						y = y1 + (length_so_far * dy / segment_length)
						z = z1 + (length_so_far * dz / segment_length)

				lc = c

		return obj

	def get_one_mesh_obj(self):
		swc_filepath = self.path / f"{self.id}" / "network.swc"
		swc_data = self.read_segments_from_file(swc_filepath)

		return self.build_vessel_from_segments(swc_data)

	def save_one_mesh(self, obj):
		objs = [ob for ob in bpy.context.scene.objects if ob.type in ('MESH','CAMERA','LIGHT')]
		bpy.ops.object.delete({"selected_objects": objs})

		output_ply_path, output_stl_path, output_npz_path = (
			self.path / f"{self.id}" / "mesh.ply", 
			self.path / f"{self.id}" / "mesh.stl",
			self.path / f"{self.id}" / "mesh.npz"
		)

		scene = bpy.context.scene
		scene.collection.objects.link(obj)

		bpy.context.scene.objects[f'Vessel{self.id}'].select_set(True)
		bpy.context.view_layer.objects.active = obj

		bpy.ops.object.convert()
		
		me = bpy.context.object.data
		bm = bmesh.new()
		bm.from_mesh(me)
		bmesh.ops.triangulate(bm, faces=bm.faces[:])
		bm.to_mesh(me)

		verts = np.array([v.co for v in bm.verts])
		faces = np.array([[me.loops[loop_index].vertex_index for loop_index in poly.loop_indices] for poly in me.polygons])

		np.savez_compressed(
			output_npz_path,
			verts=verts,
			faces=faces,
		)
		
		bpy.ops.export_mesh.ply(filepath=str(output_ply_path),check_existing=False)
		bpy.ops.export_mesh.stl(filepath=str(output_stl_path),check_existing=False,ascii=True)
