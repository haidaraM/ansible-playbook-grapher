const HOVER_CLASS = "my_hover";

function addClass(rootElement) {
    $(rootElement).find('link').each(function (index, element) {
        var target = $(element).attr('target');
        var currentElement = $('#' + target);
        currentElement.addClass(HOVER_CLASS);

        addClass(currentElement);
    })
}

function removeClass(rootElement) {
    $(rootElement).find('link').each(function (index, element) {
        var target = $(element).attr('target');
        var currentElement = $('#' + target);
        currentElement.removeClass(HOVER_CLASS);

        removeClass(currentElement);
    })
}

function hoverIn(event) {
    addClass(event.currentTarget);
}

function hoverOut(event) {
    removeClass(event.currentTarget);
}


$("#svg").ready(function () {
    var svg = Snap("#svg");

    //svg.circle(150, 150, 100);

    $("g[id^=play_]").hover(hoverIn, hoverOut);
    $("g[id^=role_]").hover(hoverIn, hoverOut);

});
