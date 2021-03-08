import sys

import bpy

argv = sys.argv
try:
    extra_args = argv[argv.index("--") + 1:]  # get all args after "--"
    render_dir = extra_args[0]
    race_name = extra_args[1]
    today = extra_args[2]
    cam_name = extra_args[3]
    start_frame = int(extra_args[4])
    end_frame = int(extra_args[5])
except ValueError:
    print("Expecting args: render_dir, race_name, today, camera name, start frame, end frame")
    sys.exit(1)

cam = bpy.data.objects[cam_name]
cam.select_set(True)
bpy.data.scenes["Scene"].camera = cam
bpy.data.scenes["Scene"].frame_start = start_frame
if not cam_name == 'race_clean_up':
    bpy.data.scenes["Scene"].frame_end = end_frame

# uncomment the following for quick 1 frame tests
# bpy.data.scenes["Scene"].frame_end = start_frame

# point explosion animation at camera
for obj in bpy.context.scene.objects:
    if obj.name.startswith("explode_sprite_color"):
        obj.constraints["Locked Track"].target = cam

bpy.data.scenes["Scene"].render.filepath = f'{render_dir}/{race_name}/{today}/{cam_name}/{start_frame}_{end_frame}/'

bpy.ops.render.render(animation=True)
