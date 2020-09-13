import csv

import bpy


def getRaceCoords(csv_filepath):
    with open(csv_filepath) as csvfile:
        reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        next(reader, None)
        return list(reader)


def getAddedCoordsForStartingPosition(team_position, first_coord, num_of_cars):
    max_move_x = 10
    incremental = max_move_x / num_of_cars
    x_translate = (incremental * team_position) + .4
    if team_position % 2 != 0:
        y_translate = .2
    else:
        y_translate = -.15

    current_x = first_coord[0]
    current_y = first_coord[1]
    first_x = current_x - x_translate
    second_x = current_x - 0.3
    third_x = current_x - 0.1
    first_y = current_y - y_translate

    coord_list = []
    coord_list.append([first_x, first_y])
    coord_list.append([second_x, first_y])
    coord_list.append([third_x, first_y])
    return coord_list


def generatePath(coords, racer_number, total_frames, num_of_cars, max_frame):
    curve_name = "racer_" + str(racer_number) + "_curve"
    # make a new curve
    crv = bpy.data.curves.new('crv_' + str(racer_number), 'CURVE')
    crv.dimensions = '2D'

    starting_coords = getAddedCoordsForStartingPosition(racer_number, coords[0], num_of_cars)
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


def assignCarToPath(curve, iterString):
    objects = bpy.data.objects
    car_base = objects['car_base' + iterString]

    bpy.ops.object.select_all(action='DESELECT')

    curve.select_set(True)
    car_base.select_set(True)

    bpy.context.view_layer.objects.active = curve
    bpy.ops.object.parent_set(type="FOLLOW")
    explode_color = objects['explode_sprite_color' + iterString]
    explode_color.hide_render = True
    explode_shadow = objects['explode_sprite_shadow' + iterString]
    explode_shadow.hide_render = True

