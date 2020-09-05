import datetime
import sys

import bpy

argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get all args after "--"

now = datetime.datetime.now().microsecond

bpy.ops.mesh.primitive_uv_sphere_add()
bpy.ops.object.shade_smooth()
bpy.data.scenes['Scene'].render.filepath = f'{argv[0]}/big-{argv[1]}-chonkus_{now}.png'
bpy.ops.render.render(write_still=True)
