import json
import os
import sys
import datetime
from os.path import dirname, abspath, join
from types import SimpleNamespace

import bpy

blend_dir = dirname(bpy.data.filepath)
code_dir = dirname(dirname(blend_dir))
script_dir = abspath(join(code_dir, "render_scripts"))

if script_dir not in sys.path:
    sys.path.append(script_dir)

import deep_racer_utils
import start_grid


def get_team_data(race_team_entry, race_speed):
    team_data = {'team_position': int(race_team_entry['starting_position'])}
    team_data['iterString'] = deep_racer_utils.getIterString(team_data['team_position'])
    team_data['team_name'] = race_team_entry['team']
    # team_data['team_city'] = race_team_entry['city']
    team_data['car_number'] = race_team_entry['car_no']
    team_data['car_color'] = race_team_entry['car_color']
    team_data['number_laps_complete'] = race_team_entry['number_laps_complete']
    team_data['plot_file_paths'] = race_team_entry['plot_data']
    team_data['lap_times'] = race_team_entry['lap_times']
    team_data['overall_time'] = race_team_entry['overall_time']
    team_data['total_frames'] = deep_racer_utils.get_frames_for_time(team_data['overall_time'], race_speed)
    return team_data


def create_zone_list():
    z_list = []
    for i in range(1, 4):
        zone_cube = bpy.data.objects[f'activation_bounds_{i}']
        min_x, max_x, min_y, max_y = get_max_min.get_zone_max_min(zone_cube)
        z_list.append(camera_activation.create_zone(i, min_x, max_x, min_y, max_y))

    return z_list


def setup_camera_animations(race_json_path, lap_json_path, race_speed):
    race_json = deep_racer_utils.get_json(race_json_path)
    lap_json = deep_racer_utils.get_json(lap_json_path)

    zone_list = create_zone_list()

    coord_markers = []
    for idx, lap in enumerate(lap_json['laps']):
        fastest_car = lap['racers'][0]['name']
        print(f'Fastest car in lap {lap["lap"]} is {fastest_car}')
        fastest_team_json = [x for x in race_json if x["team"] == fastest_car][0]
        fastest_plot = fastest_team_json['plot_data'][idx]
        best_coords = camera_activation.get_race_coords(fastest_plot)
        best_time = lap['racers'][0]['lap_time']
        overall_time = lap['racers'][0]['overall_time']
        coord_markers.append(
            camera_activation.get_coord_markers(idx, best_coords, best_time, overall_time, zone_list, len(lap_json),
                                                race_speed))

    camera_01 = {'name': 'high-starting-line', 'rule': [("exit", 1), ("enter", 2)]}
    camera_02 = {'name': 'front_chicane', 'rule': [("enter", 2), ("exit", 2)]}
    camera_03 = {'name': 'back-corner', 'rule': [("exit", 2), ("enter", 3)]}
    camera_04 = {'name': 'back_chicane', 'rule': [("enter", 3), ("exit", 3)]}
    camera_05 = {'name': 'last-turn', 'rule': [("exit", 3), ("enter", 1)]}
    camera_06 = {'name': 'finish-line-tight', 'rule': [("enter", 1), ("exit", 1)]}
    camera_action_frames = camera_activation.get_camera_action_frames_dic(coord_markers,
                                                                          [camera_01, camera_02, camera_03, camera_04,
                                                                           camera_05,
                                                                           camera_06])
    last_mapped_frame = camera_action_frames['finish-line-tight'][-1]
    camera_action_frames['race_clean_up'] = [[last_mapped_frame[-1], last_mapped_frame[-1] + 300]]

    return camera_action_frames


def create_render_list_txt(camera_action_frames, race_blend_path, today):
    with open(os.path.join(race_blend_path, f"render_list_{today}.json"), "w") as text_file:
        print("{", file=text_file)
        print(f'  "starting-line-cam": [[0, 40]],', file=text_file)
        for a in camera_action_frames:
            if a == 'race_clean_up':
                print(f'  "{a}": {camera_action_frames[a]}', file=text_file)
            else:
                print(f'  "{a}": {camera_action_frames[a]},', file=text_file)
        print("}", file=text_file)


def add_cars_to_scene(blend_rel_path, file_data):
    for i in range(len(file_data)):
        car_collection_path = blend_rel_path + "/race_car.blend/Collection"
        bpy.ops.wm.append(
            directory=car_collection_path,
            link=False, filename="race_car")


def apply_race_data_to_car(file_data, texture_path, race_speed, num_laps, last_frame):
    for racer in file_data:
        car_data = get_team_data(racer, race_speed)
        print("\nRendering race data for " + car_data['team_name'])
        car_customize.modifyCarAttributes(texture_path, car_data['iterString'], car_data['car_number'],
                                          car_data['car_color'], car_data['team_name'])
        curves = []
        last_coord = []
        last_lap_end_time = 0
        for idx, plot_data in enumerate(car_data['plot_file_paths']):
            coords = car_path.get_race_coords(plot_data)
            if len(racer['lap_times']) > idx:
                this_lap = racer['lap_times'][idx]
            else:
                this_lap = racer['overall_time'] - last_lap_end_time
            lap_end_time = this_lap + last_lap_end_time

            curves.append([car_path.generate_path(idx, coords, last_coord, car_data['team_position'], car_data['iterString'],
                                                  this_lap, race_speed), last_lap_end_time, lap_end_time])
            last_coord = coords[-1]
            last_lap_end_time = lap_end_time
        car_path.assign_car_to_path(curves, car_data['iterString'], race_speed, last_frame)

        if car_data['number_laps_complete'] < int(num_laps):
            print("  !!! Add explosion to car " + car_data['team_name'])
            car_explosions.addExplosion(car_data['iterString'], car_data['total_frames'])


def camera_animation_builder(race_json_path, lap_json_path, race_blend_path, today, race_speed):
    camera_action_frames = setup_camera_animations(race_json_path, lap_json_path, race_speed)
    create_render_list_txt(camera_action_frames, race_blend_path, today)


def parse_args(argv):
    parsed_args_dict = {}
    try:
        extra_args = argv[argv.index("--") + 1:]  # get all args after "--"
        parsed_args_dict['today'] = extra_args[0]
        parsed_args_dict['race_name'] = extra_args[1]
        parsed_args_dict['bake_crash_fx'] = extra_args[2] == 'True'
        parsed_args_dict['race_speed'] = extra_args[3]
        parsed_args_dict['num_laps'] = extra_args[4]
    except ValueError:
        parsed_args_dict['today'] = datetime.date.today()
        parsed_args_dict['race_name'] = "deepRacer-sample"
        parsed_args_dict['bake_crash_fx'] = True
        parsed_args_dict['race_speed'] = 1
        parsed_args_dict['num_laps'] = 3

    args_namespace = SimpleNamespace(**parsed_args_dict)
    return args_namespace


def define_file_paths(race_name):
    paths_dict = {}
    paths_dict['code_path'] = deep_racer_utils.get_relative_code_path()
    paths_dict['blender_assets'] = os.path.join(paths_dict['code_path'], "blender_assets")
    paths_dict['car_files'] = os.path.join(paths_dict['blender_assets'], "car_files")
    paths_dict['texture_path'] = os.path.join(paths_dict['blender_assets'], "textures")
    paths_dict['race_blend_path'] = os.path.join(paths_dict['code_path'], "race_blend_files", race_name)
    paths_dict['race_json_path'] = os.path.join(paths_dict['race_blend_path'], "data", "race_data.json")
    paths_dict['lap_json_path'] = os.path.join(paths_dict['race_blend_path'], "data", "lap_data.json")

    paths_namespace = SimpleNamespace(**paths_dict)
    return paths_namespace


def get_last_frame_of_race(race_json, race_speed):
    max_time = sorted(race_json, key=lambda k: k['overall_time'], reverse=True)[0]['overall_time']
    return car_path.get_frames_for_time(max_time, race_speed)


def bake_particles(bake_crash_fx, race_name):
    if bake_crash_fx:
        old = deep_racer_utils.start_output_redirect(race_name, 'bake_fx')
        for scene in bpy.data.scenes:
            for any_object in scene.objects:
                for modifier in any_object.modifiers:
                    if modifier.name.startswith("destroyCar"):
                        bpy.ops.ptcache.bake_all(bake=True)
                        break
        deep_racer_utils.stop_output_redirect(old)


def save_race_blend(race_blend_path, today):
    full_race_blend_path = os.path.join(race_blend_path, f"race_{today}.blend")
    print(f"\nSaving race blend file as: {race_blend_path}")
    bpy.ops.wm.save_as_mainfile(filepath=full_race_blend_path)


def scene_setup():
    args = parse_args(sys.argv)
    paths = define_file_paths(args.race_name)

    with open(paths.race_json_path) as f:
        race_json = json.load(f)

    add_cars_to_scene(paths.car_files, race_json)

    last_frame = get_last_frame_of_race(race_json, args.race_speed)
    bpy.context.scene.frame_end = last_frame

    apply_race_data_to_car(race_json, paths.texture_path, args.race_speed, args.num_laps, last_frame)

    bake_particles(args.bake_crash_fx, args.race_name)

    camera_animation_builder(paths.race_json_path, paths.lap_json_path, paths.race_blend_path, args.today, args.race_speed)

    save_race_blend(paths.race_blend_path, args.today)

    start_grid.create_start_grid_blend(race_json)
    start_grid.save_start_grid_blend(paths.race_blend_path, args.today)


if __name__ == '__main__':
    blend_dir = dirname(bpy.data.filepath)
    code_dir = dirname(dirname(blend_dir))
    script_dir = abspath(join(code_dir, "render_scripts"))

    if script_dir not in sys.path:
        sys.path.append(script_dir)

    import car_path
    import car_customize
    import car_explosions
    import camera_activation
    import get_max_min

    scene_setup()
