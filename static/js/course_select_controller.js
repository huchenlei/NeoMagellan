angular.module('NeoMagellan').controller('courseSelect', ($scope, $http) => {
    // initialize the navi bar course list
    $http.get('/course_list/main').then(
        (response) => {
            $scope.mainAreas = response.data;
            getProfile();
            // initialize tabs after everything got initailized
            $(document).ready(function() {
                $('ul.tabs').tabs();
            });
            // make modals operate
            $(document).ready(function() {
                $('.modal').modal();
            });
        }, serverError
    );

    // lazy load the elective course list
    let fuse;
    $scope.elecAreas = [];
    $scope.displayPreloader = true;
    $scope.getElecAreas = function() {
        $http.get('/course_list/elective').then(
            (response) => {
                $scope.elecAreas = response.data;
                $scope.displayPreloader = false;
                fuse = new Fuse($scope.elecAreas, config);
            }, serverError
        );
    };

    // sarch bar
    const config = {
        shouldSort: true,
        threshold: 0.6,
        maxPatternLength: 15,
        minMatchCharLength: 3,
        keys: [
            "courseName",
            "courseCode"
        ]
    };
    // fuse would be initialized when elec list is loaded
    $scope.searchResult = [];
    $scope.searchKeyword = ""
    $scope.searchElec = function() {
        $scope.searchResult = fuse.search($scope.searchKeyword);
        $scope.displayFullElecList = ($scope.searchKeyword.length === 0);
    };
    $scope.displayFullElecList = true;

    //initialize profile
    function processCourseTable(response) {
        let courseTable = response.data["courseTable"];
        let courseArrange = response.data["courseArrange"];
        // bind CS HSS field
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
        // bind Course id field
        for (const year of Object.keys(courseTable)) {
            courseTable[year].forEach((course) => {
                let BreakException = {};
                try {
                    $scope.mainAreas.forEach((mainArea) => {
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

        // complete the year options
        // find the min session sessions are in form (e.g. 20159, 20161)
        let minYear = null;
        // build a year array for the convenience of course table display
        // in the form (e.g. [{"fallSession": "20159", "winterSession": "20161"} ...])
        yearArray = [];
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

        $scope.courseTable = courseTable;
        $scope.courseArrange = processCourseArrange(response.data['courseArrange']);
        $scope.CEABRequirement = processCEAB(response.data['CEABRequirement']);
        if (response.data.hasOwnProperty('prerequisiteErrors')) {
            $scope.hasPrerequisiteError = true;
            $scope.prerequisiteErrors = response.data['prerequisiteErrors'];
        } else {
            $scope.hasPrerequisiteError = false;
        }
        $scope.yearArray = yearArray;
    }

    function processCEAB(CEABRequirement) {
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

    function processCourseArrange(courseArrange) {
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

    function getProfile() {
        // mocking getting profile info from server
        $http.get('/profile').then(
            processCourseTable,
            serverError
        )
    }

    // course detail search
    // initialize courseDetail
    $scope.courseDetail = {
        "courseCode": null
    };
    const errorCourseDetail = {
        "courseCode": "Error",
        "courseName": "The course detail is not available on Magellan",
        "auInfo": {
            "Math": "N/A",
            "NS": "N/A",
            "CS": "N/A",
            "ES": "N/A",
            "ED": "N/A",
            "Total": "N/A"
        },
        "prerequisites": "N/A",
        "exclusions": "N/A",
        "coRequisites": "N/A"
    };
    $scope.getCourseDetail = function(courseCode, courseLength) {
        // only request the server if there is a change in course code
        if (!(courseCode === $scope.courseDetail.courseCode)) {
            $http.get('/course_detail/' + courseCode + courseLength).then(
                (response) => {
                    if (response.data['status'] === '500') {
                        $scope.courseDetail = errorCourseDetail;
                    } else {
                        $scope.courseDetail = response.data;
                    }
                },
                (response) => {
                    $scope.courseDetail = errorCourseDetail;
                }
            )
        }
    }

    // submitting and checking profile
    function buildPayload() {
        let payload = {};
        let electiveIndex = 1;
        for (const year of Object.keys($scope.courseTable)) {
            $scope.courseTable[year].forEach((course) => {
                if (course.hasOwnProperty('courseId')) {
                    // main Course
                    payload[course.courseId] = year;
                } else if (course.hasOwnProperty('courseCategory')) {
                    // elective
                    prefix = 'course_hss_cs_' + electiveIndex;
                    payload[prefix] = course.courseCode + course.courseLength;
                    payload['dd_' + prefix + '_session_cd_'] = year;
                    electiveIndex++;
                } else if (course.courseCode === 'ECE472') {
                    // ECE 472 Engineering Economics
                    payload['dd_ECE472H1_'] = year;
                } else if (['ECE496', 'APS490', 'BME498'].includes(course.courseCode)) {
                    // Design Project(Capstone)
                    payload['capstone_type'] = course.courseCode + course.courseLength;
                    payload['dd_capstone_'] = year;
                }
                // TODO technical elective
                // TODO free elective
            });
        }
        return payload;
    }

    $scope.checkProfile = function() {
        $http.post('/check_profile', buildPayload()).then(
            (response) => {
                if (response.hasOwnProperty('errorMessage')) {
                    $scope.message = response.data["errorMessage"];
                    $scope.messageType = "error";
                } else {
                    $scope.courseArrange = processCourseArrange(response.data['courseArrange']);
                    $scope.CEABRequirement = processCEAB(response.data['CEABRequirement']);
                    if (response.data.hasOwnProperty('prerequisiteErrors')) {
                        $scope.hasPrerequisiteError = true;
                        $scope.prerequisiteErrors = response.data['prerequisiteErrors'];
                    } else {
                        $scope.hasPrerequisiteError = false;
                    }
                }
            }, serverError
        );
    }

    $scope.submitProfile = function() {
        $http.post('/submit_profile', buildPayload()).then(
            (response) => {
                if (response.data["status"] === "200") {
                    $scope.message = "Submit Success";
                    $scope.messageType = "success";
                } else if (response.data["status"] === "500") {
                    $scope.message = response.data["errorMessage"];
                    $scope.messageType = "error";
                }
                $scope.displayMessage = true;
            }, serverError
        );
    }

    $scope.displayProgramRules = false;
    $scope.showProgramRules = function() {
        $scope.displayProgramRules = true;
    }
    $scope.hideProgramRules = function() {
        $scope.displayProgramRules = false;
    }

    $scope.displayTrashCan = false;
    $scope.showTrashCan = function() {
        $scope.displayTrashCan = true;
    }
    $scope.hideTrashCan = function() {
        $scope.displayTrashCan = false;
    }

    $scope.displayMessage = false;
    $scope.message = "";
    $scope.hideMessage = function() {
        $scope.displayMessage = false;
    }

    function serverError(response) {
        $scope.message = "Opps! something might be wrong with the server";
        $scope.messageType = "error";
        $scope.displayMessage = true;
    }
});
