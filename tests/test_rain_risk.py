import unittest
from code.lib import address_to_house_data, get_rain_risk_response


class TestRainRisk(unittest.TestCase):
    def test_get_rain_risk_response_1(self):
        data = address_to_house_data("Kjærmarken 103, 6771 gredstedbro")
        resp = get_rain_risk_response(data["id"], data["coordinates"])
        self.assertEqual(resp["factors"]["basement"]["risk"], "low")
        self.assertEqual(resp["factors"]["fastning"]["risk"], "low")
        self.assertEqual(resp["factors"]["hollowing"]["risk"], "low")
        self.assertEqual(resp["factors"]["conductivity"]["risk"], "low")
        self.assertEqual(resp["risk"], "low")

    def test_get_rain_risk_response_2(self):
        data = address_to_house_data("Dronning Dagmars Vej 13, 6760 Ribe")
        resp = get_rain_risk_response(data["id"], data["coordinates"])
        self.assertEqual(resp["factors"]["basement"]["risk"], "high")
        self.assertEqual(resp["factors"]["fastning"]["risk"], "medium")
        self.assertEqual(resp["factors"]["hollowing"]["risk"], "high")
        self.assertEqual(resp["factors"]["conductivity"]["risk"], "low")
        self.assertEqual(resp["risk"], "high")
