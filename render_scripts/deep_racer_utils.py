import json
import os
import sys
from datetime import datetime
from os.path import dirname, abspath, join


def get_relative_code_path():
    blender_script_dir = os.path.dirname(__file__)
    code_dir = dirname(blender_script_dir)
    if blender_script_dir.endswith('.blend'):
        code_dir = dirname(dirname(blender_script_dir))
    return code_dir


def get_log_path(race_name, name):
    log_path = os.path.join('race_blend_files', race_name, 'logs')
    log_name = f'{name}_{datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}.log'
    return os.path.join(log_path, log_name)


def get_json(json_path):
    with open(json_path) as f:
        json_file = json.load(f)

    return json_file


def get_frames_for_time(time, race_speed):
    frame_rate = 24
    if int(race_speed) == 0:
        race_speed = 1
    return time * (frame_rate / int(race_speed))


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


def getIterString(team_position):
    iterString = ''
    if team_position > 0:
        iterString = "." + str(team_position).zfill(3)

    return iterString