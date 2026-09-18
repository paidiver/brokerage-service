document.addEventListener("DOMContentLoaded", function () {
    var links = Array.prototype.slice.call(
        document.querySelectorAll(".bd-links a.reference.internal")
    );

    var repoLink = links.find(function (a) {
        var text = (a.textContent || "").trim();
        var href = a.getAttribute("href") || "";
        return text === "Repository Docs" || href.indexOf("/repos/index") !== -1;
    });

    if (!repoLink) {
        return;
    }

    var repoLi = repoLink.closest("li");
    if (!repoLi) {
        return;
    }

    var details = repoLi.querySelectorAll("details");
    details.forEach(function (node) {
        node.open = true;
    });
});
