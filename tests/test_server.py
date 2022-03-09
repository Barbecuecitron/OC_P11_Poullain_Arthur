# from typing import List
from _pytest.monkeypatch import MonkeyPatch
import unittest
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
from bs4 import BeautifulSoup
sys.path.append(parentdir)
# from server import loadClubs
from server import app, loadClubs, loadCompetitions, hasHappened, datetime, json
from flask import Flask, render_template
from unittest.mock import Mock, patch


# Simulates Json clubs, returns a dict with clubs as key
def simulated_json_clubs():
    json_clubs = { 
        "clubs":[
            {
            "name":"Valid Club",
            "email": "SuperValidClub@gmail.co",
            "points": "25"
            },
            {
            "name":"another_valid_club",
            "email": "another_valid_club@gmail.com",
            "points":"12"
            },
            {
            "name":"club_with_0_points",
            "email": "club_with_0_points@gmail.com",
            "points":"0"
            },
                        {
            "name":"club_with_a_lot_of_bookings",
            "email": "club_with_a_lot_of_bookings@gmail.com",
            "points":"25"
            },
        ]
    }
    return json_clubs['clubs']

def simulated_json_comps():
    json_comps = { 
        "competitions": [
            {
                "name": "Spring Festival",
                "date": "2023-03-27 10:00:00",
                "numberOfPlaces": "25"
            },
            {
                "name": "Fall Classic",
                "date": "2023-10-22 13:30:00",
                "numberOfPlaces": "13"
            },
            {
                "name": "Competition with bookings",
                "date": "2023-10-22 13:30:00",
                "numberOfPlaces": "25",
                "Reservations": {'club_with_a_lot_of_bookings': 2}
            },
            {
                "name": "Competition with too much bookings",
                "date": "2023-10-22 13:30:00",
                "numberOfPlaces": "50",
                "Reservations": {'club_with_a_lot_of_bookings': 11}
            },
            {
                "name": "Competition from last year",
                "date": "2021-10-22 13:30:00",
                "numberOfPlaces": "25",
                "Reservations": {'club_with_a_lot_of_bookings': 11}
            },
        ]
    }
    for comp in json_comps['competitions']:
        if "Reservations" in comp:
            pass
        else:
            comp['Reservations'] = {} 
    return json_comps['competitions']


# class TestSerializers(unittest.TestCase):
loadClubs = Mock(return_value = simulated_json_clubs())
loadCompetitions = Mock(return_value = simulated_json_comps())

def patch_serialize_clubs(club_to_serialize):
    return club_to_serialize

def patch_serialize_competitions(competitions_to_serialize):
    return competitions_to_serialize
# Verify points are deducted from clubs 
class TestServer(unittest.TestCase):
    # Deserializes from our test_clubs.json
    def test_loadClubs(self):
        listOfClubs = loadClubs(f"{currentdir}\\test_clubs.json")
        self.assertIsInstance(listOfClubs, list)
        self.assertIsInstance(listOfClubs[0], dict)
        self.assertEqual(listOfClubs[0]['name'], "Valid Club" )
        self.assertEqual(listOfClubs[0]['email'], "SuperValidClub@gmail.co" )

        self.assertEqual(listOfClubs[1]['name'], "another_valid_club" )
        self.assertEqual(listOfClubs[1]['email'], "another_valid_club@gmail.com" )

    # Deserialize from our test_competitions.json file
    def test_loadCompetitions(self):
        listOfComps = loadCompetitions(f"{currentdir}\\test_competitions.json")
        self.assertIsInstance(listOfComps, list)
        self.assertIsInstance(listOfComps[0], dict)
        self.assertEqual(listOfComps[0]['name'], "Spring Festival" )
        self.assertEqual(listOfComps[0]["date"], "2023-03-27 10:00:00",)
        self.assertEqual(listOfComps[0]["numberOfPlaces"],"25") 

    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    @patch('server.serializeClub', patch_serialize_clubs)
    @patch('server.serializeCompetition', patch_serialize_competitions)

    def test_purchasePlaces_successful(self):
        req_example_club = simulated_json_clubs()[0]
        req_example_comp = simulated_json_comps()[0]
        num_places_to_purchase = 1
        
        response = app.test_client().post("/purchasePlaces", data={"club": req_example_club['name'], "competition": req_example_comp['name'],
                                            "places" : num_places_to_purchase, })
        self.assertEqual(200, response.status_code)
        self.assertIn(b"Great-booking complete",response.data)
        # Check points have been redeemed properly 
        points_per_place = 3
        string = int(req_example_club['points']) - num_places_to_purchase*points_per_place
        string = bytes(f"Points available: {string}", encoding= 'utf-8')
        self.assertIn(string, response.data)


    # We try to buy negative ammount, redirection to the same page with an error message,
    # no mods in clubs['points'] or competition['numberOfPlaces'] should occur
    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    def test_purchasePlaces_fail_due_to_negative_ammount(self):
        req_example_club = simulated_json_clubs()[0]
        req_example_comp = simulated_json_comps()[0]
        num_places_to_purchase = -1 

        response = app.test_client().post("/purchasePlaces", data={"club": req_example_club['name'], "competition": req_example_comp['name'],
                                            "places" : num_places_to_purchase, })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"The number of purchased places must be positive", response.data)
        
    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    def test_purchasePlaces_fail_due_to_not_enough_club_points(self):
        req_example_club = simulated_json_clubs()[2]
        req_example_comp = simulated_json_comps()[0]
        num_places_to_purchase = 1 

        response = app.test_client().post("/purchasePlaces", data={"club": req_example_club['name'], "competition": req_example_comp['name'],
                                            "places" : num_places_to_purchase, })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"have enough points", response.data)


    # Booking already exist for this competition & club combination, but they remain <= 12
    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    @patch('server.serializeClub', patch_serialize_clubs)
    @patch('server.serializeCompetition', patch_serialize_competitions)
    def test_purchasePlaces_success_with_pre_existing_bookings(self):
        req_example_club = simulated_json_clubs()[3]
        req_example_comp = simulated_json_comps()[2]
        num_places_to_purchase = 2 

        response = app.test_client().post("/purchasePlaces", data={"club": req_example_club['name'], "competition": req_example_comp['name'],
                                            "places" : num_places_to_purchase, })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Great-booking complete",response.data)

    # 11 Booking already exist, and we try to buy 5, so exceed 12 and fail:
    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    @patch('server.serializeClub', patch_serialize_clubs)
    @patch('server.serializeCompetition', patch_serialize_competitions)
    def test_purchasePlaces_fail_with_pre_existing_bookings(self):
        req_example_club = simulated_json_clubs()[3]
        req_example_comp = simulated_json_comps()[3]
        num_places_to_purchase = 5 

        response = app.test_client().post("/purchasePlaces", data={"club": req_example_club['name'], "competition": req_example_comp['name'],
                                            "places" : num_places_to_purchase, })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You can&#39;t book more than 12 places per competition",response.data)
    

    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    def test_fail_because_competition_has_happened(self):
        req_example_club = simulated_json_clubs()[3]
        req_example_comp = simulated_json_comps()[4]
        num_places_to_purchase = 5 

        response = app.test_client().post("/purchasePlaces", data={"club": req_example_club['name'], "competition": req_example_comp['name'],
                                            "places" : num_places_to_purchase, })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'This competition already happened !', response.data)
        
    @patch('server.competitions', simulated_json_comps())
    def test_hasHappened_past_competition(self):
        comp_from_last_year = simulated_json_comps()[4]
        self.assertTrue(hasHappened(comp_from_last_year))

    @patch('server.competitions', simulated_json_comps())
    def test_hasHappened_didnt_happen_yet(self):
        comp_from_next_year = simulated_json_comps()[0]
        self.assertFalse(hasHappened(comp_from_next_year))


    
    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    def test_points_display(self):
        response = app.test_client().get("/points_display")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'She Lifts', response.data)
    
        
    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    def test_showSummary_success(self):
        req_example_club = simulated_json_clubs()[0]
        response = app.test_client().post("/showSummary", data = {"email":req_example_club['email']})
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Points available', response.data)

    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    # Club provided is invalid, we are redirected to the same page without loggin in
    def test_showSummary_failed_because_of_invalid_club(self):
        # req_example_club = simulated_json_clubs()[0]
        response = app.test_client().post("/showSummary", data = {"email":"i_dont_exist_in_db@gmail.com"})
        self.assertEqual(response.status_code, 302)
        self.assertIn(b"Redirecting", response.data)


if __name__ == '__main__':
    unittest.main()
