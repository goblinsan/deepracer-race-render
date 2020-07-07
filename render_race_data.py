import os
import json
import csv
import bpy
from bpy_extras.image_utils import load_image

# setup filepath directories to allow script to run in ide or blender
blender_script_dir = os.path.dirname(__file__)
if blender_script_dir.endswith('.blend'):
    rel_race_data_path = "/../data_prep/race_data"
else:
    rel_race_data_path = "/data_prep/race_data"
race_data_path = blender_script_dir + rel_race_data_path

with open(race_data_path + "/sample_race.json") as f:
    fileData = json.load(f)

def getRaceCoords(race, car):
    car_csv_name = "car_" + str(car) + ".csv"
    csv_filepath = race_data_path + "/coord_plots/" + race + "/" + car_csv_name
    with open(csv_filepath) as csvfile:
        return list(csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC))

def getAddedCoordsForStartingPosition(team_position, first_coord):
    max_move_x = 10
    incremental = max_move_x / len(fileData)
    x_translate = (incremental * team_position) + .3
    y_translate = 0
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

def generatePath(coords, racer_number, car_time):
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
    crv.path_duration = 24 * float(car_time)

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


def generateCar(iterString, car_number, car_color):
    # add car to scene
    bpy.ops.wm.append(directory="D:\\deepRacer\\deepRacer-race-render\\deepracer-race-render\\race_car.blend\\Collection\\", link=False, filename="race_car")
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




#bpy.ops.transform.translate(value=(-0, -0.394784, -0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, release_confirm=True)
#bpy.ops.transform.translate(value=(-1.81986, -0, -0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, release_confirm=True)


for i in fileData:
    team_position = int(i['starting_position'])
    iterString = ''
    if team_position > 0:
        iterString = "." + str(team_position).zfill(3)
    team_name = i['team']
    car_number = i['car_no']
    car_color = i['car_color']
    car_time = i['lap_time']
    print("Rendering race data for " + team_name)

    print("Get coordinates plot for " + team_name)
    coords = getRaceCoords("sample_race", team_position)

    print("Generating Path for " + team_name)
    curve = generatePath(coords, team_position, car_time)

    print("Generating Car for " + team_name)
    generateCar(iterString, car_number, car_color)

    print("Assign car to follow path")
    assignCarToPath(curve, iterString)

    # if team_position > 0:
    #     print("Move car to starting position")
    #     moveCarToStartingPosition(team_position, curve)

