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
    return tuple([r, g, b, alpha])


def rgb_to_linearrgb(r, g, b, alpha=1):
    return tuple([srgb_to_linearrgb(c / 0xff) for c in (r, g, b)] + [alpha])


def contrast_color(rgb_color):
    black = 0x000
    white = 0xFFFFFF
    lin_rgb = tuple([srgb_to_linearrgb(c / 0xff) for c in (rgb_color[0], rgb_color[1], rgb_color[2])] + [rgb_color[3]])
    luminosity = (0.2126 * lin_rgb[0]) + (0.7152 * lin_rgb[1]) + (0.0722 * lin_rgb[2])

    contrast = black if luminosity > .5 else white

    return rgb_to_linearrgb(*hex_to_rgb(contrast))


def get_color_and_contrast(hex_color):
    color = rgb_to_linearrgb(*hex_to_rgb(hex_color))
    contrast = contrast_color(hex_to_rgb(hex_color))

    return color, contrast


