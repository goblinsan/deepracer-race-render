import bpy


def get_zone_max_min(zone_cube):
    # zone_cube = bpy.data.objects["activation_bounds_6"]
    mw = zone_cube.matrix_world
    verts = zone_cube.data.vertices

    glob_vertex_coordinates = [mw @ v.co for v in verts]  # Global coordinates of vertices

    # Find the min and max x and y values amongst the object's verts
    min_x = min([co.x for co in glob_vertex_coordinates])
    max_x = max([co.x for co in glob_vertex_coordinates])
    min_y = min([co.y for co in glob_vertex_coordinates])
    max_y = max([co.y for co in glob_vertex_coordinates])

    return min_x, max_x, min_y, max_y
