angular.module('NeoMagellan').service('courseTableService', function() {
    // bind CS HSS information to elective courses in coursetable
    function bindElectiveFields(courseTable, courseArrange) {
        courseArrange['HSS and CS'].forEach((elective) => {
            courseCode = elective.split(' ')[0];
            courseCategory = elective.split(' ')[1];
            // find the elective in courseTable
            // and inject 'courseCategory' field
            for (const year of Object.keys(courseTable)) {
                courseTable[year].forEach((course) => {
                    if ((course.courseCode + course.courseLength) === courseCode) {
                        course['courseCategory'] = courseCategory;
                    }
                });
            }
        });
    };

    // bind course id field to mainCourses in courseTable
    function bindMainFields(courseTable, mainAreas) {
        for (const year of Object.keys(courseTable)) {
            courseTable[year].forEach((course) => {
                let BreakException = {};
                try {
                    mainAreas.forEach((mainArea) => {
                        mainArea.courseLists.forEach((courseList) => {
                            courseList.forEach((mainCourse) => {
                                if (mainCourse.courseCode === course.courseCode) {
                                    if (mainCourse.hasOwnProperty("courseId"))
                                        course['courseId'] = mainCourse.courseId;
                                    if (mainCourse.hasOwnProperty('kernel')) {
                                        course['kernel'] = true;
                                        // console.log('kernel ' + mainCourse.courseCode);
                                    }
                                    // console.log("matching success:" + course['courseId']);
                                    throw BreakException;
                                }
                            });
                        });
                    });
                } catch (e) {
                    if (e !== BreakException) throw e;
                }
            });
        }
    };

    // complete session list
    // and build yearArray
    function completeSessionList(courseTable, yearArray) {
        // find the min session sessions are in form (e.g. 20159, 20161)
        let minYear = null;
        // build a year array for the convenience of course table display
        // in the form (e.g. [{"fallSession": "20159", "winterSession": "20161"} ...])
        for (const year of Object.keys(courseTable)) {
            intYear = parseInt(year);
            if (minYear === null)
                minYear = intYear;
            if (minYear > intYear)
                minYear = intYear;
        }
        minYear = Math.floor(minYear / 10);

        for (let i = 0; i < 5; i++) { // max 10 sessions
            fallSession = (minYear + i).toString() + "9";
            winterSession = (minYear + i + 1).toString() + "1";
            yearArray.push({
                "fallSession": fallSession,
                "winterSession": winterSession
            });
            if (!(courseTable.hasOwnProperty(fallSession)))
                courseTable[fallSession] = [];
            if (!(courseTable.hasOwnProperty(winterSession)))
                courseTable[winterSession] = [];
        }
    };

    this.processCourseTable = function(courseTable, courseArrange, mainAreas, yearArray) {
        bindElectiveFields(courseTable, courseArrange);
        bindMainFields(courseTable, mainAreas);
        completeSessionList(courseTable, yearArray);
        return courseTable;
    }

    this.processCEAB = function(CEABRequirement) {
        let processedCEAB = [];
        for (const category in CEABRequirement) {
            if (CEABRequirement.hasOwnProperty(category)) {
                let categoryObject = {};
                categoryObject['categoryName'] = category;
                let currentCategory = CEABRequirement[category];
                if (currentCategory.outstanding === "OK") {
                    categoryObject['satisfied'] = true;
                    categoryObject['relativeAU'] = (parseFloat(currentCategory.projected) - parseFloat(currentCategory.minRequirement)).toFixed(1);
                } else {
                    categoryObject['satisfied'] = false;
                    categoryObject['relativeAU'] = -1 * parseFloat(currentCategory.outstanding).toFixed(1);
                }
                processedCEAB.push(categoryObject);
            }
        }
        processedCEAB.sort((categoryObjectA, categoryObjectB) => {
            return categoryObjectA.categoryName.localeCompare(categoryObjectB.categoryName);
        });
        return processedCEAB;
    }

    this.processCourseArrange = function(courseArrange) {
        let processedCourseArrange = [];
        for (const category in courseArrange) {
            if (courseArrange.hasOwnProperty(category)) {
                let categoryObject = {};
                categoryObject["categoryName"] = category;
                categoryObject["courseList"] = [];
                pattern = /^(\w{3}\d{3}[YH]1(?:\s*\((?:CS|HSS)\))?)$/;
                courseArrange[category].forEach((course) => {
                    if (course.match(pattern) != null) {
                        categoryObject["courseList"].push({
                            "satisfied": true,
                            "courseName": course
                        });
                    } else {
                        // handle ECE472H1N
                        if (course.endsWith("N")) {
                            course = course.slice(0, 8);
                        }
                        categoryObject["courseList"].push({
                            "satisfied": false,
                            "courseName": course
                        });
                    }
                });
                processedCourseArrange.push(categoryObject);
            }
        }
        processedCourseArrange.sort((categoryObjectA, categoryObjectB) => {
            return categoryObjectA.categoryName.localeCompare(categoryObjectB.categoryName);
        });
        return processedCourseArrange;
    }

});
