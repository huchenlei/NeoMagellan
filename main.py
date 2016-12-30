# coding:utf-8
"""
Created on Dec 09, 2016

@author: Charlie
"""
import json
import requests

from flask import Flask, send_from_directory, request, session
from pymongo import MongoClient
from bson import json_util

from utils.profile_utils import ProfileReportParser, parse_info_page, parse_profile_list_page, check_authorization, \
    ProfileException
from utils.course_utils import get_course_info

app = Flask(__name__)
app.debug = True

db_client = MongoClient()  # default max 100 connections good enough for ECEs


@app.route("/")
@app.route("/index")
def root():
    return send_from_directory('templates', 'index.html')


# user login
@app.route("/profile_list", methods=['POST'])
def get_profile_list():
    """ with username and password posted
    return the user profile list
    session["base_url"]
    session["student_id"]
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
        return json.dumps({"status": "500",
                           "errorMessage": "Connection Error: Unable to reach School Magellan Server"})

    # check whether username and password are correct
    if not check_authorization(info_page):
        return json.dumps({"status": "500",
                           "errorMessage": "Sorry, it seems like your username or password are incorrect"})
    # parse HTML
    try:
        student_id = parse_info_page(info_page)
        profile_list = parse_profile_list_page(profile_list_page)
    except ProfileException as e:
        print("ProfileError: " + str(e))
        return json.dumps({"status": "500",
                           "errorMessage": "Sorry, something wrong happened, please try again later"})

    session["student_id"] = student_id
    return json.dumps({"studentId": student_id,
                       "profileList": profile_list,
                       "status": "200"})


@app.route("/course_select", methods=['POST'])
def course_select():
    """
    go to course selecting page, returns HTML,
    handles new profile action
    session["profile_name"]
    """
    new_profile = request.form.getlist("newProfile")  # handle checkbox
    new_profile_name = request.form["newProfileName"]

    if new_profile:
        print("new a profile")
        try:
            data = {
                "profile_name": new_profile_name,
                "profile_action": "Create New",
                "profile_new": "new"
            }
            m_session = requests.session()
            requests.post(session["base_url"] + "/profile_edit.php", data=data)
            data = {
                "profile_name": new_profile_name,
                "profile_action": "Create New",
                "view_personid": session["student_id"]
            }
            m_session.post(session["base_url"] + "/profile_view_report.php", data=data)
            m_session.post(session["base_url"] + "/profile_edit_save.php", data=data)
            session["profile_name"] = new_profile_name
        except Exception as e:
            print("[Error] In /course_select:\n" + str(e))
            return send_from_directory('templates', 'error.html')
    else:
        session["profile_name"] = request.form["profileName"]

    return send_from_directory('templates', 'course_select.html')  # choose profile


@app.route("/profile", methods=['GET'])
def get_profile():
    """ get user profile details based on student_id and profile name, returns json """
    # the POST data to official Magellan server
    data = {"view_personid": session["student_id"], "profile_name": session["profile_name"]}
    try:
        page = requests.post(session["base_url"] +
                             "/profile_view_report.php", data=data).text
    except Exception as e:
        print("[Error] In /profile:\n" + str(e))
        return json.dumps({"status": "500",
                           "errorMessage": "Connection Error: Unable to reach School Magellan Server"})
    try:
        return ProfileReportParser(page).parse()
    except ProfileException as e:
        print("ProfileError: " + str(e))
        return json.dumps({"status": "500",
                           "errorMessage": "Sorry, something wrong happened, please try again later"})


@app.route("/submit_profile", methods=['POST'])
def submit_profile():
    """
    submit the profile to Magellan Server
    :return: json
    """
    try:
        data = json.loads(request.data.decode("utf-8"))
        student_info = {
            "view_personid": session["student_id"],
            "profile_name": session["profile_name"],
            "profile_action": "Edit Profile"
        }
        data.update(student_info)
        # submit to view page
        requests.post(session["base_url"] + "/profile_view_report.php", data)

        m_session = requests.session()
        m_session.post(session["base_url"] + "/profile_edit_save.php", student_info)
        return json.dumps({"status": "200"})
    except Exception as e:
        print("[Error] In /submit_profile:\n" + str(e))
        return json.dumps({"status": "500",
                           "errorMessage": "Connection Error: Unable to reach School Magellan Server"})


@app.route("/check_profile", methods=['POST'])
def check_profile():
    """
    validate of profile
    :return: json(the same structure as get profile)
    """
    data = json.loads(request.data.decode("utf-8"))
    data.update({
        "view_personid": session["student_id"],
        "profile_name": session["profile_name"],
        "profile_action": "Edit Profile"
    })
    page = requests.post(session["base_url"] + "/profile_view_report.php").text
    return ProfileReportParser(page).parse()


@app.route("/course_list/<course_list_type>", methods=['GET'])
def get_course_list(course_list_type):
    """return the course list json"""
    if course_list_type == "main":
        return send_from_directory('static', 'main_course_list.json')
    elif course_list_type == "elective":
        return send_from_directory('static', 'elec_course_list.json')


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
        return json.dumps({"status": "500", "errorMessage": "The course description is unavailable right now"})
    except Exception as e:
        return json.dumps({"status": "500", "errorMessage": str(e)})
    result.update({"status": "200"})
    return json.dumps(result, default=json_util.default)


@app.route("/test_profile", methods=['GET'])
def get_test_profile():
    """ for testing """
    with open('config/account.json', 'r') as f:
        account = json.loads(f.read())
        username = account["username"]
        password = account["password"]
        session["base_url"] = "https://" + username + ":" + password + "@magellan.ece.toronto.edu"
    return send_from_directory('static', 'info_prerequisite.json')


@app.route("/test_course_select", methods=['GET'])
def get_test_course_select():
    """ for testing """
    session['profile_name'] = "Test_1"
    return send_from_directory('templates', 'course_select.html')


@app.route("/components/<component_name>")
def get_component(component_name):
    return send_from_directory('templates', component_name)


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
if __name__ == "__main__":
    app.run()
