$(function () {
    function readablePeriod(timeStamp) {
        // timeStamp should consist information about timezone
        const diff = Date.now() - Date.parse(timeStamp);
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

    function initAllDownloads(data) {
        $("#async-downloads .dropdown-menu").empty();
        data.forEach(function (dl) {
            initDownload(dl);
            updateDownload(dl);
        });
        if ($("#downloads-dropdown > div").length === 0) {
            $("#downloads-dropdown").append(
                '<a class="dropdown-item" href="">No downloads</a>'
            );
        }
    }

    function initDownload(data) {
        $("#async-downloads").addClass("in-progress");
        const dropdown = $("#downloads-dropdown");
        // remove 'No downloads' msg if exists in dropdown
        dropdown.find("a").remove();
        dropdown.prepend(data.download.html);
        calculateTimeStamps()
    }

    function updateDownload(data) {
        const download_div = $(`#download-${data.download_key}`);
        const download = data.download;
        const bar = download_div.find(".progress-bar");
        download_div.attr("data-url", download.url);
        bar.attr({
            style: `width: ${download.percentage}%`,
            "aria-valuenow": download.percentage,
        });
        if (download.complete) {
            download_div.attr("complete", "true");
            bar.addClass("bg-success");
            bar.removeClass("bg-info progress-bar-animated");
        }
        if (download.errors) {
            download_div.attr("complete", "true");
            bar.addClass("bg-danger");
            bar.removeClass("bg-success");
            download_div.attr({
                "data-toggle": "tooltip",
                "data-placement": "bottom",
                title: download.errors,
            });
            $("#async-downloads [data-toggle='tooltip']").tooltip();
        }

        if (!$('.download-container[complete="false"]').length) {
            $("#async-downloads").removeClass("in-progress");
        }
        calculateTimeStamps();
    }

    function removeDownload(data) {
        $(`#download-${data.download_key}`).remove();
        if ($("#downloads-dropdown > div").length === 0)
            $("#downloads-dropdown").append(
                '<a class="dropdown-item" href="">No downloads</a>'
            );
        if (!$('.download-container[complete="false"]').length) {
            $("#async-downloads").removeClass("in-progress");
        }
    }

    function startDownloadSocket() {
        const url = new URL($("#async-downloads-script").data("url"));
        url.protocol = url.protocol == "https:" ? "wss:" : "ws";
        const ws = new WebSocket(url);

        ws.onopen = function (e) {
            ws.send(
                JSON.stringify({
                    eventType: "initAllDownloads",
                    location: window.location.host,
                })
            );
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
                                .closest(".download-container")
                                .data("filepath"),
                        },
                    })
                );
            });
            setInterval(calculateTimeStamps, 1000);
        };

        ws.onmessage = function (e) {
            // Do nothing if the downloads div doesn't exist
            if ($("#async-downloads").length === 0) return;
            const msg = JSON.parse(e.data);
            switch (msg.eventType) {
                case "initAllDownloads":
                    initAllDownloads(msg.data);
                    break;
                case "updateDownload":
                    updateDownload(msg.data);
                    break;
                case "removeDownload":
                    removeDownload(msg.data);
                    break;
                case "initDownload":
                    initDownload(msg.data);
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

    startDownloadSocket();
});
