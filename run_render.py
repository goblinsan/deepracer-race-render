import datetime
import subprocess
from pathlib import Path
from shutil import copyfile

import yaml

import camera_activation


def build_blend_files():
    subprocess.run([exe_path, "--background", "base_track.blend", "--python", "render_race_data.py", "--", f'{today}'])


def build_camera_blends():
    best_csv, best_time = camera_activation.get_best_car()
    coords = camera_activation.get_race_coords(f"data_prep/{best_csv}")

    # max and min of activation zones in blend file - see get_max_min.py
    zone_1 = camera_activation.create_zone(1, 2.2383158206939697, 3.514540433883667,
                                           0.028154075145721436, 1.2572650909423828)
    zone_2 = camera_activation.create_zone(2, 5.38928747177124, 6.248302936553955,
                                           0.028154075145721436, 1.2572650909423828)
    zone_3 = camera_activation.create_zone(3, 6.485426902770996, 7.8031110763549805,
                                           1.364519476890564, 2.355942487716675)
    zone_4 = camera_activation.create_zone(4, 5.544686794281006, 6.403702259063721,
                                           2.0969109535217285, 3.326022148132324)
    zone_5 = camera_activation.create_zone(5, 0.31292879581451416, 3.658247947692871,
                                           3.757744073867798, 4.9868550300598145)
    zone_6 = camera_activation.create_zone(6, 0.42658960819244385, 1.9064496755599976,
                                           0.8830092549324036, 2.189504861831665)
    zone_list = [zone_1, zone_2, zone_3, zone_4, zone_5, zone_6]

    coord_markers = camera_activation.get_coord_markers(coords, best_time, zone_list + zone_list + zone_list)

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
    blend_file = f'race_{today}.blend'
    exec_args = camera_activation.get_camera_action_frames(coord_markers,
                                                           [camera_01, camera_02, camera_03, camera_04, camera_05,
                                                            camera_06])
    last_mapped_frame = exec_args[-1]
    exec_args.append(['07_race_clean_up', str(last_mapped_frame[-1]), str(int(last_mapped_frame[-1]) + 300)])

    with open("render_list.txt", "w") as text_file:
        for a in exec_args:
            print(a, file=text_file)

    files_to_render = []
    for i, args in enumerate(exec_args):
        print(f'running: {args}')
        render_blend_file = f'race_{today}_camera_{i + 1}.blend'
        files_to_render.append(render_blend_file)
        copyfile(blend_file, render_blend_file)
        subprocess.run([exe_path, "--background", render_blend_file, "--python", "position_camera.py", "--",
                        render_path, args[0], args[1], args[2]])

    return files_to_render


if __name__ == '__main__':
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    exe_path = setup_yml['blender_exe']
    render_path = setup_yml['render_out_dir']
    Path(render_path).mkdir(parents=True, exist_ok=True)
    today = datetime.date.today()

    build_blend_files()
    render_file_list = build_camera_blends()

    for blend_file in render_file_list:
        subprocess.run([exe_path, "-b", blend_file, "-a"])
