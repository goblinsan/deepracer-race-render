import os
import json
import csv
import bpy
from bpy_extras.image_utils import load_image

race_num = 2

# setup filepath directories to allow script to run in ide or blender
blender_script_dir = os.path.dirname(__file__)
if blender_script_dir.endswith('.blend'):
    rel_race_data_path = "/../data_prep/race_data"
else:
    rel_race_data_path = "/data_prep/race_data"
race_data_path = blender_script_dir + rel_race_data_path

with open(race_data_path + f"/race_{race_num}_data.json") as f:
    fileData = json.load(f)

def getRaceCoords(race, plot_file_path):
    csv_filepath = blender_script_dir + "/../data_prep/" + plot_file_path
    with open(csv_filepath) as csvfile:
        reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        next(reader, None)
        return list(reader)

def getAddedCoordsForStartingPosition(team_position, first_coord):
    max_move_x = 10
    incremental = max_move_x / len(fileData)
    x_translate = (incremental * team_position) + .4
    if team_position % 2 != 0:
        y_translate = .3
    else:
        y_translate = -.1

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
    if   c < 0:       return 0
    elif c < 0.04045: return c/12.92
    else:             return ((c+0.055)/1.055)**2.4

def hex_to_rgb(h,alpha=1):
    r = (h & 0xff0000) >> 16
    g = (h & 0x00ff00) >> 8
    b = (h & 0x0000ff)
    return tuple([srgb_to_linearrgb(c/0xff) for c in (r,g,b)] + [alpha])


def modifyCarAttributes(iterString, car_number, car_color):
    # update number
    numberImage = load_image("D:\\deepRacer\\deepRacer-race-render\\deepracer-race-render\\Textures\\generated\\car_number-assets\\car_number_" + str(car_number) +".png")
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_number'].image = numberImage
    # update color
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_color'].outputs[0].default_value = hex_to_rgb(int(car_color, 16))


def assignCarToPath(curve, iterString):
    objects = bpy.data.objects
    car_base = objects['car_base' + iterString]

    bpy.ops.object.select_all(action='DESELECT')

    curve.select_set(True)
    car_base.select_set(True)

    bpy.context.view_layer.objects.active = curve
    bpy.ops.object.parent_set(type="FOLLOW")


def addExplosion(iterString, total_frames):
    explosion_frame = total_frames - 5
    smoke_domain = bpy.data.objects['smoke_domain' + iterString]
    smoke_domain.modifiers["Fluid"].domain_settings.cache_frame_start = explosion_frame
    smoke_domain.modifiers["Fluid"].domain_settings.cache_frame_end = explosion_frame + 200
    iter_no_dot = iterString[1:]
    smoke_domain.modifiers["Fluid"].domain_settings.cache_directory = f'//race_{race_num}_car_{iter_no_dot}_explode_cache'
    bpy.data.particles['flame' + iterString].frame_start = explosion_frame
    bpy.data.particles['flame' + iterString].frame_end = explosion_frame + 1
    bpy.data.particles['destroyCar' + iterString].frame_start = explosion_frame
    bpy.data.particles['destroyCar' + iterString].frame_end = total_frames
    bpy.data.particles['destroyCar' + iterString].lifetime = 1000

    smoke_domain.select_set(True)
    bpy.context.view_layer.objects.active = smoke_domain
    bpy.ops.fluid.bake_data()

for i in range(len(fileData)):
    # add cars to scene
    bpy.ops.wm.append(directory="D:\\deepRacer\\deepRacer-race-render\\deepracer-race-render\\race_car.blend\\Collection\\", link=False, filename="race_car")

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
    coords = getRaceCoords(f"race_{race_num}", plot_file_path)

    print("Generating Path")
    curve = generatePath(coords, team_position, total_frames)

    print("Generating Car")
    modifyCarAttributes(iterString, car_number, car_color)

    print("Assign car to follow path")
    assignCarToPath(curve, iterString)

    if crashed == 'off_track':
        print("Add explosion to car " + team_name)
        addExplosion(iterString, total_frames)

