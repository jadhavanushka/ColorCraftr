from flask import Flask, render_template, request, redirect, url_for, session, send_file
from colorthief import ColorThief
import os
from utils import (
    get_colors_list,
    find_similar_colors,
    generate_random_hex,
    calculate_color_distance,
    calculate_accuracy,
    save_image,
    get_image,
    query_db,
)

app = Flask(__name__)
app.secret_key = "secret_key"

UPLOAD_FOLDER = "static/uploads"
# Default image when the page first loads
DEFAULT_IMAGE = "default.jpg"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/images/<filename>")
def serve_image(filename):
    """Retrieve and serve images from the database."""
    image_data = get_image(filename)
    if image_data:
        return send_file(image_data, mimetype="image/jpeg")
    return "Image not found", 404


@app.route("/generate_palette", methods=["GET", "POST"])
def generatePalette():
    if request.method == "POST":
        file = request.files.get("file")
        num_colors = int(request.form.get("color-count", 8))
        color_code_format = request.form.get("color-code")
        filename = file.filename

        # Check if a new file is uploaded
        if file and filename != "":
            filename = save_image(file)  # Save to database
            session["last_uploaded_image"] = filename  # Update session
        else:
            # Use the last uploaded image or the default image if none is available
            filename = session.get("last_uploaded_image", DEFAULT_IMAGE)

        # Retrieve image data from database
        image_data = get_image(filename)

        if image_data is None:
            return "Error: Image not found in database", 400

        # Use ColorThief to extract colors
        color_thief = ColorThief(image_data)
        palette = color_thief.get_palette(color_count=num_colors)

        # Convert colors to the color codes
        colors_list = get_colors_list(palette)

        return render_template(
            "generatePalette.html",
            colors_list=colors_list,
            code=color_code_format,
            color_count=num_colors,
            img_url=url_for("serve_image", filename=filename),
        )

    # On GET request, use the default image to generate the initial palette
    img_path = os.path.join(UPLOAD_FOLDER, DEFAULT_IMAGE)
    session["last_uploaded_image"] = DEFAULT_IMAGE

    color_thief = ColorThief(img_path)
    palette = color_thief.get_palette(color_count=8, quality=5)
    colors_list = get_colors_list(palette)

    return render_template(
        "generatePalette.html",
        colors_list=colors_list,
        code="hex",
        color_count=8,
        img_url=url_for("serve_image", filename=session["last_uploaded_image"]),
    )


@app.route("/color_library", methods=["GET", "POST"])
def colorLibrary():
    search_text = ""
    order_by = "hsvValue"
    similar_colors = []

    if request.method == "POST":
        search_text = request.form.get("search_text").strip().strip("#")
        order_by = request.form.get("order_by", "hsvValue")

        # Check if the search input is a valid hex code
        if len(search_text) == 6 and all(
            c in "0123456789ABCDEFabcdef" for c in search_text
        ):
            # Search by Hex and find similar colors
            colors_data = query_db(
                f"SELECT Name, Hex FROM colors ORDER BY {order_by} DESC"
            )
            similar_colors = find_similar_colors(search_text, colors_data)

    # Prepare the SQL query with the search text and dynamic order by condition
    query = f"SELECT Name, Hex FROM colors WHERE Name LIKE ? OR Hex LIKE ? ORDER BY {order_by} DESC"
    data = query_db(query, ("%" + search_text + "%", "%" + search_text + "%"))

    data += similar_colors

    return render_template(
        "colorLibrary.html", colors_list=data, search_text=search_text
    )


@app.route("/guess_hex", methods=["GET", "POST"])
def guessHex():
    if "random_hex" not in session:
        session["random_hex"] = generate_random_hex()

    random_hex = session["random_hex"]
    result = None
    guessed_color = None

    if "score" not in session:
        session["score"] = 0

    if request.method == "POST":
        action = request.form.get("action")

        if action == "restart":
            session["score"] = 0
            session.pop("random_hex", None)  # Reset the color
            return redirect(url_for("guessHex"))

        elif action == "next_color":
            # Generate a new random color
            session["random_hex"] = generate_random_hex()
            return redirect(url_for("guessHex"))

        guess = request.form.get("guess").strip().strip("#").lower()
        answer = request.form.get("answer").strip().strip("#").lower()

        # Check if the input is a valid hex code
        if len(guess) == 6 and all(c in "0123456789ABCDEFabcdef" for c in guess):
            guessed_color = guess

            # Calculate the color distance and update the score
            distance = calculate_color_distance(guess, answer)
            accuracy = calculate_accuracy(distance)

            if accuracy > 75:
                session["score"] += int(accuracy)

            result = f"{accuracy:.2f}% accurate"

        else:
            result = "Invalid hex"

    return render_template(
        "guessHex.html",
        random_hex=session["random_hex"],
        score=session["score"],
        result=result,
        guessed_color=guessed_color,
    )
