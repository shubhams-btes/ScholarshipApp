// =============================
// CONFIG
// =============================
if (!window.examConfig) {
    console.warn("examConfig not found");
} else {

const total = window.examConfig.totalQuestions;
let autoSubmitting = false;
let finalSubmission = false;
let examEndTime =
    new Date(window.examConfig.examEndTime).getTime();

let current = 1;

const attempted =
    Array(total + 1).fill(false);

const bookmarked =
    Array(total + 1).fill(false);




function updateTimer() {

    const now = Date.now();

    const remaining =
        Math.floor((examEndTime - now) / 1000);

    if (remaining <= 0) {

        document.getElementById("timer").textContent =
            "00:00";
        autoSubmitting = true;
        document.getElementById("exam-form").submit();

        return false;
    }

    const minutes =
        Math.floor(remaining / 60);

    const seconds =
        remaining % 60;

    document.getElementById("timer").textContent =
        String(minutes).padStart(2, "0") +
        ":" +
        String(seconds).padStart(2, "0");

    return true;
}

function startTimer() {

    // Display immediately
    if (!updateTimer()) return;

    const interval = setInterval(() => {

        if (!updateTimer()) {
            clearInterval(interval);
        }

    }, 1000);
}

// =============================
// PROCTORING (tab/window switch + fullscreen exit)
// =============================

let proctoringActive = false;
let violationCount    = 0;
let lastViolationAt   = 0;

const MAX_VIOLATIONS    = 3;    // 2 warnings, auto-submit on the 3rd
const VIOLATION_COOLDOWN = 1500; // ms — debounce so one action counts once

function autoSubmitExam() {
    autoSubmitting = true;
    const form = document.getElementById("exam-form");
    if (form) form.submit();
}

function triggerAutoSubmit() {

    // Block any further violation handling during the countdown.
    autoSubmitting = true;

    // Hide the resume overlay if it happens to be open.
    const resume = document.getElementById("resumeFullscreenModal");
    if (resume) resume.style.display = "none";

    const overlay = document.getElementById("autoSubmitModal");
    if (overlay) overlay.style.display = "flex";

    // Show the message for 5 seconds, then submit.
    setTimeout(function () {
        const form = document.getElementById("exam-form");
        if (form) form.submit();
    }, 5000);
}



function handleViolation(opts) {

    opts = opts || {};

    if (!proctoringActive || autoSubmitting || finalSubmission) return;

    const now = Date.now();
    if (now - lastViolationAt < VIOLATION_COOLDOWN) return; // debounce duplicate events
    lastViolationAt = now;

    violationCount++;

    if (violationCount >= MAX_VIOLATIONS) {
        triggerAutoSubmit();
        return;
    }

    if (opts.showResume) {
        // Left fullscreen (Esc/F11) → show the overlay so they can click back in.
        showResumeOverlay(violationCount);
    } else {
        // Tab switch / window blur → can't force them back, so just warn.
        showWarningDialog(violationCount);
        
    }
}

function onFullscreenChange() {
    const fsEl = document.fullscreenElement || document.webkitFullscreenElement;
    if (!fsEl) handleViolation({ showResume: true });
}

function startProctoring() {

    if (proctoringActive) return;
    proctoringActive = true;

    // Tab switch / minimize
    document.addEventListener("visibilitychange", function () {
        if (document.hidden) handleViolation();
    });

    // Switching to another app / window
    window.addEventListener("blur", handleViolation);

    // Pressing Esc / leaving fullscreen
    document.addEventListener("fullscreenchange", onFullscreenChange);
    document.addEventListener("webkitfullscreenchange", onFullscreenChange);
}

// Shows the resume overlay. warningNumber is optional (present on a live
// fullscreen-exit violation; absent on a plain reload resume).
function showResumeOverlay(warningNumber) {

    const overlay   = document.getElementById("resumeFullscreenModal");
    const resumeBtn = document.getElementById("resumeFullscreenBtn");

    if (!overlay || !resumeBtn) {
        if (warningNumber) {
            alert("Warning " + warningNumber + " of 2 — please return to full screen.");
        }
        return;
    }

    const textEl = document.getElementById("resumeText");
    if (textEl) {
        if (warningNumber) {
            textEl.innerHTML =
                "Warning <strong>" + warningNumber + "</strong> of 2 — you left full screen.<br><br>" +
                "The timer is still running. Return to full screen to continue. " +
                "One more violation will submit your test automatically.";
        } else {
            textEl.innerHTML =
                "Your test is still in progress and must be taken in full screen.<br><br>" +
                "The timer has kept running while you were away. Click below to return and continue.";
        }
    }

    overlay.style.display = "flex";
}

// Wire the resume button ONCE. It re-enters fullscreen, and then either starts
// the runtime (reload case) or just closes (live re-entry, runtime already going).
function wireResumeButton() {

    const resumeBtn = document.getElementById("resumeFullscreenBtn");
    if (!resumeBtn) return;

    resumeBtn.addEventListener("click", async function () {

        resumeBtn.disabled = true;

        try {
            await document.documentElement.requestFullscreen();
        } catch (err) {
            console.error(err);
            alert("Full screen is required to continue. Please allow full screen and try again.");
            resumeBtn.disabled = false;
            return;
        }

        const overlay = document.getElementById("resumeFullscreenModal");
        if (overlay) overlay.style.display = "none";
        resumeBtn.disabled = false;

        // Reload case → runtime not started yet, so start it now.
        // Live Esc case → proctoring/timer already running, nothing more to do.
        if (!proctoringActive) {
            beginExamRuntime(window.examConfig.examEndTime);
        }
    });
}

function showWarningDialog(warningNumber) {

    const modal = document.getElementById("warningModal");
    const textEl = document.getElementById("warningText");

    if (textEl) {
        textEl.innerHTML =
            "Warning <strong>" + warningNumber + "</strong> of 2<br><br>" +
            "Switching tabs or windows is not allowed during the test.<br><br>" +
            "One more violation will submit your test automatically.";
    }

    if (modal) {
        modal.style.display = "flex";
    }
}

// Called by exam_guidelines.js after start_exam succeeds,
// and on refresh if the exam is already in progress.
function beginExamRuntime(endTimeStr) {

    if (endTimeStr) {
        examEndTime = new Date(endTimeStr).getTime();
        window.examConfig.examEndTime = endTimeStr;
    }

    if (!isNaN(examEndTime) && examEndTime > 0) {
        startTimer();
    }

    startProctoring();
}

// =============================
// RESUME AFTER RELOAD
// =============================
// On a mid-exam reload, guidelines_accepted is already true (so the guidelines
// modal never renders) and examEndTime is populated. The browser will NOT let
// us re-enter fullscreen without a fresh user gesture, so we show a "return to
// fullscreen" overlay and only call beginExamRuntime after its button is clicked.

function resumeExamAfterReload() {

    // Deadline already passed → don't prompt, submit immediately.
    if (isNaN(examEndTime) || examEndTime - Date.now() <= 0) {
        autoSubmitting = true;
        const form = document.getElementById("exam-form");
        if (form) form.submit();
        return;
    }

    const overlay = document.getElementById("resumeFullscreenModal");
    if (!overlay) {
        // Overlay markup missing → resume without fullscreen rather than trapping them.
        beginExamRuntime(window.examConfig.examEndTime);
        return;
    }

    showResumeOverlay(); // no warning number → default reload text
}

// Expose so exam_guidelines.js can reach it
window.beginExamRuntime = beginExamRuntime;

// =============================
// PROGRESS BAR
// =============================

function updateProgress() {

    const completed =
        attempted.filter(Boolean).length;

    const progressPercent =
        (completed / total) * 100;

    const progressText =
        document.getElementById("progress-text");

    const progressFill =
        document.getElementById("progress-fill");

    if (progressText) {

        progressText.innerText =
            `${completed} of ${total} completed`;
    }

    if (progressFill) {

        progressFill.style.width =
            `${progressPercent}%`;
    }
}

// =============================
// NAVIGATION STATES
// =============================

function updateNavButtonState(n) {

    const btn =
        document.getElementById("nav-" + n);

    if (!btn) return;

    btn.classList.remove(
        "answered",
        "bookmarked",
        "active"
    );

    if (attempted[n]) {
        btn.classList.add("answered");
    }

    if (bookmarked[n]) {
        btn.classList.add("bookmarked");
    }

    if (n === current) {
        btn.classList.add("active");
    }
}

function refreshNavigation() {

    for (let i = 1; i <= total; i++) {
        updateNavButtonState(i);
    }
}

// =============================
// QUESTION ATTEMPT CHECK
// =============================

function markCurrentAsAttempted(n) {

    const radios =
        document.querySelectorAll(
            '#question-' + n + ' input[type="radio"]'
        );

    for (const radio of radios) {

        if (radio.checked) {

            attempted[n] = true;

            updateProgress();
            updateNavButtonState(n);

            return;
        }
    }
}

// =============================
// QUESTION NAVIGATION
// =============================

function showQuestion(n) {

    if (n < 1 || n > total) return;

    markCurrentAsAttempted(current);

    const currentBlock =
        document.getElementById(
            "question-" + current
        );

    const nextBlock =
        document.getElementById(
            "question-" + n
        );

    if (currentBlock) {
        currentBlock.style.display = "none";
    }

    if (nextBlock) {
        nextBlock.style.display = "block";
    }

    current = n;

    refreshNavigation();

    const prevBtn =
        document.getElementById("prev-btn");

    if (prevBtn) {
        prevBtn.disabled =
            current === 1;
    }

    const nextBtn =
        document.getElementById("next-btn");

    const submitBtn =
        document.getElementById("submit-btn");

    if (current === total) {

        if (nextBtn) {
            nextBtn.style.display = "none";
        }

        if (submitBtn) {
            submitBtn.style.display =
                "inline-block";
        }

    } else {

        if (nextBtn) {
            nextBtn.style.display =
                "inline-block";
        }

        if (submitBtn) {
            submitBtn.style.display =
                "none";
        }
    }
}

function nextQuestion() {
    showQuestion(current + 1);
}

function prevQuestion() {
    showQuestion(current - 1);
}

// =============================
// BOOKMARKS
// =============================

function toggleBookmark(n) {

    bookmarked[n] =
        !bookmarked[n];

    updateNavButtonState(n);
}

// =============================
// RADIO BUTTON STYLING
// =============================

document.addEventListener(
    "change",
    function (e) {

        if (
            !e.target.matches(
                'input[type="radio"]'
            )
        ) {
            return;
        }

        const block =
            e.target.closest(
                ".question-block"
            );

        if (!block) return;

        const questionNo =
            parseInt(
                block.dataset.qnum
            );

        attempted[questionNo] = true;

        updateProgress();
        updateNavButtonState(questionNo);

        block
            .querySelectorAll(".option")
            .forEach(option => {
                option.classList.remove(
                    "selected"
                );
            });

        e.target
            .closest(".option")
            .classList.add("selected");
    }
);

// =============================
// PAGE LOAD
// =============================

window.addEventListener(
    "DOMContentLoaded",
    function () {

        updateProgress();

        refreshNavigation();

        showQuestion(1);

        //  if (window.examConfig.examEndTime) {
        //     // Exam already in progress (e.g. page refreshed) → resume timer + proctoring
        //     beginExamRuntime(window.examConfig.examEndTime);
        // }

        wireResumeButton();
        const warningAckBtn = document.getElementById("warningAckBtn");
        if (warningAckBtn) {
            warningAckBtn.addEventListener("click", function () {
                const modal = document.getElementById("warningModal");
                if (modal) modal.style.display = "none";
            });
        }
        if (window.examConfig.examEndTime) {
            // Exam already in progress (page was reloaded) → require a fresh
            // click to re-enter fullscreen before resuming.
            resumeExamAfterReload();
        }

    }
);
function openSubmitConfirmation() {

    const attemptedCount =
        attempted.filter(Boolean).length;

    const remainingCount =
        total - attemptedCount;

    const confirmText =
        document.querySelector(".confirm-text");

    if (confirmText) {

        if (remainingCount > 0) {

            confirmText.innerHTML = `
                You still have
                <strong>${remainingCount}</strong>
                unanswered question(s).

                <br><br>

                Are you sure you want to submit?
            `;

        } else {

            confirmText.innerHTML = `
                You have answered all questions.

                <br><br>

                Are you sure you want to submit?
            `;
        }
    }

    const attemptedEl =
        document.getElementById("attemptedCount");

    if (attemptedEl) {
        attemptedEl.textContent =
            attemptedCount;
    }

    const remainingEl =
        document.getElementById("remainingCount");

    if (remainingEl) {
        remainingEl.textContent =
            remainingCount;
    }

    const modal =
        document.getElementById(
            "submitConfirmModal"
        );

    if (modal) {
        modal.style.display = "flex";
    }
}

// =============================
// EVENT BINDINGS
// =============================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById(
                "exam-form"
            );

        // Intercept form submit
        if (form) {

            form.addEventListener(
                "submit",
                function (e) {
                    console.log("FORM INTERCEPTED");
                    if (
                        finalSubmission ||
                        autoSubmitting
                    ) {
                        return;
                    }

                    e.preventDefault();

                    openSubmitConfirmation();
                }
            );
        }

        // Review Answers Button
        const reviewBtn =
            document.getElementById(
                "reviewAnswersBtn"
            );

        if (reviewBtn) {

            reviewBtn.addEventListener(
                "click",
                function () {

                    const modal =
                        document.getElementById(
                            "submitConfirmModal"
                        );

                    if (modal) {
                        modal.style.display =
                            "none";
                    }
                }
            );
        }

        // Final Submit Button
        const finalSubmitBtn =
            document.getElementById(
                "finalSubmitBtn"
            );

        if (finalSubmitBtn) {

            finalSubmitBtn.addEventListener(
                "click",
                function () {

                    finalSubmission = true;

                    document.getElementById(
                        "exam-form"
                    ).submit();
                }
            );
        }

    }
);
// =============================
// DISABLE COPY / PASTE / RIGHT-CLICK / SELECTION
// =============================
["contextmenu", "copy", "cut", "paste", "dragstart", "selectstart"]
    .forEach(function (evt) {
        document.addEventListener(evt, function (e) {
            e.preventDefault();
        });
    });

} 

