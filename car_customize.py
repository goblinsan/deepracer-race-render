import bpy
from bpy_extras.image_utils import load_image


def srgb_to_linearrgb(c):
    if c < 0:
        return 0
    elif c < 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(h, alpha=1):
    r = (h & 0xff0000) >> 16
    g = (h & 0x00ff00) >> 8
    b = (h & 0x0000ff)
    return tuple([srgb_to_linearrgb(c / 0xff) for c in (r, g, b)] + [alpha])


def modifyCarAttributes(texture_path, iterString, car_number, car_color, team_name):
    # update number
    car_num_path = "/generated/car_number-assets/car_number_"
    numberImage = load_image(texture_path + car_num_path + str(car_number) + ".png")
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_number'].image = numberImage
    bpy.data.materials['banner_number' + iterString].node_tree.nodes['banner_number_img'].image = numberImage
    # update color
    rgb_color = hex_to_rgb(int(car_color, 16))
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_color'].outputs[0].default_value = rgb_color
    bpy.data.materials['banner_color' + iterString].node_tree.nodes['banner_bg_color'].outputs[0].default_value = rgb_color
    # update banner text
    bpy.data.objects['team_name' + iterString].data.body = team_name
    bpy.data.objects['team_name_depth' + iterString].data.body = team_name
    # bpy.data.objects['explode_sprite_shadow' + iterString].constraints["Locked Track"].target = bpy.data.objects["track-sun"]
    bpy.data.objects['explode_sprite_color' + iterString].constraints["Locked Track"].target = bpy.data.objects["zz_free_cam"]
    bpy.data.objects['banner_bg' + iterString].constraints["Locked Track"].target = bpy.data.objects["zz_free_cam"]
    bpy.data.objects['banner_bg_white' + iterString].constraints["Locked Track"].target = bpy.data.objects["zz_free_cam"]
    bpy.data.objects['banner_number' + iterString].constraints["Locked Track"].target = bpy.data.objects["zz_free_cam"]
    bpy.data.objects['team_name' + iterString].constraints["Locked Track"].target = bpy.data.objects["zz_free_cam"]
    # bpy.data.objects['team_name_depth' + iterString].constraints["Locked Track"].target = bpy.data.objects["zz_free_cam"]

