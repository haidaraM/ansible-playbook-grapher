const HOVER_CLASS = "my_hover";

function hoverInPlay(event) {
    $(event.currentTarget).find('link').each(function (index, element) {
        var target = $(element).attr('target');
        $('#' + target).addClass(HOVER_CLASS);
    })
}

function hoverOutPlay(event) {
    $(event.currentTarget).find('link').each(function (index, element) {
        var target = $(element).attr('target');
        $('#' + target).removeClass(HOVER_CLASS);
    })
}

$("#svg").ready(function () {
    var svg = Snap("#svg");

    //svg.circle(150, 150, 100);

    // each play
    $("g[id^=play_]").hover(hoverInPlay, hoverOutPlay);
    $("g[id^=role_]").hover(hoverInPlay, hoverOutPlay);

});
