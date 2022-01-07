import requests
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from datetime import date, datetime, timedelta
from db_models import get_profile


def get_google_api_link():
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]

    flow = Flow.from_client_secrets_file(
        "client_secret.json", scopes=scopes, redirect_uri='urn:ietf:wg:oauth:2.0:oob')

    auth_url, _ = flow.authorization_url(prompt="consent")

    return auth_url


def get_google_api_credentials(code):
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    flow = Flow.from_client_secrets_file(
        "client_secret.json", scopes=scopes, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    flow.fetch_token(code=code)
    credentials = flow.credentials

    return credentials


def get_tomorrows_morning(credentials):
    tomorrow = date.today() + timedelta(days=1)

    start_time = datetime.strptime('01:00', '%H:%M').time()
    min_time = datetime.combine(
        tomorrow, start_time).strftime("%Y-%m-%dT%H:%M:%SZ")

    stop_time = datetime.strptime('23:00', '%H:%M').time()
    max_time = datetime.combine(
        tomorrow, stop_time).strftime("%Y-%m-%dT%H:%M:%SZ")

    service = build("calendar", "v3", credentials=credentials)

    result = service.calendarList().list().execute()

    schedule = None

    for i in result['items']:
        if i["summary"] == 'Schedule':
            schedule = i

    result = service.events().list(calendarId=schedule["id"], timeMin=min_time, timeMax=max_time,
                                   timeZone='Europe/Stockholm', maxResults=2, singleEvents=True,
                                   orderBy="startTime").execute()

    if result["items"]:
        if result["items"][0]["summary"] != 'PFL ':
            return datetime.strptime(result["items"][0]["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+02:00")
        else:
            return datetime.strptime(result["items"][1]["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+02:00")
    else:
        return -1


class KomitidProfil:
    def __init__(self, id, credentials, home, school, pre_trip_time):
        self.id = id
        self.credentials = credentials
        self.home = home
        self.school = school
        self.pre_trip_time = pre_trip_time

    def get_alarm(self):
        school_margin = 10

        tomorrows_morning = get_tomorrows_morning(self.credentials)

        if tomorrows_morning != -1:
            morning_time = datetime.strftime(tomorrows_morning - timedelta(minutes=school_margin),
                                             "%H:%M")

            trip = sl_get_trip(self.home, self.school, morning_time)[-1]

            depart_time = datetime.strptime(trip.depart_time, "%H:%M")

            alarm_time = (
                depart_time - timedelta(minutes=int(self.pre_trip_time))).strftime("%H:%M")

            return alarm_time, trip
        else:
            return "Ledig", -1


class Trip:
    def __init__(self, info):
        self.info = info
        self.depart_time = info["LegList"]["Leg"][0]["Origin"]["time"][:5]
        self.depart_place = info["LegList"]["Leg"][0]["Origin"]["name"]
        self.arrive_time = info["LegList"]["Leg"][-1]["Destination"]["time"][:5]
        self.arrive_place = info["LegList"]["Leg"][-1]["Destination"]["name"]
        self.travel_time = self.calc_travel_time()
        self.leg_info = self.get_leg_info()

    def __getitem__(self, item):
        return item[-1]

    def calc_travel_time(self):
        start = datetime.strptime(self.depart_time, "%H:%M")
        stop = datetime.strptime(self.arrive_time, "%H:%M")

        return ((stop - start).seconds//60) % 60

    def get_leg_info(self):
        final = []
        for i in self.info["LegList"]["Leg"]:
            if i["type"] != "WALK":
                line_class = i["Product"]["name"].replace(
                    'tunnelbanans ', '').replace(' linje', 'linje').split(' ')
                final.append({
                    "o_name": i["Origin"]["name"],
                    "o_time": i["Origin"]["time"][:5],
                    "d_name": i["Destination"]["name"],
                    "d_time": i["Destination"]["time"][:5],
                    "line": line_class[1],
                    "class": line_class[0]
                })
            elif "hide" not in i:
                final.append({
                    "o_name": i["Origin"]["name"],
                    "o_time": i["Origin"]["time"][:5],
                    "d_name": i["Destination"]["name"],
                    "d_time": i["Destination"]["time"][:5],
                    "line": "🗿",
                    "class": "walk"
                })

        return final


def sl_search(start, dest):
    search_key = '9af74c05d3464ed3b18fa132c9b41726'

    station_info = [start, dest]

    for i, search_string in enumerate(station_info):
        get_site_id = 'https://api.sl.se/api2/typeahead.json?key=' + search_key + \
            '&searchstring=' + search_string + '&stationsonly=False&maxresults=1'
        req = requests.get(get_site_id)
        req_json = json.loads(req.text)
        station_info[i] = req_json['ResponseData'][0]

    origin_out = None
    dest_out = None

    if station_info[0]["Type"] == "Address":
        y = station_info[0]["Y"]
        x = station_info[0]["X"]
        origin_out = (y[:2] + '.' + y[2:], x[:2] + '.' + x[2:])
    else:
        origin_out = station_info[0]["SiteId"]

    if station_info[1]["Type"] == "Address":
        y = station_info[1]["Y"]
        x = station_info[1]["X"]
        dest_out = (y[:2] + '.' + y[2:], x[:2] + '.' + x[2:])
    else:
        dest_out = station_info[1]["SiteId"]

    return origin_out, dest_out


def sl_get_trip(origin, dest, dest_time, dest_date_offset=1):
    today = date.today()
    tomorrow = today + timedelta(days=dest_date_offset)

    d1 = tomorrow.strftime("%Y-%m-%d")

    origin_in, dest_in = sl_search(origin, dest)

    origin_string = ""

    if type(origin_in) == tuple:
        origin_string = "originCoordLat=" + \
            origin_in[0] + "&originCoordLong=" + origin_in[1]
    else:
        origin_string = "originId=" + origin_in + "&"

    dest_string = ""

    if type(dest_in) == tuple:
        dest_string = "destCoordLat=" + \
            dest_in[0] + "&destCoordLong=" + dest_in[1]
    else:
        dest_string = "destId=" + dest_in

    trip_key = '6828b3e5b4b04737b4311891e825e913'

    print(trip_key, origin_string, dest_string, d1, dest_time)
    get_trip = "http://api.sl.se/api2/TravelplannerV3_1/trip.json?key=" + trip_key + "&" + \
        origin_string + "&" + dest_string + "&Date=" + \
        d1 + "&Time=" + dest_time + "&searchForArrival=1"
    req = requests.get(get_trip)
    req_json = json.loads(req.text)

    trips = [Trip(trip) for trip in req_json["Trip"]]
    trips.reverse()
    return trips
