const url = $("#async-downloads-script").data("url");

function readablePeriod(timeStamp) {
    //determine the timezone offset the browser applies to Date()
    const offset = new Date().getTimezoneOffset() * 60000;

    const diff = Date.now() - Date.parse(timeStamp) + offset;
    function suffix(number) {
        return (number > 1 ? "s" : "") + " ago";
    }
    let temp = diff / 1000;
    const years = Math.floor(temp / 31536000);
    if (years) return years + " year" + suffix(years);
    const days = Math.floor((temp %= 31536000) / 86400);
    if (days) return days + " day" + suffix(days);
    const hours = Math.floor((temp %= 86400) / 3600);
    if (hours) return hours + " hour" + suffix(hours);
    const minutes = Math.floor((temp %= 3600) / 60);
    if (minutes) return minutes + " minute" + suffix(minutes);
    const seconds = Math.floor(temp % 60);
    if (seconds) return seconds + " second" + suffix(seconds);
    return "now";
}

function calculateTimeStamps() {
    $(".download-timestamp").each(function () {
        const timeStamp = $(this).attr("value");
        $(this).text(readablePeriod(timeStamp));
    });
}
function refreshDownloads() {
    // Do nothing if the downloads div doesn't exist
    if ($("#async-downloads").length === 0) return;
    $.ajax({
        method: "GET",
        url: url,
    }).done(function (response) {
        $("#async-downloads .dropdown-menu").html(response.html);
        calculateTimeStamps();
    });
}

function initDownload(data) {
    const dropdown = $("#downloads-dropdown");
    // remove 'No downloads' msg if exists in dropdown
    dropdown.find("a").remove();
    const download = data.download;
    const download_div = `
    <div id="${data.downloadKey}" class="ws-download-container" data-url="${download.url}"
        data-filepath="${download.filepath}">
        <div class="ws-product-label background-color-${download.product}"></div>
        <div class="download-content">
            <div class="download">
                <span class="download-name">${download.name}</span>
                <span class="download-timestamp" value="${download.timestamp}">now</span>
            </div>
            <span class="download-clear"><i class="fa fa-times-circle"></i></span>

            <div class="progress" style="height: 4px;">
                <div class="progress-bar progress-bar-striped bg-info progress-bar-animated" role="progressbar"
                    style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        </div>
    </div>
    `;
    dropdown.prepend(download_div);
}

function updateDownload(data) {
    const download_div = $(`#${data.downloadKey}`);
    const download = data.download;
    const bar = download_div.find(".progress-bar");
    download_div.attr("data-url", download.url);
    bar.attr({
        style: `width: ${download.percentage}%`,
        "aria-valuenow": download.percentage,
    });
    if (download.complete) {
        bar.addClass("bg-success");
        bar.removeClass("bg-info progress-bar-animated");
    }
    if (download.errors) {
        bar.addClass("bg-danger");
        bar.removeClass("bg-success");
        download_div.attr({
            "data-toggle": "tooltip",
            "data-placement": "bottom",
            title: download.errors,
        });
        $("#async-downloads [data-toggle='tooltip']").tooltip();
    }
}
function removeDownload(data) {
    $(`#${data.downloadKey}`).remove();
    if ($("#downloads-dropdown > div").length === 0)
        $("#downloads-dropdown").append(
            '<a class="dropdown-item" href="">No downloads</a>'
        );
}

function startDownloadSocket() {
    const master_stripped_url = JSON.parse(
        document.getElementById("MASTER_URL").textContent
    ).replace(/(^\w+:|^)\/\//, "");
    const username = JSON.parse(
        document.getElementById("username").textContent
    );
    const ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";

    const ws = new WebSocket(
        `${ws_scheme}://${master_stripped_url}/ws/downloads/${username}/`
    );

    function requestDownloadUpdate(data) {
        setTimeout(function () {
            const downloadKey = data.downloadKey;
            if (!data.download.complete) {
                ws.send(
                    JSON.stringify({
                        eventType: "getDownload",
                        location: window.location.host,
                        downloadKey: downloadKey,
                    })
                );
            }
        }, 1000);
    }
    ws.onopen = function (e) {
        // clear btn for download
        $(document).on("click", ".download-clear", function (e) {
            e.stopPropagation();
            ws.send(
                JSON.stringify({
                    eventType: "clearDownload",
                    location: window.location.host,
                    data: {
                        filepath: $(this)
                            .closest(".download-content")
                            .closest(".ws-download-container")
                            .data("filepath"),
                    },
                })
            );
        });
        setInterval(function () {
            $(".download-timestamp").each(function () {
                const timeStamp = $(this).attr("value");
                $(this).text(readablePeriod(timeStamp));
            });
        }, 1000);
    };

    ws.onmessage = function (e) {
        // Do nothing if the downloads div doesn't exist
        if ($("#async-downloads").length === 0) return;
        const msg = JSON.parse(e.data);
        switch (msg.eventType) {
            case "refreshDownloads":
                refreshDownloads();
                break;
            case "updateDownload":
                updateDownload(msg.data);
                requestDownloadUpdate(msg.data);
                break;
            case "removeDownload":
                removeDownload(msg.data);
                break;
            case "initDownload":
                initDownload(msg.data);
                requestDownloadUpdate(msg.data);
                break;
        }
    };

    ws.onclose = function (e) {
        console.log(
            "DownloadSocket is closed. Reconnect will be attempted in 5 second.",
            e.reason
        );
        setTimeout(function () {
            startDownloadSocket();
        }, 5000);
    };

    ws.onerror = function (err) {
        console.error(
            "DownloadSocket encountered error: ",
            err.message,
            "Closing socket"
        );
        ws.close();
    };
}

$(function () {
    refreshDownloads();
    startDownloadSocket();
});
