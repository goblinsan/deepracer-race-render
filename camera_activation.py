import csv
import json


def create_zone(id, min_x, max_x, min_y, max_y):
    return {
        "id": id,
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y
    }


def get_best_car():
    with open("data_prep/race_data_best_3laps/race_data.json") as f:
        json_file = json.load(f)

    best_car_csv = ''
    best_time = 1000

    for i in json_file:
        car_time = i['lap_time']
        crashed = i['lap_end_state']

        if (crashed != "off_track") and (car_time < best_time):
            best_time = car_time
            best_car_csv = i['plot_file']

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


def convert_markers_to_frames(coord_marker, total_time, total_points):
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
    for z, zone in enumerate(zones):
        if z % 6 == 0:
            lap += 1
            while is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap] = {}
            marker_map[lap][zone["id"]] = {}
            marker_map[lap][zone["id"]]["exit"] = round(i * frames_per_point)
        else:
            while not is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap][zone["id"]] = {}
            marker_map[lap][zone["id"]]["enter"] = round(i * frames_per_point)
            while is_coord_in_zone(coords[i], zone):
                i += 1
            marker_map[lap][zone["id"]]["exit"] = round(i * frames_per_point)
            if z % 6 == 5:
                while not is_coord_in_zone(coords[i], zones[0]):
                    i += 1
                marker_map[lap][zones[0]["id"]]["enter"] = round(i * frames_per_point)

    return marker_map


def get_camera_action_frames(markers, cam_rules):
    camera_actions = []
    start_frame_padding = 24
    end_frame_padding = 50

    for cam_rule in cam_rules:
        cam_name = cam_rule['name']
        rule = cam_rule['rule']
        for i in range(1, 4):
            start_frame = markers[i][rule[0][1]][rule[0][0]]
            start_frame = max(1, start_frame - start_frame_padding)
            end_frame = markers[i][rule[1][1]][rule[1][0]]
            end_frame = end_frame + end_frame_padding
            camera_actions.append([cam_name, str(start_frame), str(end_frame)])

    return camera_actions


if __name__ == '__main__':
    best_csv, best_time = get_best_car()
    coords = get_race_coords(f"data_prep/{best_csv}")

    # max and min of activation zones in blend file - see get_max_min.py
    zone_1 = create_zone(1, 2.2383158206939697, 3.514540433883667, 0.028154075145721436, 1.2572650909423828)
    zone_2 = create_zone(2, 5.38928747177124, 6.248302936553955, 0.028154075145721436, 1.2572650909423828)
    zone_3 = create_zone(3, 6.485426902770996, 7.8031110763549805, 1.364519476890564, 2.355942487716675)
    zone_4 = create_zone(4, 5.544686794281006, 6.403702259063721, 2.0969109535217285, 3.326022148132324)
    zone_5 = create_zone(5, 0.31292879581451416, 3.658247947692871, 3.757744073867798, 4.9868550300598145)
    zone_6 = create_zone(6, 0.42658960819244385, 1.9064496755599976, 0.8830092549324036, 2.189504861831665)
    zone_list = [zone_1, zone_2, zone_3, zone_4, zone_5, zone_6]

    coord_markers = get_coord_markers(coords, best_time, zone_list + zone_list + zone_list)

    # rules for activating cameras
    # cam 01 exit zone 1, exit zone 2
    # cam 02 enter zone 2, exit zone 4
    # cam 03 enter zone 3, enter zone 5
    # cam 04 enter zone 5, exit zone 5
    # cam 05 enter zone 5, enter zone 6
    # cam 06 exit zone 5, exit zone 6

    camera_01 = {'name': '01_race_start_cam', 'rule': [("exit", 1), ("exit", 2)]}
    camera_02 = {'name': '02_turn_1_close_cam', 'rule': [("enter", 2), ("exit", 4)]}
    camera_03 = {'name': '03_start_sbend', 'rule': [("enter", 3), ("enter", 5)]}
    camera_04 = {'name': '04_thru_sbend', 'rule': [("enter", 5), ("exit", 5)]}
    camera_05 = {'name': '05_back_corner', 'rule': [("enter", 5), ("enter", 6)]}
    camera_06 = {'name': '06_last_turn', 'rule': [("exit", 5), ("exit", 6)]}
    blender_exe = "C:\\Program Files\\Blender Foundation\\Blender 2.90\\blender.exe"
    exec_commands = get_camera_action_frames(coord_markers,
                                             [camera_01, camera_02, camera_03, camera_04, camera_05, camera_06])


