import json
import os
import sys
import datetime

import bpy

blend_dir = os.path.dirname(bpy.data.filepath)
if blend_dir not in sys.path:
    sys.path.append(blend_dir)

import car_path
import car_customize
import car_explosions

argv = sys.argv
try:
    local_args = argv[argv.index("--") + 1:]  # get all args after "--"
    today = local_args[0]
except ValueError:
    local_args = []
    today = datetime.date.today()

max_frame = 500

# setup filepath directories to allow script to run in ide or blender
rel_path = ""
blender_script_dir = os.path.dirname(__file__)
if blender_script_dir.endswith('.blend'):
    rel_path = "/.."

blend_rel_path = blender_script_dir + rel_path
data_prep_path = blend_rel_path + "/data_prep/"
race_data_path = data_prep_path + "race_data_best_3laps"
texture_path = blend_rel_path + "/Textures"

with open(f"{race_data_path}/race_data.json") as f:
    fileData = json.load(f)

for i in range(len(fileData)):
    # add cars to scene
    car_collection_path = blend_rel_path + "/race_car.blend/Collection"
    bpy.ops.wm.append(
        directory=car_collection_path,
        link=False, filename="race_car")


def getIterString(team_position):
    iterString = ''
    if team_position > 0:
        iterString = "." + str(team_position).zfill(3)

    return iterString


for i in fileData:
    team_position = int(i['starting_position'])
    iterString = getIterString(team_position)
    team_name = i['team']
    car_number = i['car_no']
    car_color = i['car_color']
    car_time = i['lap_time']
    crashed = i['lap_end_state']
    plot_file_path = i['plot_file']
    total_frames = 24 * car_time
    print("\nRendering race data for " + team_name)
    # print("  Get coordinates plot")
    coords = car_path.getRaceCoords(data_prep_path + plot_file_path)
    # print("  Generating Path")
    curve, max_frame = car_path.generatePath(coords, team_position, total_frames, len(fileData), max_frame)
    # print("  Generating Car")
    car_customize.modifyCarAttributes(texture_path, iterString, car_number, car_color)
    # print("  Assign car to follow path")
    car_path.assignCarToPath(curve, iterString)

    if crashed == 'off_track':
        print("  !!! Add explosion to car " + team_name)
        car_explosions.addExplosion(iterString, total_frames)

# set animation duration
bpy.context.scene.frame_end = max_frame

# save generated race blend file
race_blend_path = f"{bpy.path.abspath('//')}race_{today}.blend"
print(f"\nSaving race blend file as: {race_blend_path}")
bpy.ops.wm.save_as_mainfile(filepath=race_blend_path)

# save generated starting grid blend file
start_grid_blend_path = f"{bpy.path.abspath('//')}starting_grid_{today}.blend"
print(f"\nCreate Starting Grid and saving file as: {start_grid_blend_path}")

for i in fileData:
    iterString = getIterString(int(i['starting_position']))
    car_base = bpy.data.objects[f'car_base{iterString}']
    bpy.ops.object.select_all(action='DESELECT')
    car_base.select_set(True)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

bpy.ops.wm.save_as_mainfile(filepath=start_grid_blend_path)


