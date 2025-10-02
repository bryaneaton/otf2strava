#!/usr/bin/env python3
"""
Entry Point for the Orange Theory Fitness to Strava Integration
"""
import json
import os
import sys
import time
import webbrowser
import yaml
import requests
from strava.api import oauth2
from strava.config import creds_store
from otf_api import Otf, OtfUser
from otf_api.models import Workout

from models.strava import Activity
from datetime import datetime, timedelta, timezone

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
IMPERIAL_UNITS = False

def get_workout_duration_minutes(start_time, end_time):
    """Calculate workout duration in minutes"""
    if isinstance(start_time, str):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    if isinstance(end_time, str):
        end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    duration = int((end_time - start_time).total_seconds() / 60)
    # if duration is less than 0 set it to positive
    if duration < 0:
        duration = -duration
    return duration

def post_activity(single_performance: Workout):
    """
    Run, Rowing, Workout, WeightTraining etc are types.
    """
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
            distance = single_performance.treadmill_data.total_distance.display_value * 1609.344
    
    workout_duration = sum([s[1] for s in single_performance.zone_time_minutes]) * 60

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
    else:
        print("Failed to post workout!")
        print(response.content)


def strava_login():
    """
    Login to Strava
    :return:
    """
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


def get_performance_response(class_history_uuid, member_uuid, token):
    """
    Get the performance response
    :param class_history_uuid:
    :param member_uuid:
    :param token:
    :return:
    """
    payload = {"ClassHistoryUUId": class_history_uuid, "MemberUUId": member_uuid}
    url = "https://performance.orangetheory.co/v2.4/member/workout/summary"
    perf_header = gen_header(token)
    return requests.post(url, headers=perf_header, json=payload, timeout=10)


def get_in_studio_response(email, password):
    """
    Get the in studio response
    :param email:
    :param password:
    :return:
    """
    header = '{"Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth"}'
    body = (
        '{"AuthParameters": {"USERNAME": "'
        + email
        + '", "PASSWORD": "'
        + password
        + '"}, "AuthFlow": "USER_PASSWORD_AUTH", "ClientId": "65knvqta6p37efc2l3eh26pl5o"}'
    )

    header = json.loads(header)
    body = json.loads(body)

    response = requests.post(
        "https://cognito-idp.us-east-1.amazonaws.com/", headers=header, json=body, timeout=10
    )

    if response.status_code != 200:
        print("Failed to authenticate to OTF. Please update the creds.yaml file...")
        sys.exit(1)

    this_token = json.loads(response.content)["AuthenticationResult"]["IdToken"]

    endpoint = "https://api.orangetheory.co/virtual-class/in-studio-workouts"
    header = gen_header(this_token)

    studio_response = requests.get(endpoint, headers=header, timeout=10)

    return header, studio_response, this_token


def gen_header(token):
    """
    Generate the header
    :param token:
    :return:
    """
    return {
        "Content-Type": "application/json",
        "Authorization": token,
        "Connection": "keep-alive",
        "accept": "appliction/json",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://otlive.orangetheory.com",
        "referer": "https://otlive.orangetheory.com",
        "sec-ch-ua": '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
        "sec-ch-ua-platform": '"macOS"',
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/103.0.0.0 Safari/537.36",
    }


def assert_user_input(inp, cnt):
    """
    Assert the user input
    :param inp:
    :param cnt:
    :return:
    """
    if not inp.isdigit():
        print("Input must be an integer")
        return False
    if int(inp) > cnt:
        print(f"Invalid Workout #,  must be less than {cnt}")
        return False
    return True


def get_input():
    """
    Get the input
    :return:
    """
    wrk = input("Please enter your input: ")
    if not assert_user_input(wrk, len(workouts)):
        return False
    return int(wrk)


if __name__ == "__main__":

    strava_login()

    otf = Otf(user=OtfUser(OTF_EMAIL, OTF_PASSWORD))
    class_type_counter = {}
    classes_by_coach = {}

    # print(memberUuid)

    workouts = otf.workouts.get_workouts(start_date=datetime.now() - timedelta(days=7))


    print("Select a workout to post to Strava:")
    for ix, performance in enumerate(workouts):
        print(
            f"Workout #{ix+1}, Date: {performance.otf_class.starts_at.strftime("%Y-%m-%d %H:%M:%S")}, Type: {performance.otf_class.name}"
        )

    while True:
        workout_to_post = get_input()
        if workout_to_post:
            break
    # post_to_strave(workout_to_post, performances, token)
    post_this = workouts[workout_to_post - 1]

    print("Posting workout to Strava...")
    post_activity(post_this)
