# from typing import List
from _pytest.monkeypatch import MonkeyPatch
import unittest
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from unittest.mock import Mock, patch
# from server import loadClubs
# import requests
from server import app, loadClubs, loadCompetitions


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


def patch_serialize_clubs(club_to_serialize):
    return club_to_serialize

def patch_serialize_competitions(competitions_to_serialize):
    return competitions_to_serialize

loadClubs = Mock(return_value = simulated_json_clubs())
loadCompetitions = Mock(return_value = simulated_json_comps())

class TestFlaskApi(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch('server.clubs', simulated_json_clubs())
    @patch('server.competitions', simulated_json_comps())
    @patch('server.serializeClub', patch_serialize_clubs)
    @patch('server.serializeCompetition', patch_serialize_competitions)

    def test_from_login_to_booking(self):
        clubs = loadClubs()
        competitions = loadCompetitions()
        our_club = clubs[0]
        competition_to_book = competitions[0]
        # Go to the login page
        response = self.app.get('/')
        self.assertIn(b"Welcome to the GUDLFT Registration Portal", response.data)
        
        # Log our user
        login_response = app.test_client().post("/showSummary", data = {"email":our_club['email']}, follow_redirects =True)
        self.assertEqual(login_response.status_code, 200)
        url_name = f"/book/{competition_to_book['name']}/{our_club['name']}"

        # Get request to acces the book page
        book_get = app.test_client().get(url_name, follow_redirects =True)
        self.assertEqual(book_get.status_code, 200)
        self.assertIn(b"How many places?", book_get.data)

        # Simulate the form filling of book 
        purchase_places = app.test_client().post("/purchasePlaces", data={"club": our_club['name'], "competition": competition_to_book['name'],
                                            "places" : 1, })
        self.assertEqual(200, purchase_places.status_code)
        self.assertIn(b"Great-booking complete",purchase_places.data)

        # Log out
        logout_req = app.test_client().get("/logout", follow_redirects = True)
        self.assertEqual(logout_req.status_code, 200 )
        self.assertIn(b"Welcome to the GUDLFT Registration Portal !", logout_req.data)

if __name__ == "__main__":
    unittest.main()