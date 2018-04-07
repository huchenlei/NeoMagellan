# coding:utf-8
"""
Created on Dec 09, 2016

@author: Charlie
"""
import json
import os
import requests

from flask import Flask, send_from_directory, request, session
from pymongo import MongoClient
from bson import json_util

from utils.profile_utils import ProfileReportParser, parse_info_page, parse_profile_list_page, check_authorization, \
    ProfileException, create_new_profile, check_submit_profile
from utils.course_utils import get_course_info

app = Flask(__name__)
app.debug = True

with open("/var/www/NeoMagellan/config/dbAccount.json", 'r') as f:
    db_account = json.loads(f.read())
    db_username = db_account["username"]
    db_password = db_account["password"]
db_client = MongoClient(
    "mongodb://" + db_username + ":" + db_password +
    "@localhost:27017/")  # default max 100 connections good enough for ECEs


@app.route("/")
@app.route("/index")
def root():
    return send_from_directory(
        os.path.join(app.root_path, 'templates'), 'index.html')


# user login
@app.route("/profile_list", methods=['POST'])
def get_profile_list():
    """With username and password posted return the user profile list.

    session["base_url"]
    session["student_id"]
    summary
    """
    data = json.loads(request.data.decode("utf-8"))
    username = data["username"]
    password = data["password"]
    # set the base url
    base_url = "https://" + username + ":" + password + "@magellan.ece.toronto.edu"
    session["base_url"] = base_url

    # fetch HTML info from Official Magellan
    try:
        info_page = requests.get(base_url + "/student_view.php").text
        profile_list_page = requests.get(base_url + "/profile_menu.php").text
    except Exception as e:
        print("Error in  /profile+list: " + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Connection Error: Unable to reach School Magellan Server"
        })

    # check whether username and password are correct
    if not check_authorization(info_page):
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Sorry, it seems like your username or password are incorrect"
        })
    # parse HTML
    try:
        student_id = parse_info_page(info_page)
        profile_list = parse_profile_list_page(profile_list_page)
    except ProfileException as e:
        print("ProfileError: " + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Sorry, something wrong happened, please try again later"
        })

    session["student_id"] = student_id
    return json.dumps({
        "studentId": student_id,
        "profileList": profile_list,
        "status": "200"
    })


@app.route("/shared_profile_list/<page_number>", methods=['GET'])
def get_shared_profile_list(page_number):
    """return shared profile list"""
    page_number = int(page_number)
    if page_number < 1:
        return
    item_per_page = 5
    profiles = db_client.NeoMagellan.profiles
    result = profiles.find({
        "shareOptions.share": True
    }, {"shareOptions": True,
        "personalInfo":
        True}).skip(item_per_page * (page_number - 1)).limit(item_per_page)
    return json.dumps(list(result), default=json_util.default)


@app.route("/existing_profile", methods=['POST'])
def use_existing_profile():
    """
    go to course selecting page, returns HTML,
    save to session: profile_name
    """
    session["profile_name"] = request.form["profileName"]
    return send_from_directory(
        os.path.join(app.root_path, 'templates'),
        'course_select.html')  # choose profile


@app.route("/new_profile", methods=['POST'])
def use_new_profile():
    """Create new profile.

    save to session: profile_name
    """
    session["profile_name"] = request.form["newProfileName"]
    try:
        create_new_profile(session["profile_name"], session["base_url"],
                           session["student_id"])
        return send_from_directory(
            os.path.join(app.root_path, 'templates'), 'course_select.html')
    except Exception as e:
        print("[Error] In /new_profile:\n" + str(e))
        return send_from_directory(
            os.path.join(app.root_path, 'templates'), 'error.html')


@app.route("/shared_profile", methods=['POST'])
def use_shared_profile():
    """Load shared profile.

    save to session: profile_name
    """
    session["profile_name"] = request.form["newProfileName"]
    profile_id = request.form["profileId"]
    profiles = db_client.NeoMagellan.profiles
    profile_to_use = profiles.find_one({"_id": profile_id})
    try:
        if profile_to_use is None:
            raise Exception(
                "GOT ATTACKED!")  # if got attacked, the server won't crash

        create_new_profile(session["profile_name"], session["base_url"],
                           session["student_id"])
        check_submit_profile(
            profile_to_use["payload"],
            session["student_id"],
            session["profile_name"],
            session["base_url"],
            method="submit")

        return send_from_directory(
            os.path.join(app.root_path, 'templates'), 'course_select.html')
    except Exception as e:
        print("[Error] In /shared_profile:\n" + str(e))
        return send_from_directory(
            os.path.join(app.root_path, 'templates'), 'error.html')


@app.route("/profile", methods=['GET'])
def get_profile():
    """ get user profile details based on student_id and profile name, returns json """
    # the POST data to official Magellan server
    data = {
        "view_personid": session["student_id"],
        "profile_name": session["profile_name"]
    }
    try:
        page = requests.post(
            session["base_url"] + "/profile_view_report.php", data=data).text
    except Exception as e:
        print("[Error] In /profile:\n" + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Connection Error: Unable to reach School Magellan Server"
        })
    try:
        return json.dumps(ProfileReportParser(page).parse())
    except ProfileException as e:
        print("ProfileError: " + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Sorry, something wrong happened, please try again later"
        })


@app.route("/submit_profile", methods=['POST'])
def submit_profile():
    """
    submit the profile to Magellan Server
    :return: json
    """
    data = json.loads(request.data.decode("utf-8"))
    try:
        # save profile to database
        profiles = db_client.NeoMagellan.profiles
        existing_profile = profiles.find_one({
            "personalInfo": data['personalInfo'],
            "shareOptions.description": data["shareOptions"]["description"]
        })
        # prevent multiple submit of same profile
        if existing_profile is None:
            profiles.insert_one(data)

        payload = data['payload']
        return check_submit_profile(
            payload,
            session["student_id"],
            session["profile_name"],
            session["base_url"],
            method="submit")
    except ProfileException as e:
        print("ProfileError: " + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Sorry, something wrong happened, please try again later"
        })
    except Exception as e:
        print("[Error] In /submit_profile:\n" + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Connection Error: Unable to reach School Magellan Server"
        })


@app.route("/check_profile", methods=['POST'])
def check_profile():
    """
    validate of profile
    :return: json(the same structure as get profile)
    """
    data = json.loads(request.data.decode("utf-8"))
    try:
        return check_submit_profile(
            data,
            session["student_id"],
            session["profile_name"],
            session["base_url"],
            method="check")
    except ProfileException as e:
        print("ProfileError: " + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Sorry, something wrong happened, please try again later"
        })
    except Exception as e:
        print("[Error] In /check_profile:\n" + str(e))
        return json.dumps({
            "status": "500",
            "errorMessage":
            "Connection Error: Unable to reach School Magellan Server"
        })


@app.route("/course_list/<course_list_type>", methods=['GET'])
def get_course_list(course_list_type):
    """return the course list json"""
    if course_list_type == "main":
        return send_from_directory(
            os.path.join(app.root_path, 'static'), 'main_course_list.json')
    elif course_list_type == "elective":
        return send_from_directory(
            os.path.join(app.root_path, 'static'), 'elec_course_list.json')


@app.route("/course_detail/<course_code>", methods=['GET'])
def get_course_detail(course_code):
    """
    query the database or the remote server for detailed course info details
    :param course_code: full course code including H1 or Y1 at the end
    :return: json
    """
    db = db_client.NeoMagellan
    # print("[Get course detail] " + course_code)  # log each request
    try:
        result = get_course_info(course_code, db, session["base_url"])
    except ValueError:
        # the course is not available(wrong course code or year)
        return json.dumps({
            "status": "500",
            "errorMessage": "The course description is unavailable right now"
        })
    except Exception as e:
        return json.dumps({"status": "500", "errorMessage": str(e)})
    result.update({"status": "200"})
    return json.dumps(result, default=json_util.default)


@app.route("/test_profile", methods=['GET'])
def get_test_profile():
    """For testing."""
    if os.path.exists('config/account.json'):
        with open('config/account.json', 'r') as f:
            account = json.loads(f.read())
            username = account["username"]
            password = account["password"]
            student_id = account["student_id"]
            session[
                "base_url"] = "https://" + username + ":" + password + "@magellan.ece.toronto.edu"
            session["student_id"] = student_id
    return send_from_directory('static', 'info.json')


@app.route("/test_course_select", methods=['GET'])
def get_test_course_select():
    """For testing."""
    session['profile_name'] = "Test_4"
    return send_from_directory(
        os.path.join(app.root_path, 'templates'), 'course_select.html')


@app.route("/components/<component_name>")
def get_component(component_name):
    """Provide access to static components."""
    return send_from_directory(
        os.path.join(app.root_path, 'templates'), component_name)


# for local testing
# app.secret_key = "1sdfsdfsdfsabasewfwae324"

if __name__ == "__main__":
    app.run()
