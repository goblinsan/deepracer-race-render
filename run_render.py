import datetime
import json
import os
import subprocess
from pathlib import Path

import yaml


def build_blend_files():
    subprocess.run([exe_path, "--background", base_blend, "--python", "render_race_data.py",
                    "--", f'{run_date}', f'{race_name}', f'{bake_crash_fx}'])


if __name__ == '__main__':
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    exe_path = setup_yml['blender_exe']
    base_blend = setup_yml['base_blender_file']
    race_name = setup_yml['race_name']
    render_path = setup_yml['render_out_dir']
    start_render = setup_yml['start_render']
    bake_crash_fx = setup_yml['bake_crash_fx']
    assemble_video = setup_yml['assemble_video']
    Path(render_path).mkdir(parents=True, exist_ok=True)
    save_path = os.path.join("race_blend_files", race_name)
    Path(save_path).mkdir(parents=True, exist_ok=True)
    logfile_path = os.path.join(save_path, "logs")
    Path(logfile_path).mkdir(parents=True, exist_ok=True)
    run_date = datetime.date.today()
    # run_date = '2021-03-08'

    build_blend_files()

    with open(f"render_list_{run_date}.json", "r") as render_list_file:
        render_instructions = json.load(render_list_file)

    if start_render:
        subprocess.run(
            [exe_path, "-b", os.path.join('race_blend_files', race_name, f'starting_grid_{run_date}.blend'), "-o",
             f'{render_path}/{race_name}/{run_date}/team_intro/', "-a"])

    for camera_name, cam_frames in render_instructions.items():
        print(f'{camera_name} : frames {cam_frames}')

        if start_render:
            for frame_set in cam_frames:
                subprocess.run(
                    [exe_path, "-b", os.path.join('race_blend_files', race_name, f'race_{run_date}.blend'), "--python",
                     "render_instructions.py", "--",
                     f'{render_path}', f'{race_name}', f'{run_date}', f'{camera_name}', f'{frame_set[0]}',
                     f'{frame_set[1]}'])

    if assemble_video:
        subprocess.run([exe_path, "-b", "vid_assemble_base.blend", "--python", "assemble_video_clips.py",
                        "--", f'render_list_{run_date}.json', f'{render_path}', f'{race_name}', f'{run_date}'])
