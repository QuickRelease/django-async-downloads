const url = $("#downloads_script").data("url");
const clearUrl = $("#downloads_script").data("clear-url");

function updateDownloads() {
    $.ajax({
        method: "GET",
        url: url,
    }).done(function (response) {
        $("#downloads .dropdown-menu").html(response.html);
        if (response.in_progress) {
            $("#downloads").addClass("in-progress");
            setTimeout(updateDownloads, 1000);
        }
        else {
            $("#downloads").removeClass("in-progress");
        }
    });
}

function clearDownload(filepath) {
    $.ajax({
        method: "POST",
        url: clearUrl,
        data: {filepath: filepath},
    }).done(function (response) {
        updateDownloads();
    });
}

$(function () {
    updateDownloads();
});
