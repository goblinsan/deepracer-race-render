import bpy


def setExplodeVisibilityKeyframes(sprite, start_frame):
    sprite.keyframe_insert('hide_render')
    sprite.hide_render = False
    sprite.keyframe_insert('hide_render', frame=start_frame)
    sprite.hide_render = True
    sprite.keyframe_insert('hide_render', frame=start_frame + 160)


def addExplosion(iterString, total_frames):
    explosion_frame = total_frames - 5

    bpy.data.particles['destroyCar' + iterString].frame_start = explosion_frame
    bpy.data.particles['destroyCar' + iterString].frame_end = total_frames
    bpy.data.particles['destroyCar' + iterString].lifetime = 5000

    objects = bpy.data.objects
    explode_color = objects['explode-sprite-color' + iterString]
    setExplodeVisibilityKeyframes(explode_color, explosion_frame)
    explode_shadow = objects['explode-sprite-shadow' + iterString]
    explode_shadow.constraints['Locked Track'].target = objects['track-sun']
    setExplodeVisibilityKeyframes(explode_shadow, explosion_frame)

    bpy.data.materials['explosion' + iterString].node_tree.nodes[
        'sprite-texture'].image_user.frame_start = explosion_frame
    bpy.data.materials['explosion_shadow' + iterString].node_tree.nodes[
        'sprite-texture'].image_user.frame_start = explosion_frame
