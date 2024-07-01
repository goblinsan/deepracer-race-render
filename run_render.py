import datetime
import json
import os
import subprocess
from pathlib import Path

import yaml

from render_scripts.deep_racer_utils import get_log_path
from render_scripts.process_data import process_logs


def build_blend_files():
    subprocess.run([exe_path, "--background", base_blend, "--python", "render_scripts/render_race_data.py",
                    "--", f'{run_date}', f'{race_name}', f'{start_render}', f'{bake_crash_fx}', f'{race_speed}', f'{race_laps}', f'{car_scale}'])



if __name__ == '__main__':
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    eval_log_path = setup_yml['log_path']
    exe_path = setup_yml['blender_exe']
    base_blend = f'blender_assets/track_files/{setup_yml["base_blender_file"]}'
    race_name = setup_yml['race_name']
    render_path = setup_yml['render_out_dir']
    race_laps = setup_yml['race_laps']
    car_scale = setup_yml['car_scale']
    start_render = setup_yml['start_render']
    one_frame_render = setup_yml['one_frame_render']
    bake_crash_fx = setup_yml['bake_crash_fx']
    assemble_video = setup_yml['assemble_video']
    race_speed = setup_yml['race_speed']
    Path(render_path).mkdir(parents=True, exist_ok=True)
    save_path = os.path.join("race_blend_files", race_name)
    Path(save_path).mkdir(parents=True, exist_ok=True)
    logfile_path = os.path.join(save_path, "logs")
    Path(logfile_path).mkdir(parents=True, exist_ok=True)
    data_path = os.path.join(save_path, "data")
    Path(data_path).mkdir(parents=True, exist_ok=True)
    run_date = datetime.date.today()
    render_list_file_path = os.path.join(save_path, f"render_list_{run_date}.json")

    process_logs(eval_log_path, data_path, race_laps)

    build_blend_files()
    print(f'Track progress in the logs being written in this location: {os.path.abspath(logfile_path)}')


    if start_render:
        with open(render_list_file_path, "r") as render_list_file:
            render_instructions = json.load(render_list_file)
        logfile = get_log_path(race_name, 'intro_render')
        end_frame_flag = ''
        end_frame_value = ''
        process_args = []
        if one_frame_render:
            print("Rendering 1 frame")
            process_args = [exe_path, "-b", os.path.join('race_blend_files', race_name, f'starting_grid_{run_date}.blend'), "-o",
                            f'{render_path}/{race_name}/{run_date}/team_intro/', "-e", "1", "-a"]
        else:
            process_args = [exe_path, "-b", os.path.join('race_blend_files', race_name, f'starting_grid_{run_date}.blend'), "-o",
                            f'{render_path}/{race_name}/{run_date}/team_intro/', "-a"]

        with open(logfile, 'w') as fp:
            subprocess.run(process_args, stdout=fp)

        for camera_name, cam_frames in render_instructions.items():
            print(f'{camera_name} : frames {cam_frames}')

            if start_render and camera_name != 'last-turn':
                for frame_set in cam_frames:
                    subprocess.run(
                        [exe_path, "-b", os.path.join('race_blend_files', race_name, f'race_{run_date}.blend'), "--python",
                         "render_scripts/render_instructions.py", "--",
                         f'{render_path}', f'{race_name}', f'{run_date}', f'{camera_name}', f'{frame_set[0]}',
                         f'{frame_set[1]}', f'{logfile_path}', f'{one_frame_render}'])

        if assemble_video:
            subprocess.run([exe_path, "-b", "blender_assets/vid_assemble_base.blend", "--python", "render_scripts/assemble_video_clips.py",
                            "--", f'{render_list_file_path}', f'{render_path}', f'{race_name}', f'{run_date}'])
