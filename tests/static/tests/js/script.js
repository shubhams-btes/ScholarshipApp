// =============================
// CONFIG
// =============================

const total = window.examConfig.totalQuestions;

const examEndTime =
    new Date(window.examConfig.examEndTime).getTime();

let current = 1;

const attempted =
    Array(total + 1).fill(false);

const bookmarked =
    Array(total + 1).fill(false);

// =============================
// TIMER
// =============================

function updateTimer() {

    const now = Date.now();

    const remaining =
        Math.floor((examEndTime - now) / 1000);

    if (remaining <= 0) {

        document.getElementById("timer").textContent =
            "00:00";

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

        startTimer();
    }
);