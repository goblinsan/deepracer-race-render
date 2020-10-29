import yaml
import argparse
import json
import pandas as pd
import numpy as np
from os import path
from os import chdir
from os import makedirs


def bomType(file):
    """
    returns file encoding string for open() function

    EXAMPLE:
        bom = bomtype(file)
        open(file, encoding=bom, errors='ignore')
    """

    f = open(file, 'rb')
    b = f.read(4)
    f.close()

    if (b[0:3] == b'\xef\xbb\xbf'):
        return "utf8"

    # Python automatically detects endianess if utf-16 bom is present
    # write endianess generally determined by endianess of CPU
    if ((b[0:2] == b'\xfe\xff') or (b[0:2] == b'\xff\xfe')):
        return "utf16"

    if ((b[0:5] == b'\xfe\xff\x00\x00') 
              or (b[0:5] == b'\x00\x00\xff\xfe')):
        return "utf32"

    # If BOM is not provided, then assume its the codepage
    #     used by your operating system
    return "cp1252"
    # For the United States its: cp1252


def OpenRead(file):
    bom = bomType(file)
    return open(file, 'r', encoding=bom, errors='ignore')


def parse_message( message_text ):

    hdr = "episode,step,x-coordinate,y-coordinate,heading,steering_angle,speed,action_taken,reward,job_completed,all_wheels_on_track,progress, closest_waypoint_index,track_length,time,state"
    message_text = message_text.replace('SIM_TRACE_LOG:','')

    headers = hdr.split(",")
    data = message_text.replace('SIM_TRACE_LOG:','').split(",")
    
    data_dict = {}
    for i in range(len(data)):
        data_dict[headers[i]] = data[i]

    return data_dict    

def evaluate_and_sort( raw_log_data ):

    # Data conditioning
    df = pd.DataFrame(raw_log_data)
    df = df[["team","car_no","color","start_pos","episode","step","time",
             "progress","state","x-coordinate","y-coordinate"]]
    for float_var in ["time","progress","x-coordinate","y-coordinate"]:
        df[float_var] = df[float_var].astype("float")
    for int_var in ["episode","step"]:
        df[int_var] = df[int_var].astype("int")
    df.sort_values(by=["team","episode","step","time"], inplace=True)
    df = df.reset_index(drop=True)

    df_min_time = df[["team","episode","time"]].groupby(["team","episode"]).min()
    df_min_time = df_min_time.rename(columns={"time":"start_time"})
    df_max_time = df[["team","episode","time"]].groupby(["team","episode"]).max()
    df_max_time = df_max_time.rename(columns={"time":"end_time"})

    # Determine the end results of each episode, sort by best to worst performance (progress and steps)
    df_end_state = df[ df["state"] != "in_progress"  ]
    df_end_state = df_end_state[["team","episode","progress","state","step"]] 

    df_end_state = df_end_state.merge(df_min_time, on=["team","episode"])
    df_end_state = df_end_state.merge(df_max_time, on=["team","episode"])
    df_end_state["lap_time"] = df_end_state["end_time"] - df_end_state["start_time"] 
    df_end_state = df_end_state.sort_values(by=["team","progress","lap_time"], ascending=[True,False,True]).reset_index(drop=True)
    df_end_state["race_index"] = df_end_state.index + 1
    df_end_state = df_end_state.rename(columns={"progress": "lap_progress", 
                                            "state": "lap_end_state", "step": "lap_step_count"})
   
    # invert the race sequence so they run slowest to fastest
    df_end_state["race_number"] = df_end_state["race_index"]

    # Merge in the lap summary back to data
    df=df_end_state.merge(df, how="inner", on=["team","episode"])
    df["time"] = df["time"] - df["start_time"]
    df=df[["race_number","team","car_no","color","start_pos","lap_progress", 
           "lap_end_state", "lap_time", "lap_step_count","episode","step",
           "time","progress","state","x-coordinate","y-coordinate"]]
    
    return df

def process_team_log_file( team, new_style_log = False ):

    team_name = team["team"]
    log_file_name = path.join("cloudwatch_logs",team["logfile"])

    print(f"Processing {team_name} log file {log_file_name}")

    dr_trace = []

    if not new_style_log :
        with OpenRead(log_file_name ) as logfile:
            for msg in json.load(logfile)["events"]:
                if msg["message"].startswith("SIM_TRACE_LOG:"):
                    payload = parse_message(msg["message"])
                    payload["team"] = team_name
                    payload["car_no"] = str(int(team["car"])).zfill(2)
                    payload["color"] = team["color"]
                    payload["start_pos"] = team["start_pos"]
                    dr_trace.append(payload)
    else:
         with OpenRead(log_file_name ) as logfile:
            for line in logfile.readlines():
                if line.startswith("SIM_TRACE_LOG:"):
                    payload = parse_message(line.replace("\n",""))
                    #print(payload)
                    payload["team"] = team_name
                    payload["car_no"] = str(int(team["car"])).zfill(2)
                    payload["color"] = team["color"]
                    payload["start_pos"] = team["start_pos"]
                    dr_trace.append(payload)       

    return dr_trace   

def process_teams( yaml_file = "log_file_map.yaml", use_new_log_mode = True ):

    with open(yaml_file,"r") as yfp:
        file_to_team_map = yaml.load(yfp, Loader=yaml.FullLoader)
       
    full_data_set = None
    starting_pos = 0

    for team in file_to_team_map:
        team["start_pos"] = starting_pos
        starting_pos += 1
        raw_log_data = process_team_log_file( team, use_new_log_mode )
        team_data = evaluate_and_sort(raw_log_data)

        if full_data_set is None:
            full_data_set = team_data
        else:
            full_data_set = pd.concat([full_data_set,team_data])

    full_data_set.sort_values(by=["race_number","team","step"], inplace=True)

    # Individual Lap Races
    generate_races(full_data_set)
    generate_leaderboards(full_data_set)
    full_data_set.to_csv("race_data_out.csv", index=False)

    # 3 Lap Races
    data_set_3lap = full_data_set[ full_data_set.race_number <=3 ]
    generate_3_lap_race(data_set_3lap)
    generate_leaderboard_3lap(data_set_3lap)


def generate_leaderboards( race_data ):

    summary = race_data[["race_number","team","car_no","lap_end_state","lap_progress","lap_time"]].copy().drop_duplicates()
    race_list = summary.race_number.unique()
    for race_no in race_list:
        print(f"Generate Race Result {race_no}")
        one_race_lb = summary[summary.race_number == race_no].copy()
        one_race_lb.sort_values(by=["lap_progress","lap_time"], ascending=[False,True], inplace=True)
        one_race_lb= one_race_lb.reset_index(drop=True)
        one_race_lb.index = one_race_lb.index + 1
        one_race_lb.index.name = "Place"
        
        prior_time = 0.0
        one_race_lb["Delta"] = 0.0
        for index_label, row_series in one_race_lb.iterrows():
            # For each row update the 'Bonus' value to it's double
            if one_race_lb.at[index_label , 'lap_end_state'] == 'lap_complete' and prior_time is not 0.0:
                one_race_lb.at[index_label , 'Delta'] = row_series['lap_time'] -  prior_time
            else:
                one_race_lb.at[index_label , 'Delta'] = np.NaN
            prior_time = row_series['lap_time'] 

        one_race_lb.to_csv(path.join("race_data_single_laps",f'race_{race_no}_results.csv'))


def generate_races( race_data ):

    race_list = race_data.race_number.unique()
    
    for race_no in race_list:
        print(f"Generate Race Data {race_no}")
        one_race_data = race_data[race_data.race_number == race_no]
        race_teams = one_race_data.team.unique()
        race_json = []
        for team in race_teams:
            one_race_team_data = one_race_data[one_race_data.team == team].reset_index(drop=True)
            race_data_path = path.join("race_data_single_laps","coord_plots",f"race {race_no}".replace(" ","_").lower())
            race_data_file = f"{team}.csv".replace(" ","_").lower()
            race_team_json = { "team": team,
                               "starting_position" : int(one_race_team_data.loc[0, 'start_pos']),
                               "car_no" : one_race_team_data.loc[0, 'car_no'],
                               "car_color" : hex(one_race_team_data.loc[0, 'color']),
                               "lap_end_state" : one_race_team_data.loc[0, 'lap_end_state'],
                               "lap_progress" : one_race_team_data.loc[0, 'lap_progress'],
                               "lap_time" : one_race_team_data.loc[0, 'lap_time'],
                               "plot_file" : f"{race_data_path}/{race_data_file}"
                             }
            race_json.append(race_team_json)
            makedirs(race_data_path, exist_ok=True)
            loc_data = one_race_team_data[['x-coordinate', 'y-coordinate']]
            loc_data = loc_data.rename(columns={"x-coordinate": "x", "y-coordinate": "y"})
            loc_data.to_csv(path.join(race_data_path,race_data_file), header=False, index=False)

        with open(path.join("race_data_single_laps",f'race_{race_no}_data.json'), 'w') as fp:
            json.dump(race_json, fp, sort_keys=False, indent=2)
            
def generate_3_lap_race( race_data ):
    print(f"Generate 3Lap Data")
    race_teams = race_data.team.unique()
    race_data_path = path.join("race_data_best_3laps","coord_plots")
    makedirs(race_data_path, exist_ok=True) 
    race_json = []
    for team in race_teams:
        race_data_file = f"{team}.csv".replace(" ","_").lower()   
        one_race_team_data = race_data[race_data.team == team]
        last_complete_lap = one_race_team_data[ one_race_team_data['lap_end_state'] == 'lap_complete']
        if last_complete_lap.count == 0 or last_complete_lap.empty:
           keep_lap = 1
           print("No laps completed.")
        else:
           keep_lap = min(last_complete_lap.race_number.max()+1,3)
        one_race_team_data = one_race_team_data[one_race_team_data.race_number <= keep_lap]    
        loc_data = one_race_team_data[['x-coordinate', 'y-coordinate','race_number','step']].reset_index(drop=True)
        loc_data = loc_data.rename(columns={"x-coordinate": "x", "y-coordinate": "y"})
        
        #Smooth the start-finish line pass
        curr_x = loc_data.loc[0, 'x']
        for i in range(10, len(loc_data)-1):
            if (loc_data.loc[i, 'race_number'] != loc_data.loc[i+1, 'race_number']):
              curr_x = loc_data.loc[i, 'x']
            elif ( loc_data.loc[i, 'step'] < 20 and curr_x > loc_data.loc[i, 'x'] ):
              loc_data.loc[i, 'x'] = curr_x


        loc_data = loc_data[['x', 'y']]
        loc_data.to_csv(path.join(race_data_path,race_data_file), header=False, index=False)
        one_race_team_data_lap = one_race_team_data[["team","start_pos","car_no",
                                                     "color","lap_end_state",
                                                     "lap_progress","lap_time"
                                                      ]].copy().drop_duplicates()
        
        race_team_json = { "team": team,
                               "starting_position" : int(one_race_team_data_lap.loc[0, 'start_pos']),
                               "car_no" : one_race_team_data_lap.loc[0, 'car_no'],
                               "car_color" : hex(one_race_team_data_lap.loc[0, 'color']),
                               "lap_end_state" : one_race_team_data_lap.lap_end_state.max(),
                               "lap_progress" : one_race_team_data_lap.lap_progress.sum() / 3.0,
                               "lap_time" : one_race_team_data_lap.lap_time.sum(),
                               "plot_file" : f"{race_data_path}/{race_data_file}"
                             }
        race_json.append(race_team_json)
        
    with open(path.join("race_data_best_3laps",f'race_data.json'), 'w') as fp:
        json.dump(race_json, fp, sort_keys=False, indent=2)


def generate_leaderboard_3lap( race_data ):
    print(f"Generate 3 Lap Summary")
    race_data_path = "race_data_best_3laps"
    makedirs(race_data_path, exist_ok=True) 

    all_teams = race_data[["team","car_no"]].copy().drop_duplicates()

    summary = race_data[race_data["lap_end_state"]=="lap_complete"]
    summary = summary[["race_number","team","car_no","lap_time"]].copy().drop_duplicates()

    lap1 = summary[summary.race_number == 1][["team","car_no","lap_time"]]
    lap1.rename(columns={"lap_time":"lap1_time"},inplace=True)
    lap2 = summary[summary.race_number == 2][["team","car_no","lap_time"]]
    lap2.rename(columns={"lap_time":"lap2_time"},inplace=True)
    lap3 = summary[summary.race_number == 3][["team","car_no","lap_time"]]
    lap3.rename(columns={"lap_time":"lap3_time"},inplace=True)    

    race = pd.merge(all_teams,lap1,on=["team","car_no"],how="outer")
    race = pd.merge(race,lap2,on=["team","car_no"],how="outer")
    race = pd.merge(race,lap3,on=["team","car_no"],how="outer")
    
    race["lap_total"] = race["lap1_time"]+race["lap2_time"]+race["lap3_time"]
    race["lap_average"] = race["lap_total"] / 3.0
    race["best2lap"] = race["lap1_time"]+race["lap2_time"]
    race.sort_values(by=["lap_average","best2lap","lap1_time"], inplace=True)
    race = race.reset_index(drop=True)
    race.index = race.index + 1
    race.index.name = "Place"
    race = race.drop(['best2lap'], axis=1)

    prior_time = 0.0
    race["delta"] = 0.0
    for index_label, row_series in race.iterrows():
        if race.at[index_label , 'lap_average'] != np.NaN and prior_time is not 0.0:
            race.at[index_label , 'delta'] = row_series['lap_average'] -  prior_time
        else:
            race.at[index_label , 'delta'] = np.NaN
        prior_time = row_series['lap_average'] 

    print(race)
    race.to_csv(path.join(race_data_path,f"3lap_results.csv"))


if __name__ == "__main__":

    
    parser = argparse.ArgumentParser(description='DeepRacer Log Collection and Race Data Generator')
    parser.add_argument('--legacy','-l', action="store_true", default=False,
                        help="Legacy Cloudwatch mode, use for directly exported CloudWatch Files")

    args = parser.parse_args()
    if args.legacy:
        print("Using Legacy CloudWatch export mode.")


    chdir( path.dirname(__file__))
    process_teams(  "log_file_map.yaml", not args.legacy )
