document.addEventListener("DOMContentLoaded", function () {

    const checkbox = document.getElementById("guidelineCheck");
    const startBtn = document.getElementById("startExamBtn");
    const modal    = document.getElementById("guidelinesModal");

    if (!checkbox || !startBtn) return;

    checkbox.addEventListener("change", function () {
        startBtn.disabled = !this.checked;
    });

    startBtn.addEventListener("click", async function () {

        startBtn.disabled = true;

        // 1. Enter fullscreen — MUST happen inside this click gesture
        try {
            await document.documentElement.requestFullscreen();
        } catch (err) {
            console.error(err);
            alert("Full screen is required to start the test. Please allow full screen and try again.");
            startBtn.disabled = false;
            return;
        }

        // 2. Tell the server the exam has started
        let data;
        try {
            const response = await fetch(window.examConfig.startExamUrl, {
                method: "GET",
                credentials: "same-origin"
            });
            data = await response.json();
        } catch (err) {
            console.error(err);
            alert("Could not start the test. Please check your connection and try again.");
            startBtn.disabled = false;
            if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
            return;
        }

        if (!data || !data.success) {
            alert((data && data.message) || "Unable to start the test.");
            startBtn.disabled = false;
            if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
            return;
        }

        // 3. Hide the guidelines modal (NO reload)
        if (modal) modal.style.display = "none";

        // 4. Start timer + proctoring using the end time from the server
        if (typeof window.beginExamRuntime === "function") {
            window.beginExamRuntime(data.exam_end_time);
        }
    });
});