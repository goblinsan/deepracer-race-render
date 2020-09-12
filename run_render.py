import datetime
import json
import subprocess
from pathlib import Path

import yaml


def build_blend_files():
    subprocess.run([exe_path, "--background", "base_track.blend", "--python", "render_race_data.py", "--", f'{today}'])


if __name__ == '__main__':
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    exe_path = setup_yml['blender_exe']
    render_path = setup_yml['render_out_dir']
    Path(render_path).mkdir(parents=True, exist_ok=True)
    today = datetime.date.today()

    build_blend_files()

    with open("render_list.json", "r") as render_list_file:
        render_instructions = json.load(render_list_file)

    for camera_name, cam_frames in render_instructions.items():
        print(f'{camera_name} : frames {cam_frames}')

        for frame_set in cam_frames:
            subprocess.run([exe_path, "-b", f'race_{today}.blend', "--python", "render_instructions.py",  "--"
                            , f'{render_path}', f'{today}', f'{camera_name}', f'{frame_set[0]}', f'{frame_set[1]}'])
