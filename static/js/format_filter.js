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

angular.module('NeoMagellan').filter('auCategoryFormat', function(){
    return function(categoryName){
        let abbrName = '';
        wordList = categoryName.split(' ');
        wordList.forEach((word) => {
            if(word.startsWith("Total")){
                abbrName += "Total ";
            } else if(word.startsWith("Math")){
                abbrName += "Math";
            } else if(word === "and"){
                abbrName += " & ";
            } else if(word !== "Combined"){
                abbrName += word.charAt(0);
            }
        });
        return abbrName;
    }
});
