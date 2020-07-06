import json
import bpy
from bpy_extras.image_utils import load_image

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
curve_name = "racer_" + str(expected_eval) + "_curve"
print (curve_name)
filtered_by_eval = [x for x in rows if x[0] == expected_eval]

print(len(filtered_by_eval))
print(filtered_by_eval[0])

pre_race_coords = [2.0399124787587044, 0.9838196013153698]
pre_race_coords2 = [2.749912415761146, 0.9840310918882519]

new_coords_list = []
# append last place grid postion
new_coords_list.append([-1, float(filtered_by_eval[0][3])] )
for i in filtered_by_eval:
    x = float(i[2])
    y = float(i[3])
    new_coords_list.append([x , y])
# append final position
new_coords_list.append([30, 1])  
print(new_coords_list[0])

# make a new curve
crv = bpy.data.curves.new('crv', 'CURVE')
crv.dimensions = '2D'

# make a new spline in that curve
spline = crv.splines.new(type='NURBS')

# a spline point for each point
spline.points.add(len(filtered_by_eval) + 1) # extra points for pre and post race

# assign the point coordinates to the spline points
for p, new_co in zip(spline.points, new_coords_list):
    p.co = (new_co + [0] + [1.0]) # (add nurbs weight)

# make a new object with the curve
obj = bpy.data.objects.new(curve_name, crv)
bpy.context.scene.collection.objects.link(obj)

bpy.ops.wm.append(directory="D:\\deepRacer\\deepRacer-race-render\\deepracer-race-render\\race_car.blend\\Collection\\", link=False, filename="race_car")

objects = bpy.data.objects
a = objects['racer_6_curve']
b = objects['car_base']

bpy.ops.object.select_all(action='DESELECT') #deselect all object

bpy.data.objects['racer_6_curve'].select_set(True)
bpy.data.objects['car_base'].select_set(True)

bpy.context.view_layer.objects.active = a  
bpy.ops.object.parent_set(type="FOLLOW")

numberImage = load_image("D:\\deepRacer\\deepRacer-race-render\\deepracer-race-render\\Textures\\generated\\car_number-assets\\car_number_42.png")
bpy.data.materials['car_material'].node_tree.nodes['car_number'].image = numberImage


def srgb_to_linearrgb(c):
    if   c < 0:       return 0
    elif c < 0.04045: return c/12.92
    else:             return ((c+0.055)/1.055)**2.4

def hex_to_rgb(h,alpha=1):
    r = (h & 0xff0000) >> 16
    g = (h & 0x00ff00) >> 8
    b = (h & 0x0000ff)
    return tuple([srgb_to_linearrgb(c/0xff) for c in (r,g,b)] + [alpha])

bpy.data.materials["car_material"].node_tree.nodes["car_color"].outputs[0].default_value = hex_to_rgb(0x336600)
