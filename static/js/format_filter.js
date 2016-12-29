angular.module('NeoMagellan').filter('sessionFormat', function(){
    return function(rawSessionString){
        return rawSessionString.slice(0, 4) + "." + rawSessionString.slice(4, 5);
    }
});

angular.module('NeoMagellan').filter('idFormat', function(){
    return function(index, prefix){
        return prefix.replace(/\s|&|\//g, '') + index.toString();
    }
});
