# coding=utf-8
"""
Created on Nov 02, 2016

@author: Charlie
"""

from lxml import etree

import requests
import json
import re
import datetime


def cache_page(name, html):
    with open("cached_pages/" + name + ".html", 'w') as f:
        f.write(html)


class ProfileException(Exception):
    pass


class ProfileReportParser(object):
    """
    this class parse the edit profile page(html) to a course table json object
    the object is available at static/info.json
    """

    def __init__(self, page):
        """
        parse the html string to lxml processable object
        :param page: the html string of view page
        """
        self.raw_page = page
        self.page = etree.HTML(page)

    def parse(self):
        json_result = {}
        try:
            tables = self.page.xpath('//table[starts-with(@style, "width:100%;")]')
            if len(tables) < 10:
                raise ProfileException("Missing info tables in profile!:" + str(len(tables)))
            if len(tables) > 12:
                raise ProfileException("Unexpected tables in profile!:" + str(len(tables)))
            # if there was prerequisite error, there would be 1 more table, and table after
            # prerequisite table would be offset by 1
            # if there was co-requisite error, there would be 1 another more table, and table after
            # co-requisite table would be offset by 1
            offset = len(tables) - 10

            json_result.update({"lastUpdated": self.get_update_info(tables[0])})
            json_result.update({"personalInfo": self.get_personal_info(tables[1])})
            json_result.update({"courseTable": self.get_course_table(tables[3])})
            if offset > 0:
                json_result.update({"prerequisiteErrors": self.get_prerequisite_errors(tables[4])})
            json_result.update({"courseArrange": self.get_course_arrange(tables[6 + offset])})
            json_result.update({"CEABRequirement": self.get_ceab_requirment(tables[7 + offset])})
            json_result.update({"graduationEligibility": self.get_eligibility(tables[9 + offset])})
        except ProfileException as e:
            cache_page(str(e) + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), self.raw_page)
            raise e
        return json.dumps(json_result, indent=4, separators=(',', ': '))

    def get_update_info(self, table):
        update_string = table.xpath('.//td[@colspan = "2"]/text()')
        if len(update_string) != 0:
            if hasattr(update_string[0], 'strip'):
                return update_string[0].strip()
        else:
            raise ProfileException("Failed to get update info")

    def get_personal_info(self, table):
        """
        parse the table containing personal info
        :param table: etree object
        :return: dictionary
        """
        json_result = {}
        row_list = table.xpath('./tr[position() > 1]')
        for row in row_list:
            row_key = row.xpath('./td[1]/b/text()')
            if row_key:
                row_key = row_key[0]
            else:
                raise ProfileException("Failed to get key of personal info")
            row_value = row.xpath('./td[2]/text()')
            if (len(row_value) != 0) & hasattr(row_value[0], 'strip'):
                row_value = row_value[0].strip()
            else:
                raise ProfileException("Failed to get value of personal info")
            json_result.update({row_key: row_value})
        if json_result:
            return json_result
        else:
            raise ProfileException("Failed to get personal info table(row list is empty)")

    def get_course_table(self, table):
        """
        parse the table containing the course table
        :param table: table etree object
        :return: dictionary
        """
        json_result = {}
        row_list = table.xpath('.//table[@id = "s_course"]/tr[position() > 1]')
        for row in row_list:
            session = row.xpath('./td[1]/text()')
            course_full_code_list = row.xpath('.//a[starts-with(@href, "javascript:course_popup")]/text()')
            course_name_list = row.xpath('.//font[@style = "font-size:7pt;"]/text()')
            course_list = []
            if len(course_full_code_list) != len(course_name_list):
                # year course design project would be count twice
                if ("Design Project" == course_name_list[0]) & \
                        (len(course_full_code_list) + 1 == len(course_name_list)):
                    course_name_list = course_name_list[1:]
                else:
                    raise ProfileException(
                        "Error: unmatched lists. course code list:",
                        course_full_code_list, "\n course name list:", course_name_list)
            for i, full_code in enumerate(course_full_code_list):
                if re.match(re.compile('\w{3}\d{3}[YH]1\s+[SFY]'), full_code) is None:
                    raise ProfileException("Illegal course code!:" + full_code)
                course_list.append({
                    "courseName": course_name_list[i],
                    "courseCode": full_code[0:6],
                    "courseTime": full_code[-1],
                    "courseLength": full_code[6:8]
                })
            # there is a empty session
            if session:
                json_result.update({session[0]: course_list})
        if json_result:
            return json_result
        else:
            raise ProfileException("Failed to get course_table table(row list is empty)")

    def get_prerequisite_errors(self, table):
        has_error = table.xpath('.//span[@style = "color:red;"]/text()')
        errors = []
        if has_error:
            errors = table.xpath('.//table//td/text()')
            errors = [error.strip() for error in errors]
        return errors

    def get_course_arrange(self, table):
        json_result = {}

        sub_tables = table.xpath('.//table[@id = "s_course"]')  # 2 tables

        if len(sub_tables) != 2:
            raise ProfileException("Failed to get course arrange sub tables:" + str(sub_tables))

        area_row_list = sub_tables[0].xpath('./tr[position() > 1]')
        for row in area_row_list:
            area_name = row.xpath('./td[1]/text()')
            if area_name:
                area_name = area_name[0]
            else:
                raise ProfileException("Failed to get area name when getting course arrange(main)")
            course_list = row.xpath('./td[position() > 1]/text()')
            json_result.update(
                {area_name: course_list})  # the first course in course list is kernel, the lefts are depth

        other_row_list = sub_tables[1].xpath('./tr')
        for row in other_row_list:
            area_name = row.xpath('./td[1]/b/text()')
            if area_name:
                area_name = area_name[0]
            else:
                raise ProfileException("Failed to get area name when getting course arrange(others)")

            course_list = row.xpath('./td[position() > 1]/node()')
            processed_course_list = []
            for course in course_list:
                if hasattr(course, 'xpath'):
                    course = course.xpath('./text()')
                    if course:
                        course = course[0].strip()
                        if course == "ECE472H1":
                            processed_course_list.append(course + "N")
                        else:
                            processed_course_list.append(course)
                else:
                    if not len(course.strip()) < 1:
                        if (course[0:3] != "Min") & (course[0:6] != "CS/HSS"):
                            processed_course_list.append(course.strip())
            json_result.update({area_name: processed_course_list})
        return json_result

    def get_ceab_requirment(self, table):
        json_result = {}
        row_list = table.xpath('.//table[@id = "s_course"]/tr[position() > 1 and position() < 10]')
        for row in row_list:
            category = row.xpath('./td[1]/node()')
            # contact nodes together to reform complete cate_name string
            cate_name = category[0]
            if len(category) == 3:
                cate_name += ' ' + category[2]

            info_list = row.xpath('./td[position() > 1]/text()')
            if len(info_list) != 4:
                raise ProfileException("Unexpected CEAB table structure: " + str(len(info_list)) + "cols")
            info_obj = {"minRequirement": info_list[0],
                        "obtained": info_list[1],
                        "projected": info_list[2],
                        "outstanding": info_list[3]}
            json_result.update({cate_name: info_obj})
        return json_result

    def get_eligibility(self, table):
        info_list = table.xpath('.//font/text()')
        if info_list:
            return {"eligibilityList": info_list[:-1],
                    "conclusion": info_list[-1]}
        else:
            raise ProfileException("Failed to get eligibility info")


def parse_profile_list_page(page):
    """" returns a list containing all profiles"""
    page_tree = etree.HTML(page)
    profile_list = page_tree.xpath(
        '//table[@class="table_header"]/tr[position() > 4 and position() < (last() - 3)]/td/node()[1]')
    if profile_list:
        profile_list[0] = "main"
        return [text.strip() for text in profile_list]
    else:
        raise ProfileException("Failed to get profile list")


def parse_info_page(raw_page):
    """ returns the student number string"""
    student_id = etree.HTML(raw_page).xpath('//table[@style="width:100%; margin-top:30px;"]/tr[3]/td[2]/text()')
    if student_id:
        return student_id[0].strip()
    else:
        raise ProfileException("Failed to get student id")


def check_authorization(raw_page):
    """checks whether password and username from user is correct"""
    unauthed = re.match(re.compile('.*<h1>Unauthorized<\/h1>.*', re.S), raw_page)
    if unauthed:
        return False
    else:
        return True


# Test ProfileReportParser

# with open('../config/account.json', 'r') as f:
#     data = json.loads(f.read())
#     username = data["username"]
#     password = data["password"]
#     student_id = data["student_id"]
#
# page = requests.post("https://" + username + ":" + password + "@magellan.ece.toronto.edu/profile_view_report.php",
#                      data={"view_personid": student_id,
#                            "profile_name": "Test_1"}).text
# cache_page("profile", page)
#
# with open("../cached_pages/profile.html", 'r') as f:
#     page = f.read()
#     p = ProfileReportParser(page)
#     table_info = ''
#     try:
#         table_info = p.parse()
#     except ProfileException as e:
#         print(e)
#
#     with open("../static/info.json", 'w') as j:
#         j.write(table_info)

# Test parse profile
# page = requests.get("https://username:password@magellan.ece.toronto.edu/profile_menu.php").text
# print(parse_profile_list_page(page))

# Test parse info page
# page = requests.get("https://username:password@magellan.ece.toronto.edu/student_view.php").text
# print(parse_info_page(page))
