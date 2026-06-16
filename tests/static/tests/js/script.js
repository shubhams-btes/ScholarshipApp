// =============================
// CONFIG
// =============================
if (!window.examConfig) {
    console.warn("examConfig not found");
} else {

const total = window.examConfig.totalQuestions;
let autoSubmitting = false;
let finalSubmission = false;
const examEndTime =
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

        if(window.examConfig.examEndTime){
            startTimer();
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
}