import os
import sys
import datetime
import time

import bpy

blend_dir = os.path.dirname(bpy.data.filepath)
if blend_dir not in sys.path:
    sys.path.append(blend_dir)

argv = sys.argv
try:
    local_args = argv[argv.index("--") + 1:]  # get all args after "--"
    # "--", render_path,  01_race_start_cam, (1, 111)
    render_dir = local_args[0]
    cam_name = local_args[1]
    start_frame = float(local_args[2])
    end_frame = float(local_args[3])
except ValueError:
    print("Missing args.  Usage: <blender_path> --background <blend_file> --python position_camera.py"
          " -- <render_path> <cam_name> <start_frame>, <end_frame>")
    sys.exit(1)

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
            old_keys = None

        for key in channel_data:
            key_parts = key.split("|")
            new_fcurve = cam_action_data.fcurves.new(key_parts[0], index=int(key_parts[1]), action_group=g.name)
            old_channel = channel_data[key]

            keyframe_start = new_fcurve.keyframe_points.insert(key_range[0], old_channel[0].co[1], keyframe_type='KEYFRAME')
            keyframe_start.easing = 'EASE_IN'

            if len(old_channel) > 2:
                old_min = old_channel[0].co[0]
                old_max = old_channel[-1].co[0]
                for mid_key in old_channel[1:-1]:
                    new_frame = adjust_key_for_range(mid_key.co[0], [old_min, old_max], key_range)
                    new_fcurve.keyframe_points.insert(new_frame, mid_key.co[1], keyframe_type='KEYFRAME')

            keyframe_end = new_fcurve.keyframe_points.insert(key_range[1], old_channel[-1].co[1], keyframe_type='KEYFRAME')
            keyframe_end.easing = 'EASE_OUT'


setup_camera_frames(cam_name, (start_frame, end_frame))
timestamp = datetime.datetime.now().timestamp()

cam = bpy.data.objects[cam_name]
cam.select_set(True)
bpy.data.scenes["Scene"].camera = cam
bpy.data.scenes["Scene"].frame_start = start_frame
# if not cam_name == '07_race_clean_up':
#     bpy.data.scenes["Scene"].frame_end = end_frame

bpy.data.scenes["Scene"].frame_end = start_frame

bpy.data.scenes["Scene"].render.filepath = f'{render_dir}/{cam_name}/{timestamp}/'
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
