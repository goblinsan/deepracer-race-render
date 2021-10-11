import csv

import bpy

from deep_racer_utils import get_frames_for_time
from render_race_data import get_team_data
import car_customize, car_explosions


def get_race_coords(csv_filepath):
    with open(csv_filepath) as csvfile:
        reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        next(reader, None)
        return list(reader)


def generate_path(idx, coords, last_coord, racer_number, iter_string, total_frames, race_speed):
    curve_name = "racer_" + str(racer_number) + "_curve"
    # make a new curve
    crv = bpy.data.curves.new('crv_' + str(racer_number), 'CURVE')
    crv.dimensions = '2D'

    # make a new spline in that curve
    spline = crv.splines.new(type='NURBS')

    if idx == 0:
        starting_coords = get_added_coords_for_starting_position(iter_string)
        updated_coords = starting_coords + coords
    else:
        updated_coords = [last_coord] + coords

    # a spline point for each point - already contains 1 point
    spline.points.add(len(updated_coords) - 1)

    # assign the point coordinates to the spline points
    for p, new_co in zip(spline.points, updated_coords):
        p.co = (new_co + [0] + [1.0])

    # make a new object with the curve
    new_curve = bpy.data.objects.new(curve_name, crv)
    bpy.context.scene.collection.objects.link(new_curve)

    # update path duration
    path_time = get_frames_for_time(total_frames, race_speed)
    crv.path_duration = path_time

    return new_curve


def get_added_coords_for_starting_position(iter_string):
    starting_curve = bpy.data.objects["start_grid_curve" + iter_string]
    starting_curve_bez_points = bpy.data.curves["start_grid_curve" + iter_string].splines[0].bezier_points

    xyz1 = starting_curve.matrix_world @ starting_curve_bez_points[0].co
    xyz2 = starting_curve.matrix_world @ starting_curve_bez_points[1].co
    xyz3 = starting_curve.matrix_world @ starting_curve_bez_points[2].co

    return [[xyz1[0], xyz1[1]],
            [xyz2[0], xyz2[1]],
            [xyz3[0], xyz3[1]]]


def assign_car_to_path(curves, iter_string, race_speed, last_frame):
    objects = bpy.data.objects
    car_base = objects['car_base' + iter_string]

    for idx, crv_detail in enumerate(curves):
        curve = crv_detail[0]
        start_frame = round(get_frames_for_time(crv_detail[1], race_speed))
        end_frame = round(get_frames_for_time(crv_detail[2], race_speed))
        length = end_frame - start_frame
        curve.data.use_path = True

        # create animation curve
        anim = curve.data.animation_data_create()
        anim.action = bpy.data.actions.new(f'{curve.data.name}_action')
        fcu = anim.action.fcurves.new("eval_time")

        # set keyframes
        curve.data.keyframe_insert(data_path="eval_time", frame=start_frame)
        curve.data.eval_time = length
        curve.data.keyframe_insert(data_path="eval_time", frame=end_frame)

        # Set keyframes to linear
        for kp in fcu.keyframe_points:
            kp.interpolation = 'LINEAR'

        path_constraint = car_base.constraints.new(type='FOLLOW_PATH')
        path_constraint.use_curve_follow = True
        path_constraint.target = curve
        if idx != 0:
            path_constraint.influence = 0
            path_constraint.keyframe_insert(data_path="influence", frame=0)
            path_constraint.keyframe_insert(data_path="influence", frame=start_frame-1)
        path_constraint.influence = 100
        path_constraint.keyframe_insert(data_path="influence", frame=start_frame)
        path_constraint.keyframe_insert(data_path="influence", frame=end_frame-1)
        if len(curves) > (idx + 1):
            path_constraint.influence = 0
            path_constraint.keyframe_insert(data_path="influence", frame=end_frame)
        else:
            path_constraint.keyframe_insert(data_path="influence", frame=last_frame)

    explode_color = objects['explode_sprite_color' + iter_string]
    explode_color.hide_render = True
    explode_shadow = objects['explode_sprite_shadow' + iter_string]
    explode_shadow.hide_render = True


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
            coords = get_race_coords(plot_data)
            if len(racer['lap_times']) > idx:
                this_lap = racer['lap_times'][idx]
            else:
                this_lap = racer['overall_time'] - last_lap_end_time
            lap_end_time = this_lap + last_lap_end_time

            curves.append([generate_path(idx, coords, last_coord, car_data['team_position'], car_data['iterString'],
                                                  this_lap, race_speed), last_lap_end_time, lap_end_time])
            last_coord = coords[-1]
            last_lap_end_time = lap_end_time
        assign_car_to_path(curves, car_data['iterString'], race_speed, last_frame)

        if car_data['number_laps_complete'] < int(num_laps):
            print("  !!! Add explosion to car " + car_data['team_name'])
            car_explosions.addExplosion(car_data['iterString'], car_data['total_frames'])