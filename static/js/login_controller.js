angular.module('NeoMagellanLogin').controller('login', ($scope, $http) => {
    // initialize everything
    $scope.readyToSelectProfile = false;
    $scope.errorMessage = null;


    $scope.getProfileList = function() {
        $http({
            method: 'POST',
            url: '/profile_list',
            data: {
                "username": $scope.username,
                "password": $scope.password
            },
            headers: {
                'Content-Type': "application/json"
            }
        }).then((response) => {
            if (response.data["status"] === "200") {
                $scope.profileList = response.data["profileList"];
                $scope.readyToSelectProfile = true;
            } else if (response.data["status"] === "500") {
                $scope.errorMessage = response.data["errorMessage"];
            }
        }, (response) => {
            $scope.errorMessage = "Opps! something unexpected happended!";
        })
    };
    $scope.newProfile = function() {
        console.log("creating new profile");
        $http.post('/course_select', {
            "profileName": "TestNew",
            "newProfile": "true"
        }).then((response) => {
            $location.path('/course_select')
        }, (response) => {
            console.log("something wrong");
        });
    };
});
