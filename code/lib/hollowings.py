import asyncio
import base64
import os
from io import BytesIO

import numpy as np
import requests
from PIL import Image
import skimage

from .config import HOLLOWING_COLOR, HOUSE_COLOR, IMAGE_SIZE, OVERLAP_COLOR
from .data_retrieval import bounding_box, get_satelite_img
from .image_handling import greyscale_to_binary_image, isolate_building


def get_hollowing_img(coordinates, feature, imageSize=IMAGE_SIZE):
    params = {
        "request": "GetMap",
        "service": "WMS",
        "token": os.environ["DATAFORSYNINGEN"],
        "TRANSPARENT": "True",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "FORMAT": "image/png",
        "SRS": "EPSG:3857",
        "BBOX": bounding_box(coordinates, ESPG="3857"),
        "WIDTH": str(imageSize),
        "HEIGHT": str(imageSize),
    }
    if feature == "buildings":
        params["LAYERS"] = "BU.Building"
        params["servicename"] = "building_inspire"

    elif feature == "hollowings":
        params["servicename"] = ("dhm",)
        params["LAYERS"] = "dhm_bluespot_ekstremregn"
        params["STYLES"] = "bluespot_ekstremregn_0_015"
    else:
        raise ValueError("Invalid feature")
    response = requests.request(
        "GET", "https://api.dataforsyningen.dk/service?", params=params
    )
    img = Image.open(BytesIO(response.content))
    return img.convert("L")


async def get_hollowing_img_async(*args, **kwargs):
    return get_hollowing_img(*args, **kwargs)


async def get_images_async(coordinates):
    return asyncio.gather(
        get_hollowing_img_async(coordinates, "buildings"),
        get_hollowing_img_async(coordinates, "hollowings"),
    )


def coordinates_to_holllowing_images(coordinates):
    return [
        get_hollowing_img(coordinates, "buildings"),
        get_hollowing_img(coordinates, "hollowings"),
    ]


# Implemented to avoid using scipy. Should not increase runtime by that much.
def conv2d(src, k):
    d = int((k - 1) / 2)
    out = np.copy(src)
    for i in range(d, src.shape[0] - d):
        for j in range(d, src.shape[1] - d):
            if src[i, j]:
                for a in range(-d, d):
                    for b in range(-d, d):
                        out[i + a, j + b] = True
    return out


def house_percentage_hollowing(hollowingImg, buildingImg):
    hollowingImg = np.asarray(greyscale_to_binary_image(hollowingImg, thresshold=1))
    buildingImg = np.asarray(greyscale_to_binary_image(buildingImg, thresshold=1))

    labels = skimage.measure.label(buildingImg, connectivity=2, background=0)
    w = int(hollowingImg.shape[0] / 2)
    house_label = labels[w, w]

    house = np.ma.masked_not_equal(labels, house_label)
    house = np.logical_not(np.ma.getmaskarray(house))

    house_border = np.logical_xor(conv2d(house, 9), house)

    overlap = np.logical_and(house_border, conv2d(hollowingImg, 3))

    overlap_area = overlap.sum()
    house_area = house_border.sum()

    return overlap_area / house_area * 100


def generate_image_summary(mapImg, buildingImg, hollowingImg):
    (x, y) = mapImg.size
    overlay = np.ndarray(shape=(x, y, 4), dtype=np.uint8)
    hollowing_mask = np.asarray(greyscale_to_binary_image(hollowingImg, thresshold=10))
    building_mask = np.asarray(greyscale_to_binary_image(buildingImg, thresshold=10))
    overlap_mask = np.logical_and(hollowing_mask, building_mask)
    overlay[:, :] = [np.uint8(n) for n in [0, 0, 0, 0]]
    overlay[building_mask] = HOUSE_COLOR
    overlay[hollowing_mask] = HOLLOWING_COLOR
    overlay[overlap_mask] = OVERLAP_COLOR
    overlay_image = Image.fromarray(overlay, mode="RGBA")
    mapImg.paste(overlay_image, (0, 0), overlay_image)
    return mapImg


def get_hollowing_response(coordinates, sateliteImage=None):
    if sateliteImage is None:
        sateliteImage = get_satelite_img(coordinates)
    building, hollowing = coordinates_to_holllowing_images(coordinates)
    building = isolate_building(building)
    image_summary = generate_image_summary(sateliteImage, building, hollowing)

    final_image = BytesIO()
    image_summary.save(final_image, format="PNG")
    house_percentage = round(house_percentage_hollowing(hollowing, building), 2)
    hollowingMask = np.asarray(greyscale_to_binary_image(hollowing, thresshold=10))

    """ The method and thresshold for risk was determined by in house subject
        experts at Bolius
    """
    risk = "high" if house_percentage > 50 else "low"

    return {
        "house_percentage": house_percentage,
        "area_percentage": np.round(hollowingMask.sum() / hollowingMask.size * 100, 2),
        "image": base64.b64encode(final_image.getvalue()),
        "risk": risk,
    }
