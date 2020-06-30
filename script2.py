import json
import bpy

#aws logs filter-log-events --log-group-name /aws/deepracer/leaderboard/SimulationJobs --log-stream-name-prefix sim-mz0nm166n95y --start-time 1593459542045 --end-time 1593459695202 --filter-pattern "SIM_TRACE_LOG" --start-from-head true
with open("D:/deepRacer/eval_logs.json") as f:
  fileData = json.load(f)
  
rows = []
for i in fileData['events']:
    noKey = i['message'].replace("SIM_TRACE_LOG:", "")
    row = noKey.split(",")
    row[0] = int(row[0])
    row[1] = int(row[1])
    row[2] = float(row[2])
    row[3] = float(row[3])
    rows.append(row)
      
print(len(rows))
print(rows[7])

expected_eval = 6
filtered_by_eval = [x for x in rows if x[0] == expected_eval]

print(len(filtered_by_eval))
print(filtered_by_eval[0])



new_coords_list = []
for i in filtered_by_eval:
    x = float(i[2])
    y = float(i[3])
    new_coords_list.append([x , y])
print(new_coords_list[0])

# make a new curve
crv = bpy.data.curves.new('crv', 'CURVE')
crv.dimensions = '3D'

# make a new spline in that curve
spline = crv.splines.new(type='NURBS')

# a spline point for each point
spline.points.add(len(filtered_by_eval)-1) # theres already one point by default

# assign the point coordinates to the spline points
for p, new_co in zip(spline.points, new_coords_list):
    p.co = (new_co + [0] + [1.0]) # (add nurbs weight)

# make a new object with the curve
obj = bpy.data.objects.new('object_name', crv)
bpy.context.scene.collection.objects.link(obj)