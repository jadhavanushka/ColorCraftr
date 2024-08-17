document.addEventListener("DOMContentLoaded", function () {
    const decreaseBtn = document.getElementById("decrease-count");
    const increaseBtn = document.getElementById("increase-count");
    const colorCountInput = document.getElementById("color-count");

    // Decrease button logic
    decreaseBtn.addEventListener("click", function () {
        let currentValue = parseInt(colorCountInput.value);
        if (currentValue > 1) {
            colorCountInput.value = currentValue - 1;
        }
    });

    // Increase button logic
    increaseBtn.addEventListener("click", function () {
        let currentValue = parseInt(colorCountInput.value);
        colorCountInput.value = currentValue + 1;
    });
});
