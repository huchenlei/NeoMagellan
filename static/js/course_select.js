angular.module('NeoMagellan').controller('courseSelect', ($scope, $http) => {
    // initialize the navi bar(course database)
    // may lazy load the electives for speed
    $http.get('/course_list').then((response) => {
        $scope.mainAreas = response.data["main"];
        $scope.elecAreas = response.data["elective"];
        getProfile();
    }, (response) => {
        alert("something wrong getting course list");
    })

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
                                    course['courseId'] = mainCourse.courseId;
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
        $scope.courseTable = courseTable;
    }

    function getProfile() {
        // mocking getting profile info from server
        $http.get('/test_profile').then(
            processCourseTable,
            (response) => {
                alert("something wrong getting profile");
            }
        )
    }

    // initialize courseDetail
    $scope.courseDetail = {
        "courseCode": null
    };
    $scope.getCourseDetail = function(courseCode, courseLength) {
        // only request the server if there is a change in course code
        if (!(courseCode === $scope.courseDetail.courseCode)) {
            $http.get('/course_detail/' + courseCode + courseLength).then(
                (response) => {
                    if (response.data['status'] === '500') {
                        alert(response.data['errorMessage']);
                    } else {
                        $scope.courseDetail = response.data;
                        console.log(response.data);
                    }
                },
                (response) => {
                    alert("something wrong getting course detail");
                }
            )
        }
    }

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
                } else if (course.courseCode === 'ECE472'){
                    // ECE 472 Engineering Economics
                    payload['dd_ECE472H1_'] = year;
                } else if (['ECE496', 'APS490', 'BME498'].includes(course.courseCode)){
                    // Design Project(Capstone)
                    console.log("designing project");
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
                $scope.courseArrange = response.data["courseArrange"];
                // TODO more fields
            },
            (response) => {
                alert('something wrong checking profile');
            }
        );
    }

    $scope.submitProfile = function() {
        $http.post('/submit_profile', buildPayload()).then(
            (response) => {
                if(response.data["status"] === "200")
                    console.log("Submit SUCCESS");
            },
            (response) => {
                alert('something wrong submitting profile');
            }
        );
    }
});
