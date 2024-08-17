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


const fileInput = document.getElementById('file-upload');
const fileNameDisplay = document.getElementById('file-name');

// Listen for the file input change event
fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
        fileNameDisplay.textContent = `Selected file: ${file.name}`;
    } else {
        fileNameDisplay.textContent = ''; // Clear if no file is selected
    }
});