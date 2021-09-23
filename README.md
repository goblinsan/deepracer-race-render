# 2021-deepracer-final

Steps to render a race:
1. Download the race cloudwatch logs to somewhere on your computer
4. Update render_setup.yml with where blender is installed, and where you want the render video output to go
2. Configure the race teams in team_setup.yml
5. Run the run_render.py script
6. The process will create a video in the location you declared i  `render_out_dir` in the render_setup.yml
