import base64
from . import (
    FASTNING_LIMITS,
    FASTNING_MAPPING,
    FASTNING_LABELS,
    IMAGE_SIZE,
    bounding_box,
    get_satelite_img,
)

from io import BytesIO

import numpy as np
import requests
from PIL import Image


def get_fastning_img(coordinates, imageSize=IMAGE_SIZE):
    response = requests.request(
        "GET",
        "http://7.tilecache2-miljoegis.mim.dk/gwc/service/wms",
        params={
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetMap",
            "FORMAT": "image/png",
            "TRANSPARENT": "true",
            "LAYERS": "theme-klimatilp-raster-arealanvendelse",
            "WIDTH": str(imageSize),
            "HEIGHT": str(imageSize),
            "SRS": "EPSG:25832",
            "BBOX": bounding_box(coordinates, ESPG="25832"),
        },
    )
    img = Image.open(BytesIO(response.content))
    return img.convert("RGB")


def fastning_image_to_value(fastning_image):
    # Fastning is a grid, the image returned by the bounding_box is 11 tall and wide
    nr_fastning_blocks = 11
    (block_width, block_height) = [
        size // nr_fastning_blocks for size in fastning_image.size
    ]

    fastning_degrees = []
    for y in range(nr_fastning_blocks):
        for x in range(nr_fastning_blocks):
            color = np.array(
                fastning_image.getpixel(
                    (
                        x * block_width + block_width // 2,
                        y * block_height + block_height // 2,
                    )
                )
            )
            color_distance = abs(FASTNING_MAPPING - color)
            fastning_degrees.append(
                FASTNING_LABELS[color_distance.sum(axis=1).argmin()]
            )

    return np.round(np.array(fastning_degrees).mean(), 2)


def get_fastning_response(coordinates, sateliteImage=None):
    if sateliteImage is None:
        sateliteImage = get_satelite_img(coordinates)
    fastning_img = get_fastning_img(coordinates)
    fastning_value = fastning_image_to_value(fastning_img)
    risk = "high"
    if fastning_value < FASTNING_LIMITS["low"]:
        risk = "low"
    elif fastning_value < FASTNING_LIMITS["medium"]:
        risk = "medium"
    image_summary = Image.blend(sateliteImage, fastning_img, 0.40)
    image_buffer = BytesIO()
    image_summary.save(image_buffer, format="PNG")

    return {
        "value": fastning_value,
        "risk": risk,
        "image": base64.b64encode(image_buffer.getvalue()),
    }
