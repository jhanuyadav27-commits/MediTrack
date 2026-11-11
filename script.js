// MEDI TRACK - SIDEBAR NAVIGATION
const menuBtn = document.getElementById("menuBtn");
const closeBtn = document.getElementById("closeBtn");
const sidebar = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebarOverlay");

function openSidebar() {
    sidebar.classList.add("open");
    sidebarOverlay.classList.add("visible");

    menuBtn.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
}

function closeSidebar() {
    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("visible");

    menuBtn.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
}

if (menuBtn) {
    menuBtn.addEventListener("click", openSidebar);
}

if (closeBtn) {
    closeBtn.addEventListener("click", closeSidebar);
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener("click", closeSidebar);
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        closeSidebar();
    }
});

console.log("MediTrack sidebar initialized successfully.");
document.addEventListener("DOMContentLoaded", function () {
const profileBtn = document.getElementById("profileBtn");
const profileDropdown = document.getElementById("profileDropdown");


if (!profileBtn || !profileDropdown) {
    return;
}

profileBtn.addEventListener("click", function (event) {
    event.stopPropagation();

    profileDropdown.hidden = !profileDropdown.hidden;

    profileBtn.setAttribute(
        "aria-expanded",
        String(!profileDropdown.hidden)
    );
});

document.addEventListener("click", function (event) {
    if (
        !profileBtn.contains(event.target) &&
        !profileDropdown.contains(event.target)
    ) {
        profileDropdown.hidden = true;
        profileBtn.setAttribute("aria-expanded", "false");
    }
});

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        profileDropdown.hidden = true;
        profileBtn.setAttribute("aria-expanded", "false");
    }
});


});
