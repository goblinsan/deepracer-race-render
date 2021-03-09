import datetime
import json
import os
import subprocess
from pathlib import Path

import yaml


def build_blend_files():
    subprocess.run([exe_path, "--background", base_blend, "--python", "render_race_data.py",
                    "--", f'{today}', f'{race_name}', f'{bake_crash_fx}'])


if __name__ == '__main__':
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    exe_path = setup_yml['blender_exe']
    base_blend = setup_yml['base_blender_file']
    race_name = setup_yml['race_name']
    render_path = setup_yml['render_out_dir']
    start_render = setup_yml['start_render']
    bake_crash_fx = setup_yml['bake_crash_fx']
    Path(render_path).mkdir(parents=True, exist_ok=True)
    save_path = os.path.join("race_blend_files", race_name)
    Path(save_path).mkdir(parents=True, exist_ok=True)
    today = datetime.date.today()

    build_blend_files()

    with open(f"render_list_{today}.json", "r") as render_list_file:
        render_instructions = json.load(render_list_file)

    if start_render:
        subprocess.run([exe_path, "-b", os.path.join('race_blend_files', race_name, f'starting_grid_{today}.blend'), "-o",
                    f'{render_path}/{race_name}/{today}/team_intro/', "-a"])

    for camera_name, cam_frames in render_instructions.items():
        print(f'{camera_name} : frames {cam_frames}')

        if start_render:
            for frame_set in cam_frames:
                subprocess.run([exe_path, "-b", os.path.join('race_blend_files', race_name, f'race_{today}.blend'), "--python",
                                "render_instructions.py", "--",
                                f'{render_path}', f'{race_name}', f'{today}', f'{camera_name}', f'{frame_set[0]}', f'{frame_set[1]}'])

