# coding=utf-8
"""
Created on Dec 05, 2016

@author: Charlie
"""

import json
import datetime
import requests
import pymongo

from lxml import etree
from pymongo import MongoClient


def get_course_info(full_course_code, db, base_url):
    """
    if the course is not found in local database, make new request
    to official magellan server, and save the course info to local database
    :param full_course_code: course code used to query database(example: ECE244H1)
    :param db: connection to mongodb database, 1 per session
    :param base_url: base url with username and password
    :return: dictionary(course info)
    """
    # the document collection courses
    courses = db.courses
    course_info = courses.find_one({"course_code": full_course_code[:-2]})

    if course_info is None:
        url = base_url + '/courses_detail_popup.php?popup_acad_act_cd=' \
              + full_course_code + '&popup_offered=' + '2015'  # TODO need to xpath the year info from page
        print("[Getting from Magellan]" + url)
        info_page = requests.get(url).text
        course_info = parse_course_page(info_page)
        courses.insert_one(course_info)
    return course_info


def parse_course_page(raw_page):
    """parse the course page html to dictionary"""
    page = etree.HTML(raw_page)
    # check whether is error page
    if page.xpath('//h1/text()'):
        raise Exception('Unauthorized, please check username and password')

    # get general course info
    info_list = [text.strip() for text in page.xpath('//td[@style = "background-color:#fff;"]/text()')]
    # for some page there are other structure
    info_list_2 = [text.strip() for text in page.xpath('//td[@style = "background-color:#fff;"]/p/text()')]
    course_description = info_list[3][1:-1] if (info_list[3] != '"') else info_list_2[0]

    # get AU info
    au_info_list = [float(text.strip()) for text in page.xpath('//td[@style = "text-align:center;"]/text()')]
    au_json = {"Math": au_info_list[0],
               "NS": au_info_list[1],
               "CS": au_info_list[2],
               "ES": au_info_list[3],
               "ED": au_info_list[4],
               "Total": au_info_list[5]}

    full_course_code = info_list[0].split()[0]
    course_time = info_list[0].split()[1]

    info_json = {"courseName": info_list[2],
                 "courseDescription": course_description,
                 "prerequisites": info_list[-6],
                 "coRequisites": info_list[-5],
                 "exclusions": info_list[-4],
                 "creditWeight": info_list[-3],
                 "auInfo": au_json,
                 "courseCode": full_course_code[:-2],
                 "courseLength": full_course_code[-2:],
                 "courseTime": course_time}
    return info_json

# test case 1
# client = MongoClient()
# db = client.NeoMagellan
# base_url = "https://username:password@magellan.ece.toronto.edu"
#
# get_course_info("ECE244H1", db, base_url)

# test case 2
# with open('../cached_pages/CIV300H1.html', 'r') as f:
#     print(parse_course_page(f.read()))
