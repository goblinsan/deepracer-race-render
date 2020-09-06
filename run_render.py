import json
import subprocess
from pathlib import Path

import yaml


def get_best_car():
    with open("dat_prep/race_data.json") as f:
        json_file = json.load(f)

    best_car_csv = ''
    best_time = 1000

    for i in json_file:
        car_time = i['lap_time']
        crashed = i['lap_end_state']

        if (crashed != "off_track") and (car_time < best_time):
            best_car_csv = i['plot_file']

    return best_car_csv


def build_blend_files():
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    exe_path = setup_yml['blender_exe']
    render_path = setup_yml['render_out_dir']

    Path(render_path).mkdir(parents=True, exist_ok=True)
    subprocess.run([exe_path, "--background", "base_track.blend", "--python", "render_race_data.py", "--", render_path])


if __name__ == '__main__':
    build_blend_files()
