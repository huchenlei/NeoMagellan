# coding=utf_8
"""
Created on Dec 05, 2016

@author: Charlie
"""

from lxml import etree

import json


class CourseInfoParser(object):
    """
    this class parse the course page to json
    """

    def __init__(self, page):
        self.page = etree.HTML(page)

    def parse(self):
        # get general course info
        info_list = [text.strip() for text in self.page.xpath('//td[@style = "background-color:#fff;"]/text()')]
        # for some page there are other structure
        info_list_2 = [text.strip() for text in self.page.xpath('//td[@style = "background-color:#fff;"]/p/text()')]
        course_description = info_list[3][1:-1] if (info_list[3] != '"') else info_list_2[0]

        # get AU info
        au_info_list = [float(text.strip()) for text in self.page.xpath('//td[@style = "text-align:center;"]/text()')]
        au_json = {"Math": au_info_list[0],
                   "NS": au_info_list[1],
                   "CS": au_info_list[2],
                   "ES": au_info_list[3],
                   "ED": au_info_list[4],
                   "Total": au_info_list[5]}

        info_json = {"course_name": info_list[2],
                     "course_description": course_description,
                     "prerequisites": info_list[-6],
                     "co_requisites": info_list[-5],
                     "exclusions": info_list[-4],
                     "credit_weight": info_list[-3],
                     "au_info": au_json}
        # some course does not have course credit
        # print(course_id, info_list[-3])
        return json.dump(info_json, indent=4, separators=(',', ': '))
