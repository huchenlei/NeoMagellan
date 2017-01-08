angular.module('NeoMagellan').controller('courseSelect', ($scope, $http, courseTableService) => {
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

    function processUserInfo(response) {
        $scope.yearArray = [];
        $scope.courseTable = courseTableService.processCourseTable(response.data['courseTable'], response.data['courseArrange'], $scope.mainAreas, $scope.yearArray);
        $scope.courseArrange = courseTableService.processCourseArrange(response.data['courseArrange']);
        $scope.CEABRequirement = courseTableService.processCEAB(response.data['CEABRequirement']);
        if (response.data.hasOwnProperty('prerequisiteErrors')) {
            $scope.hasPrerequisiteError = true;
            $scope.prerequisiteErrors = response.data['prerequisiteErrors'];
        } else {
            $scope.hasPrerequisiteError = false;
        }
        $scope.personalInfo = response.data['personalInfo'];
    }

    function getProfile() {
        // mocking getting profile info from server
        $http.get('/test_profile').then( // TODO change back to /profile
            processUserInfo,
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

    function updateRequirementPanel(response) {
        if (response.hasOwnProperty('errorMessage')) {
            $scope.message = response.data["errorMessage"];
            $scope.messageType = "error";
            $scope.displayMessage = true;
        } else {
            $scope.courseArrange = courseTableService.processCourseArrange(response.data['courseArrange']);
            $scope.CEABRequirement = courseTableService.processCEAB(response.data['CEABRequirement']);
            if (response.data.hasOwnProperty('prerequisiteErrors')) {
                $scope.hasPrerequisiteError = true;
                $scope.prerequisiteErrors = response.data['prerequisiteErrors'];
            } else {
                $scope.hasPrerequisiteError = false;
            }
        }
    }

    $scope.checkProfile = function() {
        $http.post('/check_profile', buildPayload()).then(nupdateRequirementPanel, serverError);
    }

    $scope.submitProfile = function() {
        $('#submit-modal').modal('open');
    }

    $scope.shareOptions = {
        "share": false,
        "anonymous": false,
        "description": ""
    }
    $scope.shareProfile = function() {
        const payload = {
            "payload": buildPayload(),
            "shareOptions": $scope.shareOptions,
            "personalInfo": $scope.personalInfo
        };
        $http.post('/submit_profile', payload).then(
            (response) => {
                updateRequirementPanel(response);
                if (response.data['status'] === "200") {
                    $scope.message = "Submit is successful";
                    $scope.messageType = "success";
                    $scope.displayMessage = true;
                }
                $('#submit-modal').modal('close');
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
