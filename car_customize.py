import bpy
from bpy_extras.image_utils import load_image
from color_functions import hex_to_rgb, get_color_and_contrast


def modifyCarAttributes(texture_path, iterString, car_number, car_color, team_name):
    # update number
    car_num_path = "/generated/car_number-assets/car_number_"
    numberImage = load_image(texture_path + car_num_path + str(car_number) + ".png")
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_number'].image = numberImage
    bpy.data.materials['banner_number' + iterString].node_tree.nodes['banner_number_img'].image = numberImage
    # update color
    color, contrast = get_color_and_contrast(int(car_color, 16))
    bpy.data.materials['car_material' + iterString].node_tree.nodes['car_color'].outputs[0].default_value = color
    bpy.data.materials['banner_color' + iterString].node_tree.nodes['banner_bg_color'].outputs[0].default_value = color
    bpy.data.materials['text_white' + iterString].node_tree.nodes['text_color'].inputs[0].default_value = contrast
    # update banner text
    bpy.data.objects['team_name' + iterString].data.body = team_name
    # bpy.data.objects['city_name' + iterString].data.body = team_city
    bpy.data.objects['team_name_depth' + iterString].data.body = team_name
    # set camera constraints for starting grid intro shot
    # bpy.data.objects['explode_sprite_color' + iterString].constraints["Locked Track"].target = bpy.data.objects["start_grid"]
    # bpy.data.objects['banner_bg' + iterString].constraints["Locked Track"].target = bpy.data.objects["start_grid"]
    # bpy.data.objects['banner_bg_white' + iterString].constraints["Locked Track"].target = bpy.data.objects["start_grid"]
    # bpy.data.objects['banner_number' + iterString].constraints["Locked Track"].target = bpy.data.objects["start_grid"]
    # bpy.data.objects['team_name' + iterString].constraints["Locked Track"].target = bpy.data.objects["start_grid"]
    # bpy.data.objects['city_name' + iterString].constraints["Locked Track"].target = bpy.data.objects["start_grid"]

