import json

with open("D:/deepRacer/eval_logs.json") as f:
  fileData = json.load(f)
  
rows = []
for i in fileData['events']:
    noKey = i['message'].replace("SIM_TRACE_LOG:", "")
    row = noKey.split(",")
    row[0] = int(row[0])
    row[1] = int(row[1])
    row[2] = row[2]
    row[3] = row[3]
    rows.append(row)

expected_eval = 6
filtered_by_eval = [x for x in rows if x[0] == expected_eval]

f_csv = open("D:/deepRacer/deepRacer-race-render/deepracer-race-render/data_prep/race_data/coord_plots/sample_race/car_" + str(expected_eval) + ".csv", "a")

for i in filtered_by_eval:
    coords = i[2] + ", " + i[3] + "\n"
    f_csv.write(coords)

f_csv.close()
