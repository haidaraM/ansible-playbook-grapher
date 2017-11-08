const HOVER_CLASS = "my_hover";

var selectedElement = null;

function addClass(rootElement) {
    $(rootElement).find('link').each(function (index, element) {
        var target = $(element).attr('target');
        var currentElement = $('#' + target);
        currentElement.addClass(HOVER_CLASS);

        addClass(currentElement);
    })
}

function removeClass(rootElement, hover) {
    $(rootElement).find('link').each(function (index, element) {
        if ($(rootElement).attr('id') !== $(selectedElement).attr('id') || !hover) {
            var target = $(element).attr('target');
            var currentElement = $('#' + target);
            currentElement.removeClass(HOVER_CLASS);

            removeClass(currentElement);
        }

    })
}

function hoverIn(event) {
    addClass(event.currentTarget);
}

function hoverOut(event) {
    removeClass(event.currentTarget, true);
}

function clickOnElement(event) {
    var newElement = event.currentTarget;

    if ($(newElement).attr('id') === $(selectedElement).attr('id')) {
        removeClass(selectedElement, false);
    } else {
        removeClass(selectedElement);
        addClass(newElement)
    }

    selectedElement = newElement;
}


$("#svg").ready(function () {

    $("g[id^=play_]").hover(hoverIn, hoverOut);
    $("g[id^=role_]").hover(hoverIn, hoverOut);

    $("g[id^=play_]").click(clickOnElement);
    $("g[id^=role_]").click(clickOnElement);

});
