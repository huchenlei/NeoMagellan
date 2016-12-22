# coding:utf-8
"""
Created on Dec 09, 2016

@author: Charlie
"""
import json
import requests
from flask import Flask, send_from_directory, request, session
from profile_utils import ProfileReportParser, parse_info_page, parse_profile_list_page

app = Flask(__name__)
app.debug = True


@app.route("/")
@app.route("/index")
def root():
    return send_from_directory('templates', 'index.html')


@app.route("/profile_list", methods=['POST'])
def get_profile_list():
    """ get the user profile list """
    print(request.data)
    print(hasattr(request, "form"))

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


@app.route("/profile", methods=['POST'])
def get_profile():
    """ get user profile details based on student_id and profile name """
    print(request.data)
    profile_name = (json.loads(request.data.decode('utf-8')))["profileName"]
    # the POST data to official Magellan server
    data = {"view_personid": session["student_id"], "profile_name": profile_name}
    page = requests.post(session["base_url"] + "/profile_view_report.php", data=data).text
    course_table = ProfileReportParser(page).parse()
    return course_table
    # return send_from_directory('static', 'info.json')


@app.route("/course_select", methods=['GET'])
def course_select():
    """go to course selecting page"""
    return send_from_directory('templates', 'course_select.html')


app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
if __name__ == "__main__":
    app.run()
