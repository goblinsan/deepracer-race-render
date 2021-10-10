import json
import os
import sys
import datetime
from os.path import dirname, abspath, join

import bpy

blend_dir = dirname(bpy.data.filepath)
code_dir = dirname(dirname(blend_dir))
script_dir = abspath(join(code_dir, "render_scripts"))

if script_dir not in sys.path:
    sys.path.append(script_dir)

import deep_racer_utils


def getIterString(team_position):
    iterString = ''
    if team_position > 0:
        iterString = "." + str(team_position).zfill(3)

    return iterString


def get_team_data(race_team_entry, race_speed):
    team_data = {'team_position': int(race_team_entry['starting_position'])}
    team_data['iterString'] = getIterString(team_data['team_position'])
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


def add_viz_toggle_keyframes(banner_obj, start_car_intro, end_car_intro):
    banner_obj.hide_render = False
    banner_obj.keyframe_insert('hide_render', frame=start_car_intro)
    banner_obj.keyframe_insert('hide_render', frame=start_car_intro - 1)
    banner_obj.hide_render = True
    banner_obj.keyframe_insert('hide_render', frame=end_car_intro)


def scene_setup():
    argv = sys.argv

    try:
        extra_args = argv[argv.index("--") + 1:]  # get all args after "--"
        today = extra_args[0]
        race_name = extra_args[1]
        bake_crash_fx = extra_args[2] == 'True'
        race_speed = extra_args[3]
        num_laps = extra_args[4]
    except ValueError:
        today = datetime.date.today()
        race_name = "deepRacer-sample"
        bake_crash_fx = True
        race_speed = 1
        num_laps = 3

    # setup filepath directories to allow script to run in ide or blender
    code_path = deep_racer_utils.get_relative_code_path()
    blender_assets = os.path.join(code_path, "blender_assets")
    car_files = os.path.join(blender_assets, "car_files")
    texture_path = os.path.join(blender_assets, "textures")
    race_blend_path = os.path.join(code_path, "race_blend_files", race_name)
    race_json_path = os.path.join(race_blend_path, "data", "race_data.json")
    lap_json_path = os.path.join(race_blend_path, "data", "lap_data.json")

    with open(race_json_path) as f:
        race_json = json.load(f)

    add_cars_to_scene(car_files, race_json)

    # set animation duration
    max_time = sorted(race_json, key=lambda k: k['overall_time'], reverse=True)[0]['overall_time']
    last_frame = car_path.get_frames_for_time(max_time, race_speed)
    bpy.context.scene.frame_end = last_frame

    apply_race_data_to_car(race_json, texture_path, race_speed, num_laps, last_frame)

    # bake particle collisions for exploding cars
    if bake_crash_fx:
        old = deep_racer_utils.start_output_redirect(race_name, 'bake_fx')
        for scene in bpy.data.scenes:
            for any_object in scene.objects:
                for modifier in any_object.modifiers:
                    if modifier.name.startswith("destroyCar"):
                        bpy.ops.ptcache.bake_all(bake=True)
                        break
        deep_racer_utils.stop_output_redirect(old)

    # setup cameras
    camera_animation_builder(race_json_path, lap_json_path, race_blend_path, today, race_speed)

    # save generated race blend file
    full_race_blend_path = os.path.join(race_blend_path, f"race_{today}.blend")
    print(f"\nSaving race blend file as: {race_blend_path}")
    bpy.ops.wm.save_as_mainfile(filepath=full_race_blend_path)

    # save generated starting grid blend file
    start_grid_blend_path = os.path.join(bpy.path.abspath(race_blend_path), f"starting_grid_{today}.blend")
    print(f"\nCreate Starting Grid and saving file as: {start_grid_blend_path}")

    num_racers = len(race_json)
    for racer in race_json:
        i = int(racer['starting_position'])
        iter_string = getIterString(i)
        car_base = bpy.data.objects[f'car_base{iter_string}']
        bpy.ops.object.select_all(action='DESELECT')
        car_base.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        car_base.modifiers.clear()
        car_base.animation_data_clear()
        objs = [obj for obj in bpy.data.curves if obj.name.startswith("crv_")]
        for ob in objs:
            ob.animation_data_clear()
            ob.path_duration = 650
            ob.eval_time = 0
        objs2 = [obj for obj in bpy.data.curves if obj.name.startswith("crv_") and ('.00' in obj.name)]
        for ob in objs2:
            bpy.data.curves.remove(ob)
        constraints = car_base.constraints
        for c in constraints:
            car_base.constraints.remove(c)

        path_constraint = car_base.constraints.new(type='FOLLOW_PATH')
        path_constraint.use_curve_follow = True
        if iter_string is '':
            iter_int = 0
        else:
            iter_int = int(iter_string[-1])
        path_constraint.target = bpy.data.objects[f'racer_{iter_int}_curve']
        path_constraint.influence = 100

        # setup banner visibility animations
        offset = 120
        end_animation_frame = 400
        frame_per_car = (end_animation_frame - offset) / num_racers
        start_car_intro = (i * frame_per_car) + offset
        end_car_intro = ((i + 1) * frame_per_car) + offset - 5
        add_viz_toggle_keyframes(bpy.data.objects['banner_bg' + iter_string], start_car_intro, end_car_intro)
        add_viz_toggle_keyframes(bpy.data.objects['banner_bg_white' + iter_string], start_car_intro, end_car_intro)
        add_viz_toggle_keyframes(bpy.data.objects['banner_number' + iter_string], start_car_intro, end_car_intro)
        add_viz_toggle_keyframes(bpy.data.objects['team_name' + iter_string], start_car_intro, end_car_intro)
        # add_viz_toggle_keyframes(bpy.data.objects['city_name' + iterString], start_car_intro, end_car_intro)
        add_viz_toggle_keyframes(bpy.data.objects['team_name_depth' + iter_string], start_car_intro, end_car_intro)
        # delete any explosions
        objs = [bpy.data.objects['explode_sprite_color' + iter_string],
                bpy.data.objects['explode_sprite_shadow' + iter_string]]
        bpy.ops.object.delete({"selected_objects": objs})

    for obj in bpy.context.scene.objects:
        if obj.name.startswith("explode_sprite_color"):
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.active_object.animation_data_clear()

    bpy.data.scenes['Scene'].frame_end = 650
    bpy.ops.wm.save_as_mainfile(filepath=start_grid_blend_path)


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
