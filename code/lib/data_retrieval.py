import os
from io import BytesIO

import requests
from PIL import Image
from pyproj import Transformer

import json

from .config import IMAGE_SIZE


def address_to_house_data(address):
    response = requests.request(
        "GET",
        "https://dawa.aws.dk/adresser",
        params={"q": address, "struktur": "mini", "fuzzy": ""},
    )
    if response.status_code != 200:
        raise ValueError(f"Invalid address: {address}")
    data = response.json()[0]
    return {
        "navn": data["betegnelse"],
        "id": data["adgangsadresseid"],
        "coordinates": (data["y"], data["x"]),
        "isAppartment": not data["etage"] is None,
    }


def bbr_id_to_house_data(bbr_id):
    response = requests.request(
        "GET",
        f"https://dawa.aws.dk/adresser/{bbr_id}",
        params={"struktur": "mini"},
    )
    if response.status_code != 200:
        raise ValueError(f"Invalid BBR_ID: {bbr_id}")
    data = response.json()
    return {
        "navn": data["betegnelse"],
        "id": data["adgangsadresseid"],
        "coordinates": (data["y"], data["x"]),
        "isAppartment": not data["etage"] is None,
    }


def get_basement_response(address_id):
    user, password = os.environ["DATAFORDELEREN"].split("@")

    response = requests.request(
        "GET",
        "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning?",
        params={
            "username": user,
            "password": password,
            "Format": "JSON",
            "husnummer": address_id,
        },
    )

    data = json.loads(response.content)

    basement_size = 0
    for b in data:
        if "etageList" in b:
            for c in b["etageList"]:
                if "eta022Kælderareal" in c["etage"]:
                    basement_size = c["etage"]["eta022Kælderareal"]
                if (
                    "eta025Etagetype" in c["etage"]
                    and c["etage"]["eta025Etagetype"] == "2"
                ):
                    basement_size = 1

    return {"risk": "high" if basement_size > 0 else "low"}


def bounding_box(coordinates, ESPG=None, boxSize=200):
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
    (x, y) = coordinates
    (x, y) = transformer.transform(x, y)
    minX = x - boxSize / 2
    minY = y - boxSize / 2
    maxX = x + boxSize / 2
    maxY = y + boxSize / 2
    if ESPG == "3857":
        return f"{minX},{minY},{maxX},{maxY}"
    elif ESPG == "25832":
        transformer = Transformer.from_crs("epsg:3857", f"epsg:{ESPG}")
        minX, minY = transformer.transform(minX, minY)
        maxX, maxY = transformer.transform(maxX, maxY)
        return f"{minX},{minY},{maxX},{maxY}"
    else:
        raise ValueError("NO or invalid ESPG specified")


def get_satelite_img(coordinates, imageSize=IMAGE_SIZE):
    user, password = os.environ["DATAFORDELEREN"].split("@")
    params = {
        "username": user,
        "password": password,
        "request": "GetMap",
        "CRS": "EPSG:3857",
        "SRS": "EPSG:3857",
        "styles": "default",
        "VERSION": "1.1.1",
        "FORMAT": "image/png",
        "LAYERS": "orto_foraar",
        "BBOX": bounding_box(coordinates, ESPG="3857"),
        "WIDTH": str(imageSize),
        "HEIGHT": str(imageSize),
    }
    response = requests.request(
        "GET",
        "https://services.datafordeler.dk/GeoDanmarkOrto/orto_foraar/1.0.0/WMS?",
        params=params,
    )
    img = Image.open(BytesIO(response.content))

    return img.convert("RGB")


async def get_satelite_img_async(*args, **kwargs):
    return get_satelite_img(*args, **kwargs)
