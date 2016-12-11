# coding=utf-8
"""
Created on Nov 02, 2016

@author: Charlie
"""

from lxml import etree

# import requests
import json


def cache_page(name, html):
    with open("cached_pages/" + name + ".html", 'w') as f:
        f.write(html)


class ProfileReportParser(object):
    """
    this class parse the edit profile page(html) to a course table json object
    the course table json object has following structure:
    {
      [{
        "course_id": "ECE244H1",
        "semester": "2016-9"
      } ...]
    }
    """

    def __init__(self, page):
        """
        parse the html string to lxml processable object
        :param page: the html string of view page
        """
        self.page = etree.HTML(page)

    def parse(self):
        json_result = {}
        tables = self.page.xpath('//table[starts-with(@style, "width:100%;")]')
        json_result.update({"last_updated": self.get_update_info(tables[0])})
        json_result.update({"personal_info": self.get_personal_info(tables[1])})
        # tables[2] has no content in most case
        json_result.update({"course_table": self.get_course_table(tables[3])})
        # tables[4] and tables[5] has no useful content
        json_result.update({"course_arrange": self.get_course_arrange(tables[6])})
        json_result.update({"CEAB_requirement": self.get_ceab_requirment(tables[7])})
        # tables[8] has no useful content
        json_result.update({"graduation_eligibility": self.get_eligibility(tables[9])})
        return json.dumps(json_result, indent=4, separators=(',', ': '))

    def get_update_info(self, table):
        return table.xpath('./tr/td[@colspan = "2"]/text()')[0].strip()

    def get_personal_info(self, table):
        """
        parse the table containing personal info
        :param table: etree object
        :return: dictionary
        """
        json_result = {}
        row_list = table.xpath('./tr[position() > 1]')
        for row in row_list:
            row_key = row.xpath('./td[1]/b/text()')[0]
            row_value = row.xpath('./td[2]/text()')[0].strip()
            # print(row_key, row_value)
            json_result.update({row_key: row_value})
        return json_result

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
            course_list = row.xpath('.//a[starts-with(@href, "javascript:course_popup")]/text()')
            if session:
                json_result.update({session[0]: course_list})
        # print(json_result)
        return json_result

    def get_course_arrange(self, table):
        json_result = {}
        requirement_meet = table.xpath('./tr[1]//b/node()')[0]
        if(hasattr(requirement_meet, "xpath")):
            requirement_meet = requirement_meet.xpath('./font/text()')
        json_result.update({"requirement_meet": requirement_meet})

        sub_tables = table.xpath('./tr[position() < 3]//table[@id = "s_course"]')  # 2 tables
        area_row_list = sub_tables[0].xpath('./tr[position() > 1]')
        for row in area_row_list:
            area_name = row.xpath('./td[1]/text()')[0]
            course_list = row.xpath('./td[position() > 1]/text()')
            json_result.update(
                {area_name: course_list})  # the first course in course list is kernel, the lefts are depth

        other_row_list = sub_tables[1].xpath('./tr')
        for row in other_row_list:
            area_name = row.xpath('./td[1]/b/text()')[0]
            course_list = [text.strip() for text in row.xpath('./td[position() > 1]/text()')]
            json_result.update({area_name: course_list})
        return json_result

    def get_ceab_requirment(self, table):
        json_result = {}
        row_list = table.xpath('.//table[@id = "s_course"]/tr[position() > 1 and position() < 10]')
        for row in row_list:
            category = row.xpath('./td[1]/node()')
            cate_name = category[0]
            if len(category) == 3:
                cate_name += ' ' + category[2]

            info_list = row.xpath('./td[position() > 1]/text()')
            info_obj = {"min_requirement": info_list[0],
                        "obtained": info_list[1],
                        "projected": info_list[2],
                        "outstanding": info_list[3]}
            json_result.update({cate_name: info_obj})
        return json_result

    def get_eligibility(self, table):
        info_list = table.xpath('.//font/text()')
        return {"eligibility_list": info_list[:-1],
                "conclusion": info_list[-1]}


def parse_profile_list_page(page):
    """" returns a list containing all profiles"""
    page_tree = etree.HTML(page)
    profile_list = page_tree.xpath(
        '//table[@class="table_header"]/tr[position() > 4 and position() < (last() - 3)]/td/node()[1]')
    profile_list[0] = "main"
    return [text.strip() for text in profile_list]


def parse_info_page(page):
    """ returns the student number string"""
    return etree.HTML(page).xpath('//table[@style="width:100%; margin-top:30px;"]/tr[3]/td[2]/text()')[0].strip()


# Test ProfileReportParser
# page = requests.post("https://username:password@magellan.ece.toronto.edu/profile_view_report.php",
#                      data={"view_personid": "utorid",
#                            "profile_name": "profile_name"}).text
# cache_page("profile", page)
# with open("cached_pages/profile.html", 'r') as f:
#     page = f.read()
#     p = CourseTableParser(page)
#     table_info = p.parse()
#     with open("cached_pages/info.json", 'w') as j:
#         j.write(table_info)

# Test parse profile
# page = requests.get("https://username:password@magellan.ece.toronto.edu/profile_menu.php").text
# print(parse_profile_list_page(page))

# Test parse info page
# page = requests.get("https://username:password@magellan.ece.toronto.edu/student_view.php").text
# print(parse_info_page(page))
