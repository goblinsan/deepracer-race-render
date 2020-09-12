import json
import os
import sys
import datetime
import threading
import time

import bpy


progress = 0
result_available = threading.Event()

def getIterString(team_position):
    iterString = ''
    if team_position > 0:
        iterString = "." + str(team_position).zfill(3)

    return iterString


def get_team_data(race_team_entry):
    team_data = {}
    team_data['team_position'] = int(race_team_entry['starting_position'])
    team_data['iterString'] = getIterString(team_data['team_position'])
    team_data['team_name'] = race_team_entry['team']
    team_data['car_number'] = race_team_entry['car_no']
    team_data['car_color'] = race_team_entry['car_color']
    team_data['car_time'] = race_team_entry['lap_time']
    team_data['crashed'] = race_team_entry['lap_end_state']
    team_data['plot_file_path'] = race_team_entry['plot_file']
    team_data['total_frames'] = 24 * team_data['car_time']
    return team_data

def setup_camera_animations(race_json, data_prep_path):
    best_csv, best_time = camera_activation.get_best_car(race_json)
    print(f'\nwinning car - csv: {best_csv} best time: {best_time}')
    best_coords = camera_activation.get_race_coords(data_prep_path + best_csv)
    zone_list = []

    for i in range(1, 7):
        zone_cube = bpy.data.objects[f'activation_bounds_{i}']
        min_x, max_x, min_y, max_y = get_max_min.get_zone_max_min(zone_cube)
        zone_list.append(camera_activation.create_zone(i, min_x, max_x, min_y, max_y))

    coord_markers = camera_activation.get_coord_markers(best_coords, best_time, zone_list + zone_list + zone_list)
    camera_01 = {'name': '01_race_start_cam', 'rule': [("exit", 1), ("exit", 2)]}
    camera_02 = {'name': '02_turn_1_close_cam', 'rule': [("enter", 2), ("exit", 4)]}
    camera_03 = {'name': '03_start_sbend', 'rule': [("enter", 3), ("enter", 5)]}
    camera_04 = {'name': '04_thru_sbend', 'rule': [("exit", 4), ("exit", 5)]}
    camera_05 = {'name': '05_back_corner', 'rule': [("enter", 5), ("enter", 6)]}
    camera_06 = {'name': '06_last_turn', 'rule': [("exit", 5), ("exit", 6)]}
    camera_action_frames = camera_activation.get_camera_action_frames_dic(coord_markers,
                                                           [camera_01, camera_02, camera_03, camera_04, camera_05,
                                                            camera_06])
    last_mapped_frame = camera_action_frames['06_last_turn'][-1]
    camera_action_frames['07_race_clean_up'] = [[last_mapped_frame[-1], last_mapped_frame[-1] + 300]]

    return camera_action_frames


def create_render_list_txt(camera_action_frames):
    with open("render_list.json", "w") as text_file:
        print("{", file=text_file)
        print(f'  "00_starting_line_cam": [[0, 40]],', file=text_file)
        for a in camera_action_frames:
            if a == '07_race_clean_up':
                print(f'  "{a}": {camera_action_frames[a]}', file=text_file)
            else:
                print(f'  "{a}": {camera_action_frames[a]},', file=text_file)
        print("}", file=text_file)


def add_cars_to_scene(blend_rel_path, fileData):
    for i in range(len(fileData)):
        # add cars to scene
        car_collection_path = blend_rel_path + "/race_car.blend/Collection"
        bpy.ops.wm.append(
            directory=car_collection_path,
            link=False, filename="race_car")


def get_relative_blender_path():
    rel_path = ""
    blender_script_dir = os.path.dirname(__file__)
    if blender_script_dir.endswith('.blend'):
        rel_path = "/.."
    blend_rel_path = blender_script_dir + rel_path
    return blend_rel_path


def apply_race_data_to_car(data_prep_path, file_data, max_frame, texture_path):
    for racer in file_data:
        car_data = get_team_data(racer)
        print("\nRendering race data for " + car_data['team_name'])
        coords = car_path.getRaceCoords(data_prep_path + car_data['plot_file_path'])
        curve, max_frame = car_path.generatePath(coords, car_data['team_position'], car_data['total_frames'],
                                                 len(file_data), max_frame)
        car_customize.modifyCarAttributes(texture_path, car_data['iterString'], car_data['car_number'],
                                          car_data['car_color'])
        car_path.assignCarToPath(curve, car_data['iterString'])

        if car_data['crashed'] == 'off_track':
            print("  !!! Add explosion to car " + car_data['team_name'])
            car_explosions.addExplosion(car_data['iterString'], car_data['total_frames'])
    return max_frame


def camera_animation_builder(data_prep_path, race_json):
    # setup camera animations
    camera_action_frames = setup_camera_animations(race_json, data_prep_path)
    create_render_list_txt(camera_action_frames)
    for key in camera_action_frames:
        cam = bpy.data.objects[key]
        position_camera.setup_camera_frames(cam, camera_action_frames[key])


def scene_setup():
    argv = sys.argv
    try:
        extra_args = argv[argv.index("--") + 1:]  # get all args after "--"
        today = extra_args[0]
    except ValueError:
        today = datetime.date.today()

    max_frame = 500

    # setup filepath directories to allow script to run in ide or blender
    blend_rel_path = get_relative_blender_path()
    data_prep_path = blend_rel_path + "/data_prep/"
    race_data_path = data_prep_path + "race_data_best_3laps"
    race_json = race_data_path + "/race_data.json"
    texture_path = blend_rel_path + "/Textures"

    with open(race_json) as f:
        file_data = json.load(f)

    add_cars_to_scene(blend_rel_path, file_data)
    max_frame = apply_race_data_to_car(data_prep_path, file_data, max_frame, texture_path)

    # set animation duration
    bpy.context.scene.frame_end = max_frame

    # setup cameras
    camera_animation_builder(data_prep_path, race_json)

    # save generated race blend file
    race_blend_path = f"{bpy.path.abspath('//')}race_{today}.blend"
    print(f"\nSaving race blend file as: {race_blend_path}")
    bpy.ops.wm.save_as_mainfile(filepath=race_blend_path)

    # save generated starting grid blend file
    start_grid_blend_path = f"{bpy.path.abspath('//')}starting_grid_{today}.blend"
    print(f"\nCreate Starting Grid and saving file as: {start_grid_blend_path}")

    for racer in file_data:
        iterString = getIterString(int(racer['starting_position']))
        car_base = bpy.data.objects[f'car_base{iterString}']
        bpy.ops.object.select_all(action='DESELECT')
        car_base.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

    bpy.ops.wm.save_as_mainfile(filepath=start_grid_blend_path)


if __name__ == '__main__':
    blend_dir = os.path.dirname(bpy.data.filepath)
    if blend_dir not in sys.path:
        sys.path.append(blend_dir)

    import car_path
    import car_customize
    import car_explosions
    import camera_activation
    import get_max_min
    import position_camera
    scene_setup()

