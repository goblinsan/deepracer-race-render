import os
import subprocess
from pathlib import Path

import yaml


def runme():
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    exe_path = setup_yml['blender_exe']
    render_path = setup_yml['render_out_dir']

    Path(render_path).mkdir(parents=True, exist_ok=True)
    subprocess.run([exe_path, "--background", "base_track.blend", "--python", "render_race_data.py", "--", render_path])


if __name__ == '__main__':
    runme()
