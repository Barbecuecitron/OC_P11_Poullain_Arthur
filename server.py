import json
from flask import Flask,render_template,request,redirect,flash,url_for
import os
from datetime import datetime


base_dir = f"{os.path.dirname(os.path.abspath(__file__))}/"

def loadClubs(file_path=f"{base_dir}clubs.json"):
    with open(file_path) as c:
         listOfClubs = json.load(c)['clubs']
         return listOfClubs

# load from json and add Reservations dict if doesn't exist
def loadCompetitions(file_path=f"{base_dir}competitions.json"):
    with open(file_path) as comps:
        listOfCompetitions = json.load(comps)['competitions']
        for comp in listOfCompetitions:
            if not "Reservations" in comp:
                comp['Reservations'] = {} 
        return listOfCompetitions


def serializeClub(club_to_save, filename="clubs.json"):
    with open(filename, 'r+') as f:
        data = json.load(f)
        clubs = data['clubs']
        for club in clubs:
            if club['email'] == club_to_save['email']:    
                club['points'] = str(club_to_save['points'])
        f.seek(0)        # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()# remove remaining part


def serializeCompetition(comp_to_save):
    with open('competitions.json', 'r+') as f:
        data = json.load(f)
        comps = data["competitions"]
        for comp in comps:
            if comp['name'] == comp_to_save['name']:    
                comp['numberOfPlaces'] = str(comp_to_save['numberOfPlaces'])
                comp['Reservations'] = comp_to_save['Reservations']
        f.seek(0)        # <--- should reset file position to the beginning.
        json.dump(data, f, indent=4)
        f.truncate()# remove remaining part


def hasHappened(competition):
    compet_date = competition['date'].split(" ")[0] # get rid of time data
    year, month, day = compet_date.split("-")
    if datetime(int(year),int(month),int(day)) < datetime.now():
        return True

app = Flask(__name__)
app.secret_key = 'something_special'

competitions = loadCompetitions()
clubs = loadClubs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/showSummary',methods=['POST'])
def showSummary():
    try:
        club = [club for club in clubs if club['email']
            == request.form['email']][0]
    except IndexError:
        flash("This user doesn't exist !")
        return redirect(url_for('index'))
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition,club):
    foundClub = [c for c in clubs if c['name'] == club][0]
    foundCompetition = [c for c in competitions if c['name'] == competition][0]
    if foundClub and foundCompetition:
        return render_template('booking.html',club=foundClub, competition=foundCompetition)
    else:
        flash("Something went wrong-please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces',methods=['POST'])
def purchasePlaces():
    points_per_place = 3
    competition = [c for c in competitions if c['name'] == request.form['competition']][0]
    club = [c for c in clubs if c['name'] == request.form['club']][0]
    placesRequired = int(request.form['places'])

     # Can't buy 0 or negative n° of places
    if placesRequired < 1:
        flash("The number of purchased places must be positive")
        return render_template('welcome.html', club=club, competitions=competitions)

    # Club doesn't have enough points 
    if int(club['points']) == 0 or int(club['points']) - placesRequired*points_per_place < 0:
        flash("Your club doesn't have enough points !")
        return render_template('welcome.html', club=club, competitions=competitions)

     # Not enough places in the competition
    if int(competition['numberOfPlaces']) - placesRequired*points_per_place < 0:
        flash("There are not enough places in this competition !")
        return render_template('welcome.html', club=club, competitions=competitions)

    if hasHappened(competition):
        flash("This competition already happened !")
        return render_template('welcome.html', club=club, competitions=competitions)

    # Do we have bookings for this comp yet ? Let's find out
    try:
        # Limit buyings to 12 per club
        if competition["Reservations"][club["name"]] + placesRequired*points_per_place <= 12:
            competition["Reservations"][club["name"]] += placesRequired
        else:
            flash("You can't book more than 12 places per competition")
            return render_template('welcome.html', club=club, competitions=competitions)

    # Club doesn't have any bookings in this competition yet
    except KeyError:
        if placesRequired <= 12:
            competition['Reservations'][club['name']] = placesRequired
        

     # Update club points
    club['points'] = int(club['points']) - placesRequired*points_per_place
    serializeClub(club)

    # Update competition points
    competition['numberOfPlaces'] = int(
        competition['numberOfPlaces']) - placesRequired
    serializeCompetition(competition)

    flash(f"Great-booking complete! You purchased {placesRequired*points_per_place} places for the {competition['name']} !")
    return render_template('welcome.html', club=club, competitions=competitions)

# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


@app.route('/points_display')
def points_display():
    headings = ("Club Name - ", "Points")
    data = []
    for club in loadClubs():
        club_data = (club['name'], club['points'])
        data.append(club_data)

    return render_template('points_display.html', headings=headings, data=data)