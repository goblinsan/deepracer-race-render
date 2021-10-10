import sys

import bpy
import os
import json
from os.path import dirname, abspath, join

blend_dir = dirname(bpy.data.filepath)
code_dir = dirname(blend_dir)
script_dir = abspath(join(code_dir, "render_scripts"))

if script_dir not in sys.path:
    sys.path.append(script_dir)

import deep_racer_utils


def get_render_data(render_list_filepath):
    blend_rel_path = deep_racer_utils.get_relative_code_path()
    r_list = os.path.join(blend_rel_path, render_list_filepath)

    with open(r_list) as f:
        file_data = json.load(f)

    return file_data


def adjust_scale_and_duration(seq, end_frame):
    seq.frame_final_end = end_frame
    seq.transform.scale_x = 2
    seq.transform.scale_y = 2


def setup_race_start(ren_dir):
    seqs = bpy.context.scene.sequence_editor.sequences

    movie_path = os.path.join(ren_dir, "team_intro", "0001-0650.mp4")
    team_intro = seqs.new_movie("team_intro", movie_path, 4, 0)
    adjust_scale_and_duration(team_intro, 650)

    movie_path = os.path.join(ren_dir, "starting-line-cam", "0_40", "0000-0040.mp4")
    frozen_first_frame = seqs.new_movie("frozen_first_frame", movie_path, 5, 626)
    adjust_scale_and_duration(frozen_first_frame, 713)

    freeze_effect = seqs.new_effect("stop_it", 'SPEED', 6, frame_start=626, frame_end=713, seq1=frozen_first_frame)
    freeze_effect.multiply_speed = 0

    seqs.new_effect("cross_fade", 'CROSS', 7, frame_start=626, frame_end=750, seq1=team_intro, seq2=freeze_effect)
    unfrozen_first_frame = seqs.new_movie("frozen_first_frame", movie_path, 5, 713)
    adjust_scale_and_duration(unfrozen_first_frame, 753)


def assemble_clips(ren_list, ren_dir, r_name, r_date):
    print("\n")
    rendered_movies_path = os.path.join(ren_dir, r_name, r_date)
    seqs = bpy.context.scene.sequence_editor.sequences
    render_data = get_render_data(ren_list)

    setup_race_start(rendered_movies_path)
    seq_frame_start = 754

    for lap in range(0, 3):
        for camera_name, cam_frames in render_data.items():
            if camera_name != "starting-line-cam" and camera_name != "race_clean_up" and camera_name != "last-turn":
                if len(cam_frames) > lap:
                    image_path = os.path.join(rendered_movies_path, camera_name, f"{cam_frames[lap][0]}_{cam_frames[lap][1]}",
                                              f"{cam_frames[lap][0]:04}-{cam_frames[lap][1]:04}.mp4")
                    new_seq = seqs.new_movie(camera_name, image_path, 4, seq_frame_start)
                    clip_length = cam_frames[lap][1] - cam_frames[lap][0]
                    seq_frame_start += clip_length
                    adjust_scale_and_duration(new_seq, seq_frame_start)

    cam_frames = render_data['race_clean_up']
    movie_dir = os.path.join(rendered_movies_path, 'race_clean_up', f"{cam_frames[0][0]}_{cam_frames[0][1]}")
    search_string = f"{cam_frames[0][0]:04}"
    final_frame = 4000
    for entry in os.scandir(movie_dir):
        if entry.name.startswith(search_string) and entry.is_file():
            image_path = os.path.join(movie_dir, entry.name)
            new_seq = seqs.new_movie("race_clean_up", image_path, 4, seq_frame_start)
            seq_len = new_seq.frame_final_duration
            final_frame = seq_frame_start + seq_len
            new_seq.transform.scale_x = 2
            new_seq.transform.scale_y = 2

    bpy.context.scene.frame_end = final_frame
    bpy.data.scenes["Scene"].render.filepath = os.path.join(rendered_movies_path, f'{r_name}.mp4')
    blend_rel_path = deep_racer_utils.get_relative_code_path()
    vse_blend_path = os.path.join(blend_rel_path, "race_blend_files", r_name, f"vse_{r_date}.blend")
    print(f"\nSaving race blend file as: {vse_blend_path}")
    bpy.ops.wm.save_as_mainfile(filepath=vse_blend_path)

    # redirect output to log file
    old = deep_racer_utils.start_output_redirect(r_name, 'video_render')

    # create video
    bpy.ops.render.render(animation=True)

    deep_racer_utils.stop_output_redirect(old)


if __name__ == '__main__':
    blend_dir = dirname(bpy.data.filepath)
    code_dir = dirname(dirname(blend_dir))
    script_dir = abspath(join(code_dir, "render_scripts"))

    if script_dir not in sys.path:
        sys.path.append(script_dir)

    argv = sys.argv
    try:
        extra_args = argv[argv.index("--") + 1:]  # get all args after "--"
        render_list = extra_args[0]
        render_dir = extra_args[1]
        race_name = extra_args[2]
        run_date = extra_args[3]
    except ValueError:
        render_list = "render_list_2021-03-08.json"
        render_dir = "D:\\deepRacer\\renders"
        race_name = "e2-trial"
        run_date = "2021-03-08"

    assemble_clips(render_list, render_dir, race_name, run_date)
