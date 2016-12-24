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

from profile_utils import ProfileReportParser, parse_info_page, parse_profile_list_page
from course_utils import get_course_info

app = Flask(__name__)
app.debug = True

db_client = MongoClient()


@app.route("/")
@app.route("/index")
def root():
    return send_from_directory('templates', 'index.html')


# user login
@app.route("/profile_list", methods=['POST'])
def get_profile_list():
    """ with username and password posted
    return the user profile list """

    data = json.loads(request.data.decode("utf-8"))
    username = data["username"]
    password = data["password"]
    # set the base url
    base_url = "https://" + username + ":" + password + "@magellan.ece.toronto.edu"
    session["base_url"] = base_url

    # fetch HTML info from Official Magellan
    info_page = requests.get(base_url + "/student_view.php").text
    profile_list_page = requests.get(base_url + "/profile_menu.php").text

    # parse HTML
    student_id = parse_info_page(info_page)
    session["student_id"] = student_id
    profile_list = parse_profile_list_page(profile_list_page)

    return json.dumps({"studentId": student_id, "profileList": profile_list})


# choose profile
@app.route("/profile", methods=['POST'])
def get_profile():
    """ get user profile details based on student_id and profile name """
    print(request.data)
    profile_name = (json.loads(request.data.decode('utf-8')))["profileName"]
    # the POST data to official Magellan server
    data = {"view_personid": session[
        "student_id"], "profile_name": profile_name}
    page = requests.post(session["base_url"] +
                         "/profile_view_report.php", data=data).text
    course_table = ProfileReportParser(page).parse()
    return course_table
    # return send_from_directory('static', 'info.json')


@app.route("/course_select", methods=['GET'])
def course_select():
    """go to course selecting page"""
    return send_from_directory('templates', 'course_select.html')


@app.route("/course_list", methods=['GET'])
def get_course_list():
    """return the course list json"""
    return send_from_directory('static', 'course_list.json')


@app.route("/course_detail/<course_code>", methods=['GET'])
def get_course_detail(course_code):
    """
    query the database or the remote server for detailed course info details
    :param course_code: full course code including H1 or Y1 at the end
    :return: json
    """
    db = db_client.NeoMagellan
    print("[Get course detail] " + course_code)  # log each request
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
    """for testing"""
    with open('config/account.txt', 'r') as f:
        username = f.readline().split()[0]  # get rid of \n at the end of the string
        password = f.readline()
        session["base_url"] = "https://" + username + ":" + password + "@magellan.ece.toronto.edu"
    return send_from_directory('static', 'info.json')


# @app.route("/test_modal", methods=['GET'])
# def test_modal():
#     """for testing"""
#     return send_from_directory('temp', 'modal.html')


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
if __name__ == "__main__":
    app.run()
