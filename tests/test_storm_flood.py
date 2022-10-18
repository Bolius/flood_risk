import unittest
from code.lib import (
    address_to_house_data,
    get_storm_flod_response,
    get_storm_flood_img,
)
from os import path

from PIL import Image


class TestStormFlood(unittest.TestCase):
    def test_get_flood_img(self):
        blox_coordinates = address_to_house_data("Bryghusgade, 1473 København")[
            "coordinates"
        ]
        actual_image = get_storm_flood_img(blox_coordinates)

        expected_image = Image.open(
            path.join("tests", "test_images", "blox_storm_flood.png")
        )

        self.assertEqual(actual_image, expected_image)

    def test_get_storm_flod_response(self):
        blox_coordinates = address_to_house_data(
            "Vester Voldgade 129, 1552 København V"
        )["coordinates"]
        blox_risk = get_storm_flod_response(blox_coordinates)["risk"]
        self.assertEqual(blox_risk, "medium")

        DIKU_coordinates = address_to_house_data(
            "Universitetsparken 1, 2100 København"
        )["coordinates"]
        DIKU_risk = get_storm_flod_response(DIKU_coordinates)["risk"]
        self.assertEqual(DIKU_risk, "low")


if __name__ == "__main__":
    unittest.main()
