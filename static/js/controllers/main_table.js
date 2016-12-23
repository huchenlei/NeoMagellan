angular.module('CourseTable').controller('mainTable', ($scope, $http) => {
    // mocking getting profile info from server
    $http.get('/test_profile').then((response) => {
        $scope.courseTable = response.data["course_table"];
        $scope.CEAB_requirement = response.data["CEAB_requirement"];
    }, (response) => {
        alert("something wrong getting profile");
    })
})
