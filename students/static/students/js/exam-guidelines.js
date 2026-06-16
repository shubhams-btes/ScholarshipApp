document.addEventListener(
    "DOMContentLoaded",
    function () {

        const checkbox =
            document.getElementById(
                "guidelineCheck"
            );

        const startBtn =
            document.getElementById(
                "startExamBtn"
            );

        if (!checkbox || !startBtn) {
            return;
        }

        checkbox.addEventListener(
            "change",
            function () {

                startBtn.disabled =
                    !this.checked;

            }
        );

        startBtn.addEventListener(
            "click",
            async function () {

                startBtn.disabled = true;

                const response =
                    await fetch(window.examConfig.startExamUrl, {
    method: "GET",
    credentials: "same-origin"
})

                const data =
                    await response.json();

                if(data.success){

                    location.reload();

                }

            }
        );

    }
);