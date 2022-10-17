from io import BytesIO

import numpy as np
import requests
from PIL import Image

from .config import CONDUCTIVITY_LIMITS, CONDUCTIVITY_MAPPING, CONDUCTIVITY_LABELS
from .data_retrieval import bounding_box


def get_conductivity_img(coordinates, imageSize=11):
    response = requests.request(
        "GET",
        "http://7.tilecache2-miljoegis.mim.dk/gwc/service/wms",
        params={
            "SERVICE": "WMS",
            "VERSION": "1.1.1",
            "REQUEST": "GetMap",
            "FORMAT": "image/png",
            "LAYERS": "theme-klimatilp-raster-hydrauliskledningsevne25",
            "WIDTH": str(imageSize),
            "HEIGHT": str(imageSize),
            "SRS": "EPSG:25832",
            "BBOX": bounding_box(coordinates, ESPG="25832"),
        },
    )
    img = Image.open(BytesIO(response.content))
    return img.convert("RGB")


def color_to_conductivity(color):
    color = np.array(color) if type(color) != "numpy.ndarray" else color
    color_channel_difs = abs(CONDUCTIVITY_MAPPING - color)
    color_distance = color_channel_difs.sum(axis=1)
    return int(CONDUCTIVITY_LABELS[color_distance.argmin()])


def get_conductivity_response(coordinates):
    img_color_counts = get_conductivity_img(coordinates).getcolors()
    img_color_counts.sort(key=lambda count_color: count_color[0], reverse=True)
    conductivity_value = color_to_conductivity(img_color_counts[0][1])
    risk = "low"
    if conductivity_value < CONDUCTIVITY_LIMITS["low"]:
        risk = "high"
    elif conductivity_value < CONDUCTIVITY_LIMITS["medium"]:
        risk = "medium"
    return {"value": conductivity_value, "risk": risk}
