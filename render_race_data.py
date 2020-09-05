import csv
import json
import os
import time

import bpy
from bpy_extras.image_utils import load_image

# argv = sys.argv
# argv = argv[argv.index("--") + 1:]  # get all args after "--"

current_time = int(round(time.time() * 1000))

# setup filepath directories to allow script to run in ide or blender
rel_path = ""
blender_script_dir = os.path.dirname(__file__)
if blender_script_dir.endswith('.blend'):
    rel_path = "/.."

blend_rel_path = blender_script_dir + rel_path
data_prep_path = blend_rel_path + "/data_prep/"
race_data_path = data_prep_path + "race_data_best_3laps"
texture_path = blend_rel_path + "/Textures"

with open(race_data_path + f"/race_data.json") as f:
    fileData = json.load(f)


def getRaceCoords(plot_file_path):
    csv_filepath = data_prep_path + plot_file_path
    with open(csv_filepath) as csvfile:
        reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        next(reader, None)
        return list(reader)


def getAddedCoordsForStartingPosition(team_position, first_coord):
    max_move_x = 10
    incremental = max_move_x / len(fileData)
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


def generatePath(coords, racer_number, total_frames):
    curve_name = "racer_" + str(racer_number) + "_curve"
    # make a new curve
    crv = bpy.data.curves.new('crv_' + str(racer_number), 'CURVE')
    crv.dimensions = '2D'

    starting_coords = getAddedCoordsForStartingPosition(racer_number, coords[0])
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

    return new_curve


def srgb_to_linearrgb(c):
    if c < 0:
        return 0
    elif c < 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(h, alpha=1):
    r = (h & 0xff0000) >> 16
    g = (h & 0x00ff00) >> 8
    b = (h & 0x0000ff)
    return tuple([srgb_to_linearrgb(c / 0xff) for c in (r, g, b)] + [alpha])


def modifyCarAttributes(iterString, car_number, car_color):
    # update number
    car_num_path = "/generated/car_number-assets/car_number_"
    numberImage = load_image(texture_path + car_num_path + str(car_number) + ".png")
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_number'].image = numberImage
    # update color
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_color'].outputs[0].default_value = hex_to_rgb(
        int(car_color, 16))


def assignCarToPath(curve, iterString):
    objects = bpy.data.objects
    car_base = objects['car_base' + iterString]

    bpy.ops.object.select_all(action='DESELECT')

    curve.select_set(True)
    car_base.select_set(True)

    bpy.context.view_layer.objects.active = curve
    bpy.ops.object.parent_set(type="FOLLOW")
    explode_color = objects['explode-sprite-color' + iterString]
    explode_color.hide_render = True
    explode_shadow = objects['explode-sprite-shadow' + iterString]
    explode_shadow.hide_render = True


def setExplodeVisibilityKeyframes(sprite, start_frame):
    sprite.keyframe_insert('hide_render')
    sprite.hide_render = False
    sprite.keyframe_insert('hide_render', frame=start_frame)
    sprite.hide_render = True
    sprite.keyframe_insert('hide_render', frame=start_frame + 160)


def addExplosion(iterString, total_frames):
    explosion_frame = total_frames - 5

    bpy.data.particles['destroyCar' + iterString].frame_start = explosion_frame
    bpy.data.particles['destroyCar' + iterString].frame_end = total_frames
    bpy.data.particles['destroyCar' + iterString].lifetime = 1000

    objects = bpy.data.objects
    explode_color = objects['explode-sprite-color' + iterString]
    setExplodeVisibilityKeyframes(explode_color, explosion_frame)
    explode_shadow = objects['explode-sprite-shadow' + iterString]
    explode_shadow.constraints['Locked Track'].target = objects['track-sun']
    setExplodeVisibilityKeyframes(explode_shadow, explosion_frame)

    bpy.data.materials['explosion' + iterString].node_tree.nodes[
        'sprite-texture'].image_user.frame_start = explosion_frame
    bpy.data.materials['explosion_shadow' + iterString].node_tree.nodes[
        'sprite-texture'].image_user.frame_start = explosion_frame


for i in range(len(fileData)):
    # add cars to scene
    car_collection_path = blend_rel_path + "/race_car.blend/Collection"
    bpy.ops.wm.append(
        directory=car_collection_path,
        link=False, filename="race_car")

for i in fileData:
    team_position = int(i['starting_position'])
    iterString = ''
    if team_position > 0:
        iterString = "." + str(team_position).zfill(3)
    team_name = i['team']
    car_number = i['car_no']
    car_color = i['car_color']
    car_time = i['lap_time']
    crashed = i['lap_end_state']
    plot_file_path = i['plot_file']
    total_frames = 24 * car_time
    print("Rendering race data for " + team_name)

    print("Get coordinates plot")
    coords = getRaceCoords(plot_file_path)

    print("Generating Path")
    curve = generatePath(coords, team_position, total_frames)

    print("Generating Car")
    modifyCarAttributes(iterString, car_number, car_color)

    print("Assign car to follow path")
    assignCarToPath(curve, iterString)

    if crashed == 'off_track':
        print("Add explosion to car " + team_name)
        addExplosion(iterString, total_frames)
