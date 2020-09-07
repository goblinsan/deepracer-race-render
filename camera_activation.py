import csv
import json


def create_zone(min_x, max_x, min_y, max_y):
    return {
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


def get_coord_markers(coords, zones):
    marker_list = []
    i = 0
    for z, zone in enumerate(zones):
        if z % 6 == 0:
            while is_coord_in_zone(coords[i], zone):
                i += 1
            marker_list.append(i)
        else:
            while not is_coord_in_zone(coords[i], zone):
                i += 1
            marker_list.append(i)
            while is_coord_in_zone(coords[i], zone):
                i += 1

    return marker_list


def convert_markers_to_frames(coord_markers, total_time, total_points):
    frames_per_sec = 24
    total_frames = total_time * frames_per_sec
    frames_per_point = total_frames / total_points

    return [round(coord_index * frames_per_point) for coord_index in coord_markers]


def adjust_key_for_range(existing_frame, old_range, new_range):
    old_corrected_range = old_range[1] - old_range[0]
    new_corrected_range = new_range[1] - new_range[0]
    corrected_start_value = existing_frame - old_range[0]
    percentage = (corrected_start_value * 100) / old_corrected_range
    return (percentage * new_corrected_range / 100) + new_range[0]


if __name__ == '__main__':

    new_frame = adjust_key_for_range(160, [100, 200], [200, 300])
    #[21, 48, 74, 98, 145, 209, 228, 300, 329, 353, 397, 463, 488, 557, 586, 606, 654, 717]

    # best_csv, best_time = get_best_car()
    # coords = get_race_coords(f"data_prep/{best_csv}")
    #
    # # max and min of activation zones in blend file - see get_max_min.py
    # zone_1 = create_zone(2.2383158206939697, 3.514540433883667, 0.028154075145721436, 1.2572650909423828)
    # zone_2 = create_zone(5.38928747177124, 6.248302936553955, 0.028154075145721436, 1.2572650909423828)
    # zone_3 = create_zone(6.485426902770996, 7.8031110763549805, 1.364519476890564, 2.355942487716675)
    # zone_4 = create_zone(5.544686794281006, 6.403702259063721, 2.0969109535217285, 3.326022148132324)
    # zone_5 = create_zone(0.31292879581451416, 3.658247947692871, 3.757744073867798, 4.9868550300598145)
    # zone_6 = create_zone(0.42658960819244385, 1.9064496755599976, 0.8830092549324036, 2.189504861831665)
    # zone_list = [zone_1, zone_2, zone_3, zone_4, zone_5, zone_6]
    #
    # coord_markers = get_coord_markers(coords, zone_list + zone_list + zone_list)
    # print(coord_markers)
    #
    # frame_markers = convert_markers_to_frames(coord_markers, best_time, len(coords))
    # print(frame_markers)




# bpy.ops.nla.action_pushdown(channel_index=9)

# bpy.ops.transform.transform(mode='TIME_TRANSLATE', value=(-24.5914, 0, 0, 0), orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

# bpy.ops.nla.duplicate(linked=False)

import bpy

def adjust_key_for_range(existing_frame, old_range, new_range):
    old_corrected_range = old_range[1] - old_range[0]
    new_corrected_range = new_range[1] - new_range[0]
    corrected_start_value = existing_frame - old_range[0]
    percentage = (corrected_start_value * 100) / old_corrected_range
    return (percentage * new_corrected_range / 100) + new_range[0]

def setup_camera_frames(name, key_range):
    print(f"actions for camera {name}")
    cam = bpy.data.objects[name]
    cam_action_data = cam.animation_data.action

    for g in cam_action_data.groups:
        channel_data = {}
        for channel in g.channels:
            old_keys = []
            for k in channel.keyframe_points:
                old_keys.append(k)

            channel_data[f'{channel.data_path}|{channel.array_index}'] = old_keys
            cam_action_data.fcurves.remove(channel)

        for key in channel_data:
            key_parts = key.split("|")
            new_fcurve = cam_action_data.fcurves.new(key_parts[0], index=int(key_parts[1]), action_group=g.name)
            old_channel = channel_data[key]

            new_fcurve.keyframe_points.insert(key_range[0], old_channel[0].co[1], keyframe_type='KEYFRAME')

            if len(old_channel) > 2:
                old_min = old_channel[0].co[0]
                old_max = old_channel[-1].co[0]
                for mid_key in old_channel[1:-1]:
                    new_frame = adjust_key_for_range(mid_key.co[0], [old_min, old_max], key_range)
                    new_fcurve.keyframe_points.insert(new_frame, mid_key.co[1], keyframe_type='KEYFRAME')

            new_fcurve.keyframe_points.insert(key_range[1], old_channel[-1].co[1], keyframe_type='KEYFRAME')



frames = [21, 48, 74, 98, 145, 209, 228, 300, 329, 353, 397, 463, 488, 557, 586, 606, 654, 717]

setup_camera_frames('01_race_start_cam', frames[0:2])
setup_camera_frames('02_turn_1_close_cam', [frames[1], 150])
setup_camera_frames('03_start_sbend', frames[2:4])
setup_camera_frames('04_thru_sbend', frames[3:5])
setup_camera_frames('05_back_corner', frames[4:6])
setup_camera_frames('06_last_turn', frames[5:7])


