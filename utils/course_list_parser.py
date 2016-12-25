"""
this file aims to parse the html of course selecting page to course_list.json
@author Charlie
"""
from lxml import etree
import json


def parse(page, elec_txt):
    json_result = {}

    main_areas = []
    area_list = page.xpath('//table[@style = "width:100%; margin-top:10px;"]')
    for area in area_list[:-6]:
        area_name = area.xpath('.//span[@class = "header_title"]/text()')[0].strip()[8:]
        course_code_list = area.xpath('.//table[@style = "width:100%;"]//a/text()')
        course_name_list = [text[2:].strip() for text in
                            area.xpath('.//table[@style = "width:100%;"]//a/../node()[last()]')]
        course_list = []
        for i, course_code in enumerate(course_code_list):
            course_list.append({"courseCode": course_code[:6],
                                "courseLength": course_code[6:8],
                                "courseTime": course_code[-1],
                                "courseName": course_name_list[i]})
        main_areas.append({"areaName": area_name, "courseList": course_list})
    json_result.update({"mainAreas": main_areas})

    elec_areas = []
    elec_list = elec_txt.split('|')
    elec_area = set()
    # get all areas of elective
    for elec in elec_list:
        elec_area.add(elec[:3])
    for area in elec_area:
        course_list = []
        for elec in elec_list:
            if area == elec[:3]:
                # print(elec)
                course_info = elec.split()
                if len(course_info) == 0:
                    break
                course_list.append({"courseCode": course_info[0][:6],
                                    "courseLength": elec[6:8],
                                    "courseName": elec[9:-5].strip(),
                                    "courseCategory": course_info[-1]})
        elec_areas.append({"areaCode": area, "courseList": course_list})

    json_result.update({"main": main_areas, "elective": elec_areas})
    return json.dumps(json_result, indent=4, separators=(',', ': '))


with open("../cached_pages/main_page.html", 'r') as f:
    with open("../cached_pages/hss_cs.txt", 'r') as t:
        page = etree.HTML(f.read())
        elec_txt = t.read()
        json_data = parse(page, elec_txt)
        with open("../static/course_list.json", 'w') as j:
            j.write(json_data)
