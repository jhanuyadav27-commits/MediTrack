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

// MEDI TRACK - DASHBOARD FILTERS
document.addEventListener("DOMContentLoaded", function () {

    const periodFilter = document.getElementById("periodFilter");
    const departmentFilter = document.getElementById("departmentFilter");

    // Run only on the dashboard page
    if (!periodFilter || !departmentFilter) {
        return;
    }

    const customDateRange = document.getElementById("customDateRange");
    const startDate = document.getElementById("startDate");
    const endDate = document.getElementById("endDate");

    const applyButton = document.getElementById("applyFilters");
    const resetButton = document.getElementById("resetFilters");
    const filterStatus = document.getElementById("filterStatus");

    const chartElements = {
        department: document.getElementById("departmentChart"),
        monthly: document.getElementById("monthlyChart"),
        age: document.getElementById("ageChart"),
        visit_type: document.getElementById("visitTypeChart"),
        daily: document.getElementById("dailyChart")
    };

    let activeController = null;

    // Show or hide custom date inputs
    periodFilter.addEventListener("change", function () {

        customDateRange.hidden = periodFilter.value !== "custom";

    });

    // Load filtered charts
    async function updateDashboard(showStatus = true) {

        const period = periodFilter.value;
        const department = departmentFilter.value;

        const params = new URLSearchParams();

        params.append("period", period);
        params.append("department", department);

        // Validate custom dates
        if (period === "custom") {

            if (!startDate.value || !endDate.value) {
                filterStatus.textContent =
                    "Please select both start and end dates.";
                return;
            }

            if (startDate.value > endDate.value) {
                filterStatus.textContent =
                    "Start date cannot be after end date.";
                return;
            }

            params.append("start_date", startDate.value);
            params.append("end_date", endDate.value);
        }

        // Cancel an earlier request if one is still running
        if (activeController) {
            activeController.abort();
        }

        activeController = new AbortController();

        if (showStatus) {
            filterStatus.textContent = "Updating charts...";
        }

        Object.values(chartElements).forEach(function (chart) {
            chart.classList.add("chart-loading");
        });

        try {

            const response = await fetch(
                "/api/dashboard-charts?" + params.toString(),
                {
                    method: "GET",
                    signal: activeController.signal
                }
            );

            const result = await response.json();
            console.log("Dashboard API response:", result);

            if (!response.ok) {
                throw new Error(
                    result.error || "Unable to update charts."
                );
            }

            // Update all five charts
            Object.keys(chartElements).forEach(function (key) {

                chartElements[key].src = result.charts[key];

            });

            if (showStatus) {
                filterStatus.textContent =
                    "Charts updated successfully. " +
                    result.filtered_visits + " visits found.";
            }

        } catch (error) {

            if (error.name === "AbortError") {
                return;
            }

            console.error("Dashboard error:", error);

            filterStatus.textContent =
                error.message || "Something went wrong.";

        } finally {

            Object.values(chartElements).forEach(function (chart) {
                chart.classList.remove("chart-loading");
            });

        }
    }

    // Apply filters button
    applyButton.addEventListener("click", updateDashboard);

    // Reset filters
    resetButton.addEventListener("click", function () {

        periodFilter.value = "3m";
        departmentFilter.value = "all";

        startDate.value = "";
        endDate.value = "";

        customDateRange.hidden = true;

        updateDashboard();

    });

    // Load default dashboard charts
    updateDashboard(false);

});


