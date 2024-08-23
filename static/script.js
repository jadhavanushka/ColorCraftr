document.getElementById('navbar-toggle').addEventListener('click', function () {
    var menu = document.getElementById('navbar-menu');
    menu.classList.toggle('hidden');
});


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


function copyColorCode(element) {
    // Get the color code from the data-color attribute
    const colorCode = element.getAttribute('data-color');

    // Create a temporary textarea to copy the color code
    const tempTextarea = document.createElement('textarea');
    tempTextarea.value = colorCode;
    document.body.appendChild(tempTextarea);
    tempTextarea.select();
    document.execCommand('copy');
    document.body.removeChild(tempTextarea);

    // Show the success message
    const copyMessage = document.getElementById('copyMessage');
    copyMessage.classList.remove('hidden');

    // Hide the message after 2 seconds
    setTimeout(() => {
        copyMessage.classList.add('hidden');
    }, 2000);
}


function saveAsImage() {
    const colors = document.querySelectorAll('.colors li');
    const canvas = document.getElementById('colorCanvas');
    const context = canvas.getContext('2d');

    // Set canvas dimensions
    const width = 300; // Width of each color rectangle
    const height = 50; // Height of each color rectangle
    const padding = 5; // Padding between color rectangles
    const totalHeight = (height + padding) * colors.length - padding;

    canvas.width = width;
    canvas.height = totalHeight;

    // Draw each color on the canvas
    colors.forEach((colorElement, index) => {
        const color = colorElement.style.backgroundColor;
        context.fillStyle = color;
        context.fillRect(0, index * (height + padding), width, height);
    });

    // Convert canvas to image
    const image = canvas.toDataURL('image/png');

    // Create a link to download the image
    const link = document.createElement('a');
    link.href = image;
    link.download = 'colors.png';
    link.click();
}
