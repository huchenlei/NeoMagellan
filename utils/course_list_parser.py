"""
this file aims to parse the html of course selecting page to course_list.json
@author Charlie
"""
from lxml import etree
import json


def parse(page, elec_txt):
    main_areas = []
    area_list = page.xpath('//table[@style = "width:100%; margin-top:10px;"]')
    for area in area_list[:-6]:
        area_name = area.xpath('.//span[@class = "header_title"]/text()')[0].strip()[8:]
        course_code_list = area.xpath('.//table[@style = "width:100%;"]//a/text()')
        course_name_list = [text[2:].strip() for text in
                            area.xpath('.//table[@style = "width:100%;"]//a/../node()[last()]')]
        course_id_list = area.xpath('.//table[@style = "width:100%;"]//select/@id')
        fall_course_list = []
        winter_course_list = []
        for i, course_code in enumerate(course_code_list):
            course_info = {"courseCode": course_code[:6],
                           "courseLength": course_code[6:8],
                           "courseTime": course_code[-1],
                           "courseName": course_name_list[i],
                           "courseId": course_id_list[i]}
            if course_info["courseTime"] == "F":
                fall_course_list.append(course_info)
            else:
                winter_course_list.append(course_info)
        main_areas.append({"areaName": area_name, "courseLists": [fall_course_list, winter_course_list]})

    elec_list = elec_txt.split('|')
    processed_elec_list = []
    elec_courses_pool = set()
    # get all areas of elective
    for elec in elec_list:
        elec_courses_pool.add(elec[:6])

    for elec in elec_list:
        course_info = elec.split()
        if not len(course_info) == 0:
            if elec[:6] in elec_courses_pool:
                elec_courses_pool.remove(elec[:6])
                processed_elec_list.append({"courseCode": course_info[0][:6],
                                            "courseLength": elec[6:8],
                                            "courseName": elec[9:-5].strip(),
                                            "courseCategory": course_info[-1]})
    main_areas_json = json.dumps(main_areas, indent=4, separators=(',', ': '))
    elec_areas_json = json.dumps(processed_elec_list, indent=4, separators=(',', ': '))
    return main_areas_json, elec_areas_json


with open("../cached_pages/main_page.html", 'r') as f:
    with open("../cached_pages/hss_cs.txt", 'r') as t:
        page = etree.HTML(f.read())
        elec_txt = t.read()
        main_data, elec_data = parse(page, elec_txt)
        with open("../static/main_course_list.json", 'w') as m:
            with open("../static/elec_course_list.json", 'w') as e:
                # m.write(main_data)
                e.write(elec_data)
