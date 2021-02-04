const url = $("#async-downloads-script").data("url");
const clearUrl = $("#async-downloads-script").data("clear-url");

function updateDownloads() {
    // Do nothing if the downloads div doesn't exist
    if ($("#async-downloads").length === 0) return;
    $.ajax({
        method: "GET",
        url: url,
    }).done(function (response) {
        $("#async-downloads .dropdown-menu").html(response.html);
        if (response.in_progress) {
            $("#async-downloads").addClass("in-progress");
            setTimeout(updateDownloads, 1000);
        }
        else {
            $("#async-downloads").removeClass("in-progress");
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
