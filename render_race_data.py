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
        return list(csv.reader(csvfile))


def generatePath(coords, racer_number):
    curve_name = "racer_" + str(racer_number) + "_curve"
    # make a new curve
    crv = bpy.data.curves.new('crv', 'CURVE')
    crv.dimensions = '2D'

    # make a new spline in that curve
    spline = crv.splines.new(type='NURBS')
    # a spline point for each point - already contains 1 point
    spline.points.add(len(coords) - 1)

    # assign the point coordinates to the spline points
    for p, new_co in zip(spline.points, coords):
        p.co = (new_co + [0] + [1.0])

    # make a new object with the curve
    obj = bpy.data.objects.new(curve_name, crv)
    bpy.context.scene.collection.objects.link(obj)

    return obj

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
    bpy.ops.wm.append(directory="D:\\deepRacer\\deepRacer-race-render\\deepracer-race-render\\race_car.blend\\Collection\\", link=False, filename="race_car")
    numberImage = load_image("D:\\deepRacer\\deepRacer-race-render\\deepracer-race-render\\Textures\\generated\\car_number-assets\\car_number_" + str(car_number) +".png")
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_number'].image = numberImage

    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_color'].outputs[0].default_value = hex_to_rgb(car_color)


for i in fileData:
    iterString = ''
    if i > 0:
        iterString = "." + str(i).zfill(3)
    team_name = i['team']
    team_position = i['starting_position']
    car_number = i['car_no']
    car_color = i['car_color']
    print("Rendering race data for " + team_name)

    print("Get coordinates plot for " + team_name)
    coords = getRaceCoords("sample_race", team_position)

    print("Generating Path for " + team_name)
    curve = generatePath(coords, team_position)

    print("Generating Car for " + team_name)
    generateCar(iterString, car_number, car_color)
    print("Set race car color for " + team_name)
    print("Set race car number for " + team_name)
