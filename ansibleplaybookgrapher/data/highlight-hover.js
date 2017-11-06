const HOVER_CLASS = "my_hover";

function recursiveAddClass(rootElement) {
    $(rootElement).find('link').each(function (index, element) {
        var target = $(element).attr('target');
        var currentElement = $('#' + target);
        currentElement.addClass(HOVER_CLASS);

        recursiveAddClass(currentElement);
    })
}

function recursiveRemoveClass(rootElement) {
    $(rootElement).find('link').each(function (index, element) {
        var target = $(element).attr('target');
        var currentElement = $('#' + target);
        currentElement.removeClass(HOVER_CLASS);

        recursiveRemoveClass(currentElement);
    })
}

function hoverIn(event) {
    recursiveAddClass(event.currentTarget);
}

function hoverOut(event) {
    recursiveRemoveClass(event.currentTarget);
}


$("#svg").ready(function () {
    var svg = Snap("#svg");

    //svg.circle(150, 150, 100);

    // each play
    $("g[id^=play_]").hover(hoverIn, hoverOut);
    $("g[id^=role_]").hover(hoverIn, hoverOut);

});
