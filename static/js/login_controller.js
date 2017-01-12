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

    $scope.getSharedProfileList = function(pageNumber){
        $http.get('/shared_profile_list/' + pageNumber).then(
            (response) => {
                console.log(response.data);
                $scope.sharedProfileList = response.data;
            },
            (response) => {
                alert("something wrong with shared profile list");
            }
        );
    };
});
