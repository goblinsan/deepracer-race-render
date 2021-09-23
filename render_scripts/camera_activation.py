import csv

from deep_racer_utils import get_frames_for_time


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


def convert_markers_to_frames(coord_markers, total_time, total_points):
    frames_per_sec = 24
    total_frames = total_time * frames_per_sec
    frames_per_point = total_frames / total_points

    return [round(coord_index * frames_per_point) for coord_index in coord_markers]


def get_coord_markers(idx, coords, lap_time, overall_time, zones, number_of_laps, race_speed):
    tot_points = len(coords)
    total_frames = get_frames_for_time(lap_time, race_speed)
    start_frame_offset = get_frames_for_time(overall_time, race_speed) - lap_time
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


def get_camera_action_frames_dic(markers, cam_rules):
    camera_actions = {}
    end_frame_padding = 50

    for cam_rule in cam_rules:
        cam_name = cam_rule['name']
        rule = cam_rule['rule']
        lap_frames = []
        for i in range(0, 3):
            start_frame = markers[i][i + 1][rule[0][1]][rule[0][0]]
            if cam_name == 'finish-line-tight':
                end_frame = start_frame + 150
            else:
                end_frame = markers[i][i + 1][rule[1][1]][rule[1][0]]
            end_frame = end_frame + end_frame_padding
            lap_frames.append([start_frame, end_frame])
        camera_actions[cam_name] = lap_frames

    return camera_actions
