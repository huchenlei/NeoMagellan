angular.module('NeoMagellan').controller('courseSelect', ($scope, $http) => {
    // initialize the navi bar(course database)
    // may lazy load the electives for speed
    $http.get('/course_list').then((response) => {
        $scope.mainAreas = response.data["main"];
        $scope.elecAreas = response.data["elective"];
    }, (response) => {
        alert("something wrong getting course list");
    })

    function processCourseTable(response) {
        let courseTable = response.data["courseTable"];
        let courseArrange = response.data["courseArrange"];
        courseArrange['HSS and CS'].forEach((elective) => {
            courseCode = elective.split(' ')[0];
            courseCategory = elective.split(' ')[1];
            // find the course in courseTable
            // and inject 'courseCategory' field
            for (const year of Object.keys(courseTable)) {
                courseTable[year].forEach((course) => {
                    if ((course.courseCode + course.courseLength) === courseCode) {
                        course['courseCategory'] = courseCategory;
                    }
                });
            }
        });
        $scope.courseTable = courseTable;
    }

    // mocking getting profile info from server
    $http.get('/test_profile').then(
        processCourseTable,
        (response) => {
            alert("something wrong getting profile");
        }
    )


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



})
