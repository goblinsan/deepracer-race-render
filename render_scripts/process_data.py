import json
import os
import tarfile

import pandas as pd
import yaml


def process_logs(eval_log_path, data_path, race_laps):
    print(f'Processing logs from {eval_log_path}')
    with open("team_setup.yml", "r") as yfp:
        file_to_team_map = yaml.load(yfp, Loader=yaml.FullLoader)

    team_data, laps_json = extract_each_team_log(data_path, eval_log_path, file_to_team_map, race_laps)
    race_json = format_team_data(team_data)

    with open(os.path.join(data_path, "race_data.json"), 'w') as fp:
        json.dump(race_json, fp, sort_keys=False, indent=2)

    with open(os.path.join(data_path, "lap_data.json"), 'w') as fp:
        json.dump(laps_json, fp, sort_keys=False, indent=2)


def extract_each_team_log(data_path, eval_log_path, file_to_team_map, race_laps):
    starting_pos = 0
    teams = []
    for team in file_to_team_map:
        team["log_tar_file"] = team["logfile"]
        team["start_pos"] = starting_pos
        team["final_position"] = 'DNF'
        team["number_laps_complete"] = 0
        team["best_complete_lap_time"] = 0
        team["avg_lap_time"] = 0
        team["overall_time"] = 0
        team["trials_to_render"] = []
        team["lap_times"] = []
        print(f'Processing {team["team"]} log file {team["logfile"]}')
        team_eval_log_path = os.path.join(eval_log_path, team["logfile"])

        metrics_file, tar = extract_from_tar(team_eval_log_path, 'metrics', 'evaluation', '.json')
        teams.append(process_team_metrics(metrics_file, team, race_laps))
        if tar is not None:
            tar.close()

        starting_pos += 1

    laps_json = process_race_metrics(teams, race_laps)

    get_trial_coords(eval_log_path, data_path, teams)

    return teams, laps_json


def process_team_metrics(metrics_file, team, number_of_laps):
    metrics_json = json.load(metrics_file)
    sorted_list = sorted(metrics_json["metrics"],
                         key=lambda k: (-k['completion_percentage'], k["elapsed_time_in_milliseconds"]))
    for lap in sorted_list[:number_of_laps]:
        team["overall_time"] += lap["elapsed_time_in_milliseconds"]
        team["trials_to_render"].append(lap["trial"])
        if lap["completion_percentage"] == 100:
            team["number_laps_complete"] += 1
            if team["best_complete_lap_time"] == 0:
                team["best_complete_lap_time"] = lap["elapsed_time_in_milliseconds"]
            team["avg_lap_time"] = team["overall_time"] / team["number_laps_complete"]
            team["lap_times"].append(lap["elapsed_time_in_milliseconds"] / 1000)

    if team["number_laps_complete"] < (number_of_laps - 1):
        team["trials_to_render"] = team["trials_to_render"][:(team["number_laps_complete"] + 1)]

    return team


def process_race_metrics(team_data, number_of_laps):
    team_data.sort(key=lambda x: x["avg_lap_time"])
    finishers = [x for x in team_data if x['number_laps_complete'] == number_of_laps]
    if len(finishers) > 0:
        make_first_place_laps_slowest_to_fastest(finishers[0])
        place = 1
        for finisher in finishers:
            for t in team_data:
                if t["team"] == finisher["team"]:
                    t["final_position"] = place
                    t['lap_times'] = finisher['lap_times']
            place += 1

    return create_lap_results(team_data, number_of_laps)


def make_first_place_laps_slowest_to_fastest(first_place_car):
    first_place_car['lap_times'] = first_place_car['lap_times'][::-1]
    first_place_car['trials_to_render'] = first_place_car['trials_to_render'][::-1]


def create_lap_results(team_data, number_of_laps):
    race = {'laps': []}
    times = {}
    for lap_n in range(number_of_laps):
        lap = {'lap': f'{lap_n+1} / {number_of_laps}', 'racers': []}
        for racer in team_data:
            racer_lap_result = {'number': racer['car'], 'name': racer['team']}
            if len(racer['lap_times']) > lap_n:
                racer_lap_result['laps_complete'] = lap_n + 1
                this_lap_time = racer['lap_times'][lap_n]
                racer_lap_result['lap_time'] = this_lap_time
                if lap_n == 0:
                    racer_lap_result['overall_time'] = this_lap_time
                    times[racer['team']] = this_lap_time
                else:
                    last_lap_time = times[racer['team']]
                    new_overall = round(last_lap_time + this_lap_time, 3)
                    times[racer['team']] = new_overall
                    racer_lap_result['overall_time'] = new_overall
                    racer_lap_result['avg_time'] = round(racer_lap_result['overall_time'] / (lap_n + 1), 3)
            else:
                racer_lap_result['laps_complete'] = len(racer['lap_times'])
                racer_lap_result['overall_time'] = None

            lap['racers'].append(racer_lap_result)
        lap['racers'].sort(key=lambda x: (-x['laps_complete'], x['overall_time']))
        race['laps'].append(lap)

    for lap in race['laps']:
        best_time = lap['racers'][0]['overall_time']
        for racer in lap['racers'][1:]:
            if racer['overall_time'] is not None:
                racer['diff'] = f'+{round(racer["overall_time"] - best_time, 3)}'

    return race


def get_trial_coords(eval_log_path, data_path, team_data):
    for team in team_data:
        team_eval_log_path = os.path.join(eval_log_path, team['log_tar_file'])
        sim_file, tar = extract_from_tar(team_eval_log_path, 'sim-trace', 'evaluation', '.csv')
        process_sim_trace(data_path, sim_file, team)

        if tar is not None:
            tar.close()


def process_sim_trace(data_path, sim_logs, team):
    df = pd.read_csv(sim_logs, usecols=['episode', 'X', 'Y'])
    team['plot_data'] = []
    for trial in team['trials_to_render']:
        race_data_file = f"{team['team']}_trial_{trial}.csv".replace(" ", "_").lower()
        path_for_team_csv = os.path.join(data_path, race_data_file)
        loc_data = df[(df['episode'] == trial-1)][['X', 'Y']]
        loc_data.to_csv(path_for_team_csv, header=False, index=False)
        team['plot_data'].append(path_for_team_csv)


def format_team_data(team_data):
    race_json = []
    for team in team_data:
        race_team_json = {"team": team['team'],
                          "final_position": team['final_position'],
                          "starting_position": team['start_pos'],
                          "number_laps_complete": team["number_laps_complete"],
                          "best_complete_lap_time": team["best_complete_lap_time"] / 1000,
                          "avg_lap_time": round(team["avg_lap_time"] / 1000, 2),
                          "overall_time": team["overall_time"] / 1000,
                          "lap_times": team["lap_times"],
                          "car_no": team['car'],
                          "car_color": hex(team['color']),
                          "plot_data": team['plot_data']
                          }
        race_json.append(race_team_json)

    return race_json


def extract_from_tar(team_eval_log_path, log_type, sub_type, log_extension):
    f = None
    if tarfile.is_tarfile(team_eval_log_path):
        tar = tarfile.open(team_eval_log_path, "r:gz")
        for tarinfo in tar:
            if log_type in tarinfo.name and sub_type in tarinfo.name and log_extension in tarinfo.name:
                member = tar.getmember(tarinfo.name)
                f = tar.extractfile(member)
    else:
        print(f'Failed to open. This is not a tar file:  {team_eval_log_path}')
        tar = None

    return f, tar
