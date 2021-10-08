import unittest
import sys
import json

sys.path.insert(0, "./code")

from code.app import lambda_handler, get_flood_risk  # noqa


class TestRainRisk(unittest.TestCase):
    def test_get_flood_risk_response(self):
        resp = json.loads(get_flood_risk("Kjærmarken 103, 6771 gredstedbro"))
        self.assertEqual(resp["rain_risk"]["factors"]["basement"]["risk"], "low")
        self.assertEqual(resp["rain_risk"]["factors"]["fastning"]["risk"], "low")
        self.assertEqual(resp["rain_risk"]["factors"]["hollowing"]["risk"], "low")
        self.assertEqual(resp["rain_risk"]["factors"]["conductivity"]["risk"], "low")
        self.assertEqual(resp["rain_risk"]["risk"], "low")
        self.assertEqual(resp["storm_flood"]["risk"], "low")


    def test_get_flood_risk_response_multiple(self):
        adds =  ["Rolfsvej 21, st. tv. 2000 Frederiksberg",
                 "Højby Alle 3, Højby, 5260 Odense S",
                 "Blåregnvænget 9, 2830 Virum",
                 "Tørslevvej 4, Gerlev, 3630 Jægerspris"]
        risks = [
                    ["high","high","low","high","medium","low"],
                    ["low","high","low","medium","medium","low"],
                    ["high","high","low","high","medium","low"],
                    ["high","medium","low","low","medium","low"]
                ]
        for i in range(0,len(adds)):
            resp = json.loads(get_flood_risk(adds[i]))
            self.assertEqual(resp["rain_risk"]["factors"]["basement"]["risk"], risks[i][0])
            self.assertEqual(resp["rain_risk"]["factors"]["fastning"]["risk"], risks[i][1])
            self.assertEqual(resp["rain_risk"]["factors"]["hollowing"]["risk"], risks[i][2])
            self.assertEqual(resp["rain_risk"]["factors"]["conductivity"]["risk"], risks[i][3])
            self.assertEqual(resp["rain_risk"]["risk"], risks[i][4])
            self.assertEqual(resp["storm_flood"]["risk"], risks[i][5])



    def test_handler_address(self):
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {"address": "Jarmers Pl. 2, 1551 København"},
        }

        resp = lambda_handler(event, "")
        self.assertEqual(resp["statusCode"], 200)
        data = json.loads(resp["body"])
        self.assertEqual(data["rain_risk"]["risk"], "medium")
        self.assertEqual(data["navn"], "Jarmers Plads 2, 1551 København V")
        self.assertEqual(data["isAppartment"], False)

    def test_handler_bbr_id(self):
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "unadr_bbrid": "40eb1f85-9c53-4581-e044-0003ba298018"
            },
        }
        resp = lambda_handler(event, "")
        self.assertEqual(resp["statusCode"], 200)
        data = json.loads(resp["body"])
        self.assertEqual(data["rain_risk"]["risk"], "low")
        self.assertEqual(data["navn"], "Kjærmarken 103, 6771 Gredstedbro")
        self.assertEqual(data["isAppartment"], False)
