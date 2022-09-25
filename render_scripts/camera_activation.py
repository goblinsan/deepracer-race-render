import csv
import os
import bpy

import deep_racer_utils
import get_max_min


def create_zone(id, min_x, max_x, min_y, max_y):
    return {
        "id": id,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y
    }


def get_race_coords(csv_filepath):
    with open(csv_filepath) as csvfile:
        reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        next(reader, None)
        return list(reader)


def point_in_range(point, min_val, max_val):
    return min_val < point < max_val


def is_coord_in_zone(coord, zone):
    return point_in_range(coord[0], zone['min_x'], zone['max_x']) \
           and point_in_range(coord[1], zone['min_y'], zone['max_y'])


def get_coord_markers(idx, coords, lap_time, overall_time, zones, number_of_laps, race_speed):
    tot_points = len(coords)
    total_frames = deep_racer_utils.get_frames_for_time(lap_time, race_speed)
    start_frame_offset = deep_racer_utils.get_frames_for_time(overall_time, race_speed) - total_frames
    frames_per_point = total_frames / tot_points

    marker_map = {}
    i = idx
    lap = idx
    zones_per_lap = len(zones) / number_of_laps
    for z, zone in enumerate(zones):
        if z % zones_per_lap == 0:
            lap += 1
            while i < len(coords) and is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap] = {}
            marker_map[lap][zone["id"]] = {}
            marker_map[lap][zone["id"]]["exit"] = round((i * frames_per_point) + start_frame_offset)
        else:
            while i < len(coords) and not is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap][zone["id"]] = {}
            marker_map[lap][zone["id"]]["enter"] = round((i * frames_per_point) + start_frame_offset)
            while i < len(coords) and is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap][zone["id"]]["exit"] = round((i * frames_per_point) + start_frame_offset)
            if z % zones_per_lap == zones_per_lap - 1:
                while i < len(coords) and not is_coord_in_zone(coords[i], zones[0]):
                    i += 1
                marker_map[lap][zones[0]["id"]]["enter"] = round((i * frames_per_point) + start_frame_offset)

    return marker_map


def get_camera_action_frames_dic(markers, cam_rules, num_laps):
    camera_actions = {}
    end_frame_padding = 50

    for cam_rule in cam_rules:
        cam_name = cam_rule['name']
        rule = cam_rule['rule']
        lap_frames = []
        for i in range(0, int(num_laps)):
            start_frame = markers[i][i + 1][rule[0][1]][rule[0][0]]
            if cam_name == 'finish-line-tight':
                end_frame = start_frame + 150
            else:
                end_frame = markers[i][i + 1][rule[1][1]][rule[1][0]]
            end_frame = end_frame + end_frame_padding
            lap_frames.append([start_frame, end_frame])
        camera_actions[cam_name] = lap_frames

    return camera_actions


def create_zone_list():
    z_list = []
    for i in range(1, 4):
        zone_cube = bpy.data.objects[f'activation_bounds_{i}']
        min_x, max_x, min_y, max_y = get_max_min.get_zone_max_min(zone_cube)
        z_list.append(create_zone(i, min_x, max_x, min_y, max_y))

    return z_list


def setup_camera_animations(race_json_path, lap_json_path, race_speed, num_laps):
    race_json = deep_racer_utils.get_json(race_json_path)
    lap_json = deep_racer_utils.get_json(lap_json_path)

    zone_list = create_zone_list()

    coord_markers = []
    for idx, lap in enumerate(lap_json['laps']):
        fastest_car = lap['racers'][0]['name']
        print(f'Fastest car in lap {lap["lap"]} is {fastest_car}')
        fastest_team_json = [x for x in race_json if x["team"] == fastest_car][0]
        fastest_plot = fastest_team_json['plot_data'][idx]
        best_coords = get_race_coords(fastest_plot)
        best_time = lap['racers'][0]['lap_time']
        overall_time = lap['racers'][0]['overall_time']
        coord_markers.append(
            get_coord_markers(idx, best_coords, best_time, overall_time, zone_list, len(lap_json),
                                                race_speed))

    camera_01 = {'name': 'high-starting-line', 'rule': [("exit", 1), ("enter", 2)]}
    camera_02 = {'name': 'front_chicane', 'rule': [("enter", 2), ("exit", 2)]}
    camera_03 = {'name': 'back-corner', 'rule': [("exit", 2), ("enter", 3)]}
    camera_04 = {'name': 'back_chicane', 'rule': [("enter", 3), ("exit", 3)]}
    camera_05 = {'name': 'last-turn', 'rule': [("exit", 3), ("enter", 1)]}
    camera_06 = {'name': 'finish-line-tight', 'rule': [("enter", 1), ("exit", 1)]}
    camera_action_frames = get_camera_action_frames_dic(coord_markers,
                                                                          [camera_01, camera_02, camera_03, camera_04,
                                                                           camera_05,
                                                                           camera_06], num_laps)
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


def camera_animation_builder(start_render, race_json_path, lap_json_path, race_blend_path, today, race_speed, num_laps):
    if start_render:
        camera_action_frames = setup_camera_animations(race_json_path, lap_json_path, race_speed, num_laps)
        create_render_list_txt(camera_action_frames, race_blend_path, today)