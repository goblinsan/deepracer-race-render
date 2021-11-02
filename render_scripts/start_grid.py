import os
import re

import bpy

from deep_racer_utils import getIterString


def add_viz_toggle_keyframes(banner_obj, start_car_intro, end_car_intro):
    banner_obj.hide_render = False
    banner_obj.keyframe_insert('hide_render', frame=start_car_intro)
    banner_obj.keyframe_insert('hide_render', frame=start_car_intro - 1)
    banner_obj.hide_render = True
    banner_obj.keyframe_insert('hide_render', frame=end_car_intro)


def remove_race_data(car_base):
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


def add_start_path(car_base, start_curve_slot):
    path_constraint = car_base.constraints.new(type='FOLLOW_PATH')
    path_constraint.use_curve_follow = True
    path_constraint.target = bpy.data.objects[f'racer_{start_curve_slot}_curve']
    path_constraint.influence = 100


def animate_banner_visibility(i, iter_string, num_racers):
    offset = 120
    end_animation_frame = 400
    frame_per_car = (end_animation_frame - offset) / num_racers
    start_car_intro = (i * frame_per_car) + offset
    end_car_intro = ((i + 1) * frame_per_car) + offset - 5
    add_viz_toggle_keyframes(bpy.data.objects['banner_bg' + iter_string], start_car_intro, end_car_intro)
    add_viz_toggle_keyframes(bpy.data.objects['banner_bg_white' + iter_string], start_car_intro, end_car_intro)
    add_viz_toggle_keyframes(bpy.data.objects['banner_number' + iter_string], start_car_intro, end_car_intro)
    add_viz_toggle_keyframes(bpy.data.objects['team_name' + iter_string], start_car_intro, end_car_intro)
    add_viz_toggle_keyframes(bpy.data.objects['city_name' + iter_string], start_car_intro, end_car_intro)
    add_viz_toggle_keyframes(bpy.data.objects['team_name_depth' + iter_string], start_car_intro, end_car_intro)


def delete_explosions():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("explode_sprite_color") or obj.name.startswith("explode_sprite_shadow"):
            bpy.context.object.hide_viewport = False
            obj.select_set(True)
            constraints = obj.constraints
            for c in constraints:
                obj.constraints.remove(c)
            bpy.data.objects.remove(obj)


def create_start_grid_blend(race_json):
    num_racers = len(race_json)
    for racer in race_json:
        start_pos = int(racer['starting_position'])
        iter_string = getIterString(start_pos)
        car_base = bpy.data.objects[f'car_base{iter_string}']
        remove_race_data(car_base)
        add_start_path(car_base, start_pos)
        animate_banner_visibility(start_pos, iter_string, num_racers)
        delete_explosions()

    bpy.data.scenes['Scene'].frame_end = 650


def save_start_grid_blend(race_blend_path, today):
    start_grid_blend_path = os.path.join(bpy.path.abspath(race_blend_path), f"starting_grid_{today}.blend")
    print(f"\nCreate Starting Grid and saving file as: {start_grid_blend_path}")
    bpy.ops.wm.save_as_mainfile(filepath=start_grid_blend_path)