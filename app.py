from flask import Flask, render_template, request, redirect, url_for, session
from colorthief import ColorThief
import os
from utils import get_colors_list

app = Flask(__name__)
app.secret_key = "secret_key"

# Make sure you have a folder to store the uploaded images
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Default image when the page first loads
DEFAULT_IMAGE = "static/uploads/default.jpg"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate_palette", methods=["GET", "POST"])
def generatePalette():
    if request.method == "POST":
        file = request.files.get("file")
        num_colors = int(request.form.get("color-count", 8))
        color_code_format = request.form.get("color-code")

        # Check if a new file is uploaded
        if file and file.filename != "":
            # Save the uploaded image
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(img_path)

            # Store the uploaded image path in the session to reuse later
            session["last_uploaded_image"] = img_path
        else:
            # Use the last uploaded image or the default image if none is available
            img_path = session.get("last_uploaded_image", DEFAULT_IMAGE)

        # Use ColorThief to extract colors
        color_thief = ColorThief(img_path)
        palette = color_thief.get_palette(color_count=num_colors)

        # Convert colors to the color codes
        colors_list = get_colors_list(palette)

        return render_template(
            "generatePalette.html",
            colors_list=colors_list,
            code=color_code_format,
            color_count=num_colors,
            img_url=session["last_uploaded_image"],
        )

    # On GET request, use the default image to generate the initial palette
    img_path = DEFAULT_IMAGE
    color_thief = ColorThief(img_path)
    palette = color_thief.get_palette(color_count=8, quality=5)
    session["last_uploaded_image"] = DEFAULT_IMAGE

    colors_list = get_colors_list(palette)

    return render_template(
        "generatePalette.html",
        colors_list=colors_list,
        code='hex',
        color_count=8,
        img_url=session["last_uploaded_image"],
    )


if __name__ == "__main__":
    app.run(debug=True)
