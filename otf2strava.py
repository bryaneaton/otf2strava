#!/usr/bin/env python3
"""
Entry Point for the Orange Theory Fitness to Strava Integration
"""
import os
import sys
import time
import webbrowser
from datetime import datetime, timedelta

import yaml
from strava.api import oauth2
from strava.config import creds_store
from otf_api import Otf, OtfUser
from otf_api.models import Workout

from models.strava import Activity

with open('creds.yaml', 'r', encoding='utf-8') as file:
    creds = yaml.safe_load(file)

OTF_EMAIL = creds['OTF_EMAIL'] or os.getenv("OTF_EMAIL")
OTF_PASSWORD = creds['OTF_PASSWORD'] or os.getenv("OTF_PASSWORD")
STRAVA_CLIENT_ID = creds['STRAVA_CLIENT_ID'] or os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = creds['STRAVA_CLIENT_SECRET'] or os.getenv("STRAVA_CLIENT_SECRET")

STRAVA_AUTH_API_BASE_URL = "https://www.strava.com/oauth"
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"

CLIENT_SCOPE = ["activity:read_all,activity:write"]
AUTH_URL = f"{STRAVA_AUTH_API_BASE_URL}/authorize"
TOKEN_URL = f"{STRAVA_AUTH_API_BASE_URL}/token"
REFRESH_TOKEN_URL = TOKEN_URL

def post_activity(single_performance: Workout):
    """
    Post a workout activity to Strava.

    Args:
        single_performance (Workout): The workout data from OTF
    """
    # pylint: disable=import-outside-toplevel
    from strava.api._helpers import client, url

    # name, type, start_date_local, elapsed_time, description = None, distance = None
    sport_type = "Workout"
    workout_type = "Workout"
    distance = None
    name = single_performance.otf_class.name
    if single_performance.otf_class.name == "Tread 50":
        sport_type = "Run"
        workout_type = "Run"
    if "Strength" in single_performance.otf_class.name.lower():
        sport_type = "Workout"
        workout_type = "Strength Training"
    if single_performance.treadmill_data.total_distance.display_unit == "miles":
        distance = (
            single_performance.treadmill_data.total_distance.display_value * 1609.344
        )
    workout_duration = sum(s[1] for s in single_performance.zone_time_minutes) * 60

    telemetry = [tel.hr for tel in single_performance.telemetry.telemetry if tel.hr > 0]



    activity = Activity(
        name,
        workout_type,
        sport_type,
        single_performance.otf_class.starts_at,
        workout_duration,
        description=single_performance.otf_class.name,
        distance=distance,
        calories=single_performance.calories_burned,
        max_heartrate=single_performance.telemetry.max_hr,
        avg_heartrate=sum(telemetry) / len(telemetry),
    )

    response = client.post(url("/activities"), json=activity.to_dict())

    if response.status_code == 201:
        print("Workout posted successfully!")
    elif response.status_code == 409:
        print("Workout already exists!")
    elif response.status_code:
        print(f"Failed to post workout! {response.status_code} {response.content}")
    else:
        print("Failed to post workout!")
        print(response.content)


def strava_login():
    """
    Authenticate and login to Strava using OAuth2.

    Handles the complete OAuth2 flow including opening browser for user consent.
    """
    # pylint: disable=import-outside-toplevel
    from strava.api._helpers import client

    current_token = client.token
    if current_token and current_token["expires_at"] > int(time.time()):
        print("Already logged in.")
        return

    code = None
    auth_flow = oauth2.OAuth2AuthorizationCodeFlow(
        client_id=STRAVA_CLIENT_ID,
        client_secret=STRAVA_CLIENT_SECRET,
        scope=CLIENT_SCOPE,
        auth_url=AUTH_URL,
        token_url=TOKEN_URL,
    )
    url, state = auth_flow.authorization_url()
    webbrowser.open(url)
    try:
        code = auth_flow.get_authorization_code(state)
        data = auth_flow.get_access_token(code)
        creds_store.save_access_token(data)
        print("Login successful.")
    except oauth2.AuthenticationError:
        print("Access was denied!")
        sys.exit(1)



def main():
    """Main function to run the OTF to Strava integration."""
    strava_login()

    otf = Otf(user=OtfUser(OTF_EMAIL, OTF_PASSWORD))

    workouts = otf.workouts.get_workouts(
        start_date=datetime.now() - timedelta(days=7)
    )

    print("Select a workout to post to Strava:")
    for ix, performance in enumerate(workouts):
        workout_date = performance.otf_class.starts_at.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"Workout #{ix+1}, Date: {workout_date}, "
            f"Type: {performance.otf_class.name}"
        )

    while True:
        wrk = input("Please enter your input: ")
        if wrk.isdigit() and int(wrk) <= len(workouts) and int(wrk) > 0:
            workout_to_post = int(wrk)
            break
        print("Input must be a valid workout number")

    post_this = workouts[workout_to_post - 1]

    print("Posting workout to Strava...")
    post_activity(post_this)


if __name__ == "__main__":
    main()
