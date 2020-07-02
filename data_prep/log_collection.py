import yaml
import json
import pandas as pd

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
    df = df[["team","episode","step","time","progress","state","x-coordinate","y-coordinate"]]
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

    # Determine the end results of each episode, sort by worst to best performance (progress and steps)
    df_end_state = df[ df["state"] != "in_progress"  ]
    df_end_state = df_end_state[["team","episode","progress","state","step"]] 

    df_end_state = df_end_state.merge(df_min_time, on=["team","episode"])
    df_end_state = df_end_state.merge(df_max_time, on=["team","episode"])
    df_end_state["lap_time"] = df_end_state["end_time"] - df_end_state["start_time"] 
    df_end_state = df_end_state.sort_values(by=["team","progress","lap_time"], ascending=[True,True,False]).reset_index(drop=True)
    df_end_state["race_number"] = df_end_state.index
    df_end_state = df_end_state.rename(columns={"progress": "lap_progress", 
                                            "state": "lap_end_state", "step": "lap_step_count"})
   

    # Merge in the lap summary back to data
    df=df_end_state.merge(df, how="inner", on=["team","episode"])
    df["time"] = df["time"] - df["start_time"]
    df=df[["race_number","team","lap_progress", "lap_end_state", "lap_time", "lap_step_count",
           "episode","step","time","progress","state","x-coordinate","y-coordinate"]]
    
    return df

def process_team_log_file( team_name, log_file_name):
    print(f"Processing {team_name} log file {log_file_name}")

    dr_trace = []
    with open(log_file_name,"r" ) as logfile:
        for msg in json.load(logfile)["events"]:
            if msg["message"].startswith("SIM_TRACE_LOG:"):
                payload = parse_message(msg["message"])
                payload["team"] = team_name
                dr_trace.append(payload)

    return dr_trace   

def process_teams( yaml_file = "log_file_map.yml"):

    with open(yaml_file,"r") as yfp:
        file_to_team_map = yaml.load(yfp, Loader=yaml.FullLoader)
       
    full_data_set = None

    for team in file_to_team_map:
        raw_log_data = process_team_log_file( team["team"], team["logfile"])
        team_data = evaluate_and_sort(raw_log_data)

        if full_data_set is None:
            full_data_set = team_data
        else:
            full_data_set = pd.concat([full_data_set,team_data])

    full_data_set.sort_values(by=["race_number","team","step"], inplace=True)
    full_data_set.to_csv("race_data_out.csv", index=False)


if __name__ == "__main__":
    process_teams()
