import os
import sys
from datetime import datetime


def get_relative_blender_path():
    rel_path = ""
    blender_script_dir = os.path.dirname(__file__)
    if blender_script_dir.endswith('.blend'):
        rel_path = "/.."
    blend_rel_path = blender_script_dir + rel_path
    return blend_rel_path


def get_log_path(race_name, name):
    log_path = os.path.join('race_blend_files', race_name, 'logs')
    log_name = f'{name}_{datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.log'
    return os.path.join(log_path, log_name)


def start_output_redirect(race_name, name):
    logfile = get_log_path(race_name, name)
    open(logfile, 'a').close()
    old = os.dup(1)
    sys.stdout.flush()
    os.close(1)
    os.open(logfile, os.O_WRONLY)
    return old


def stop_output_redirect(old):
    os.close(1)
    os.dup(old)
    os.close(old)
