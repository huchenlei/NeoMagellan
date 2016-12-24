angular.module('CourseTable').controller('mainTable', ($scope, $http) => {
    // mocking getting profile info from server
    $http.get('/test_profile').then(
        (response) => {
        $scope.courseTable = response.data["courseTable"];
        $scope.CEAB_requirement = response.data["CEABRequirement"];
        },
        (response) => {
        alert("something wrong getting profile");
        }
    )
})
