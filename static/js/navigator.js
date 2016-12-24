// navigator controller
angular.module('CourseTable').controller('navigator', ($scope, $http) => {
    $http.get('course_list').then((response) => {
        $scope.mainAreas = response.data["main"];
        $scope.elecAreas = response.data["elective"];
    }, (response) => {
        alert("something wrong getting course list");
    })
    $scope.getCourseDetail = function(courseCode, courseLength) {
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
})
