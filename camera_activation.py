import csv
import json


# zone 1 = 1.2403910160064697 3.9279534816741943 0.153300940990448 2.0189640522003174
# zone 2 = 3.2522759437561035 6.692943096160889 3.043959379196167 7.0091400146484375
# zone 3 = -0.6423678398132324 1.0136831998825073 2.5231447219848633 4.788795471191406

def create_zone(id, min_x, max_x, min_y, max_y):
    return {
        "id": id,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y
    }


def get_best_car(data_path="data_prep/race_data_best_3laps/race_data.json"):
    with open(data_path) as f:
        json_file = json.load(f)

    best_car_csv = ''
    best_time = 1000
    best_progress = 0
    best_progress_csv = ''
    best_progress_time = 1000

    for i in json_file:
        car_time = i['lap_time']
        crashed = i['lap_end_state']
        car_progress = i['lap_progress']

        if (crashed != "off_track") and (car_time < best_time):
            best_time = car_time
            best_car_csv = i['plot_file']

        if (car_progress > best_progress):
            best_progress = car_progress
            best_progress_csv = i['plot_file']
            best_progress_time = car_time

    # Edge case: no car finishes
    if len(best_car_csv) < 2:
        best_car_csv = best_progress_csv
        best_time = best_progress_time

    print(f"Best Car: {best_car_csv}")
    return best_car_csv, best_time


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


def convert_markers_to_frames(coord_markers, total_time, total_points):
    frames_per_sec = 24
    total_frames = total_time * frames_per_sec
    frames_per_point = total_frames / total_points

    return [round(coord_index * frames_per_point) for coord_index in coord_markers]


def get_coord_markers(coords, tot_time, zones):
    tot_points = len(coords)
    frames_per_sec = 24
    total_frames = tot_time * frames_per_sec
    frames_per_point = total_frames / tot_points

    marker_map = {}
    i = 0
    lap = 0
    number_of_laps = 3
    zones_per_lap = len(zones) / number_of_laps
    for z, zone in enumerate(zones):
        if z % zones_per_lap == 0:
            lap += 1
            while i < len(coords) and is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap] = {}
            marker_map[lap][zone["id"]] = {}
            marker_map[lap][zone["id"]]["exit"] = round(i * frames_per_point)
        else:
            while i < len(coords) and not is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap][zone["id"]] = {}
            marker_map[lap][zone["id"]]["enter"] = round(i * frames_per_point)
            while i < len(coords) and is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap][zone["id"]]["exit"] = round(i * frames_per_point)
            if z % zones_per_lap == zones_per_lap - 1:
                while i < len(coords) and not is_coord_in_zone(coords[i], zones[0]):
                    i += 1
                marker_map[lap][zones[0]["id"]]["enter"] = round(i * frames_per_point)

    return marker_map


def get_camera_action_frames_dic(markers, cam_rules):
    camera_actions = {}
    end_frame_padding = 50

    for cam_rule in cam_rules:
        cam_name = cam_rule['name']
        rule = cam_rule['rule']
        lap_frames = []
        for i in range(1, 4):
            start_frame = markers[i][rule[0][1]][rule[0][0]]
            if cam_name == 'finish-line-tight':
                end_frame = start_frame + 150
            else:
                end_frame = markers[i][rule[1][1]][rule[1][0]]
            end_frame = end_frame + end_frame_padding
            lap_frames.append([start_frame, end_frame])
        camera_actions[cam_name] = lap_frames

    return camera_actions
