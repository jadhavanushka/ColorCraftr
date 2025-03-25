# ColorCraftr

ColorCraftr is a web application for generating color palettes, exploring color libraries, and playing a hex color guessing game. Users can upload an image to generate a palette of dominant colors, search and explore colors, and test their color knowledge with a fun guessing game. Check out the site [here](https://colorcraftr.alwaysdata.net).

## Features

- **Color Palette Generator**: Upload an image to extract its dominant colors and generate a color palette.
- **Color Library**: Search and explore a library of colors by name or hex code.
- **Guess Hex Game**: Guess the hex value of a randomly generated color and score based on the accuracy of your guess.
  
## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: SQLite
- **Color Extraction**: ColorThief
- **Deployment**: AlwaysData

## Installation

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/jadhavanushka/colorcraftr.git
    cd colorcraftr
    ```

2. **Set Up the Virtual Environment:**

    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3. **Install the Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Application Locally:**

    ```bash
    flask run
    ```

6. **Access the Application:**
    Visit `http://127.0.0.1:5000` in your web browser.

## Acknowledgments

- [ColorThief](https://github.com/lokesh/color-thief-python) for color extraction.
