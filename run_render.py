import subprocess
from pathlib import Path

import yaml


#"blender.exe" --background test-render-script.blend --python test-rendies.py -- booty
def runme():
    with open("render_setup.yml", "r") as file_in:
        setup_yml = yaml.load(file_in, Loader=yaml.FullLoader)
    exe_path = setup_yml['blender_exe']
    render_path = setup_yml['render_out_dir']

    Path(render_path).mkdir(parents=True, exist_ok=True)
    subprocess.run([exe_path, "--background", "test.blend", "--python", "test-rendies.py", "--",  render_path, "jommy"])


if __name__ == '__main__':
    runme()
