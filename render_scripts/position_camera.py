def adjust_key_for_range(existing_frame, old_range, new_range):
    old_corrected_range = old_range[1] - old_range[0]
    new_corrected_range = new_range[1] - new_range[0]
    corrected_start_value = existing_frame - old_range[0]
    percentage = (corrected_start_value * 100) / old_corrected_range
    return (percentage * new_corrected_range / 100) + new_range[0]


def set_keyframe(cam, i, location_data, new_frame, rotation_data):
    x_l = location_data[0][i][1]
    y_l = location_data[1][i][1]
    z_l = location_data[2][i][1]
    cam.location = (x_l, y_l, z_l)
    cam.keyframe_insert('location', frame=new_frame)
    x_r = rotation_data[0][i][1]
    y_r = rotation_data[1][i][1]
    z_r = rotation_data[2][i][1]
    cam.rotation_euler = (x_r, y_r, z_r)
    cam.keyframe_insert('rotation_euler', frame=new_frame)


def setup_camera_frames(cam, key_ranges):
    # print(f"\nactions for camera {cam.name}")
    cam_action_data = cam.animation_data.action

    # grab channel data
    for g in cam_action_data.groups:
        # print(f'Getting channel data for: {g.name}')

        channel_data = {}
        channel_data['location'] = {}
        channel_data['rotation_euler'] = {}
        for channel in g.channels:
            old_keys = []

            for k in channel.keyframe_points:
                frame = k.co[0]
                old_keys.append((frame, channel.evaluate(frame)))

            channel_data[channel.data_path][channel.array_index] = old_keys
            cam_action_data.fcurves.remove(channel)

        location_data = channel_data['location']
        rotation_data = channel_data['rotation_euler']

        # create new keys for each lap (3 lap race)
        for key_range in key_ranges:
            set_keyframe(cam, 0, location_data, key_range[0], rotation_data)

            if len(location_data[0]) > 2:
                old_min = location_data[0][0][0]
                old_max = location_data[0][-1][0]
                for i in range(1, len(location_data[0])):
                    new_frame = adjust_key_for_range(location_data[0][i][0], [old_min, old_max], key_range)
                    set_keyframe(cam, i, location_data, new_frame, rotation_data)

            set_keyframe(cam, -1, location_data, key_range[1], rotation_data)
