// navigator controller
angular.module('CourseTable').controller('navigator', ($scope, $http) => {
    $http.get('course_list').then((response) => {
        $scope.mainAreas = response.data["main"];
        $scope.elecAreas = response.data["elective"];
    }, (response) => {
        alert("something wrong getting course list");
    })
})
