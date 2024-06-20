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

from models.otf import WorkoutData
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
IMPERIAL_UNITS = False


def post_activity(single_performance: WorkoutData):
    """
    Run, Rowing, Workout, WeightTraining etc are types.
    """
    from strava.api._helpers import client, url

    # name, type, start_date_local, elapsed_time, description = None, distance = None
    sport_type = "Workout"
    workout_type = "Workout"
    distance = None
    name = single_performance.workout.classType
    if single_performance.workout.classType == "Tread 50":
        sport_type = "Run"
        workout_type = "Run"
        distance = (
            single_performance.treadmill_data.total_distance["Value"] * 1609.344
        )  # Meters

    activity = Activity(
        name,
        workout_type,
        sport_type,
        single_performance.workout.classDate,
        single_performance.workout.activeTime,
        description=single_performance.workout.classType,
        distance=distance,
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
    if current_token["expires_at"] > int(time.time()):
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
    if not assert_user_input(wrk, data_class_counter):
        return False
    return int(wrk)


if __name__ == "__main__":

    strava_login()

    studio_header, res, studio_token = get_in_studio_response(OTF_EMAIL, OTF_PASSWORD)

    in_studio_response_json = json.loads(res.content)
    memberUuid = in_studio_response_json["data"][0]["memberUuId"]
    class_type_counter = {}
    classes_by_coach = {}

    # print(memberUuid)

    member_details_url = (
        "https://api.orangetheory.co/member/members/"
        + memberUuid
        + "?include=memberClassSummary"
    )
    member_details_response = requests.get(member_details_url, headers=studio_header, timeout=10)
    member_details_response_json = json.loads(member_details_response.content)["data"]

    data_class_counter = 0
    performances = []
    for workout in in_studio_response_json["data"]:
        # List the last 20 workouts
        if data_class_counter < 20:
            perf_res = get_performance_response(
                class_history_uuid=workout["classHistoryUuId"],
                member_uuid=memberUuid,
                token=studio_token,
            )
            performance = WorkoutData(
                workout=workout, data=json.loads(perf_res.content)
            )
            performances.append(performance)
            data_class_counter += 1

    print("Select a workout to post to Strava:")
    for ix, performance in enumerate(performances):
        print(
            f"Workout #{ix+1}, Date: {performance.workout.classDate}, Type: {performance.workout.classType}"
        )

    while True:
        workout_to_post = get_input()
        if workout_to_post:
            break
    # post_to_strave(workout_to_post, performances, token)
    post_this = performances[workout_to_post - 1]

    print("Posting workout to Strava...")
    post_activity(post_this)
