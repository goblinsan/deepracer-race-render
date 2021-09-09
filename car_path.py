import csv

import bpy


def get_race_coords(csv_filepath):
    with open(csv_filepath) as csvfile:
        reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        next(reader, None)
        return list(reader)


def get_added_coords_for_starting_position(iter_string):
    starting_curve = bpy.data.objects["start_grid_curve" + iter_string]
    starting_curve_bez_points = bpy.data.curves["start_grid_curve" + iter_string].splines[0].bezier_points

    xyz1 = starting_curve.matrix_world @ starting_curve_bez_points[0].co
    xyz2 = starting_curve.matrix_world @ starting_curve_bez_points[1].co
    xyz3 = starting_curve.matrix_world @ starting_curve_bez_points[2].co

    return [[xyz1[0], xyz1[1]],
            [xyz2[0], xyz2[1]],
            [xyz3[0], xyz3[1]]]


def generate_path(coords, racer_number, iter_string, total_frames, max_frame):
    curve_name = "racer_" + str(racer_number) + "_curve"
    # make a new curve
    crv = bpy.data.curves.new('crv_' + str(racer_number), 'CURVE')
    crv.dimensions = '2D'

    starting_coords = get_added_coords_for_starting_position(iter_string)
    updated_coords = starting_coords + coords

    # make a new spline in that curve
    spline = crv.splines.new(type='NURBS')
    # a spline point for each point - already contains 1 point
    spline.points.add(len(updated_coords) - 1)

    # assign the point coordinates to the spline points
    for p, new_co in zip(spline.points, updated_coords):
        p.co = (new_co + [0] + [1.0])

    # make a new object with the curve
    new_curve = bpy.data.objects.new(curve_name, crv)
    bpy.context.scene.collection.objects.link(new_curve)

    # update path duration
    crv.path_duration = total_frames

    # check if slowest car
    if total_frames + 50 > max_frame:
        max_frame = total_frames + 50

    return new_curve, max_frame


def assign_car_to_path(curve, iter_string):
    objects = bpy.data.objects
    car_base = objects['car_base' + iter_string]

    bpy.ops.object.select_all(action='DESELECT')

    curve.select_set(True)
    car_base.select_set(True)

    bpy.context.view_layer.objects.active = curve
    bpy.ops.object.parent_set(type="FOLLOW")
    explode_color = objects['explode_sprite_color' + iter_string]
    explode_color.hide_render = True
    explode_shadow = objects['explode_sprite_shadow' + iter_string]
    explode_shadow.hide_render = True
