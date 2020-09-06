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

    return best_car_csv


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


if __name__ == '__main__':

    print(get_best_car())
    coords = get_race_coords(f"data_prep/{get_best_car()}")

    # max and min of activation zones in blend file - see get_max_min.py
    zone_1 = create_zone(2.2383158206939697, 3.514540433883667, 0.028154075145721436, 1.2572650909423828)
    zone_2 = create_zone(5.38928747177124, 6.248302936553955, 0.028154075145721436, 1.2572650909423828)
    zone_3 = create_zone(6.485426902770996, 7.8031110763549805, 1.364519476890564, 2.355942487716675)
    zone_4 = create_zone(5.544686794281006, 6.403702259063721, 2.0969109535217285, 3.326022148132324)
    zone_5 = create_zone(0.31292879581451416, 3.658247947692871, 3.757744073867798, 4.9868550300598145)
    zone_6 = create_zone(0.42658960819244385, 1.9064496755599976, 0.8830092549324036, 2.189504861831665)

    coord_markers = []
    i = 0
    while is_coord_in_zone(coords[i], zone_1):
        i += 1
    coord_markers.append(i)
    while not is_coord_in_zone(coords[i], zone_2):
        i += 1
    coord_markers.append(i)
    while is_coord_in_zone(coords[i], zone_2):
        i += 1
    while not is_coord_in_zone(coords[i], zone_3):
        i += 1
    coord_markers.append(i)
    while is_coord_in_zone(coords[i], zone_3):
        i += 1
    while not is_coord_in_zone(coords[i], zone_4):
        i += 1
    coord_markers.append(i)
    while is_coord_in_zone(coords[i], zone_4):
        i += 1
    while not is_coord_in_zone(coords[i], zone_5):
        i += 1
    coord_markers.append(i)
    while is_coord_in_zone(coords[i], zone_5):
        i += 1
    while not is_coord_in_zone(coords[i], zone_6):
        i += 1
    coord_markers.append(i)

    print(coord_markers)

# total_time * 24 / num_points = frames per point

# bpy.ops.nla.action_pushdown(channel_index=9)

# bpy.ops.transform.transform(mode='TIME_TRANSLATE', value=(-24.5914, 0, 0, 0), orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

# bpy.ops.nla.duplicate(linked=False)
