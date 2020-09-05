import bpy


cube = bpy.data.objects["Cube"]
mw = cube.matrix_world
verts = bpy.context.object.data.vertices

glob_vertex_coordinates = [ mw @ v.co for v in verts ] # Global coordinates of vertices

# Find the min and max x and y values amongst the object's verts
min_x = min( [ co.x for co in glob_vertex_coordinates ] )
max_x = max( [ co.x for co in glob_vertex_coordinates ] )
min_y = min( [ co.y for co in glob_vertex_coordinates ] )
max_y = max( [ co.y for co in glob_vertex_coordinates ] )

sphere_mw = bpy.data.objects["Sphere"].matrix_world.to_translation()

x_loc = sphere_mw[0]
y_loc = sphere_mw[1]
in_x = x_loc > min_x and x_loc < max_x
in_y = y_loc > min_y and y_loc < max_y

print(in_x and in_y) # print: is sphere inside cube?