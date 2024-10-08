from flask import Flask, g, render_template, request, redirect, url_for, session
from colorthief import ColorThief
from datetime import timedelta
from google.cloud import storage
from dotenv import load_dotenv
import io
import os
from PIL import Image
import requests
import sqlite3
import tempfile
from utils import (
    get_colors_list,
    find_similar_colors,
    generate_random_hex,
    calculate_color_distance,
    calculate_accuracy,
)

app = Flask(__name__)
app.secret_key = "secret_key"

load_dotenv()

# Read the JSON credentials from an environment variable
google_credentials_content = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_CONTENT")

if google_credentials_content:
    # Create a temporary file for Google Cloud credentials
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        temp_file.write(google_credentials_content.encode("utf-8"))
        google_credentials_path = temp_file.name

    # Set the Google Cloud credentials using the temporary file
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials_path
else:
    raise EnvironmentError(
        "GOOGLE_APPLICATION_CREDENTIALS_CONTENT environment variable is not set."
    )


# Make sure you have a folder to store the uploaded images
UPLOAD_FOLDER = "static/uploads"
BUCKET_NAME = "color-craftr-uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Default image when the page first loads
DEFAULT_IMAGE = "static/uploads/default.jpg"

# Path to SQLite database file
DATABASE = "colors.db"


# upload the file's content to Google Cloud Storage
def upload_to_gcs(file, bucket_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)
    return destination_blob_name


# Generate a signed URL for the blob
def generate_signed_url(bucket_name, blob_name, expiration_time=900):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=expiration_time),
        method="GET",
    )
    return url


def get_image_from_signed_url(signed_url):
    response = requests.get(signed_url)
    response.raise_for_status()  # Ensure the request was successful
    img_data = io.BytesIO(response.content)  # Keep the image in memory
    return Image.open(img_data)  # Return an in-memory image


def get_db():
    # Opens a connection to the SQLite database
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


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
            destination_blob_name = f"uploads/{file.filename}"
            img_path = upload_to_gcs(file, BUCKET_NAME, destination_blob_name)
            session["last_uploaded_image"] = img_path
        else:
            # Use the last uploaded image or the default image if none is available
            img_path = session.get("last_uploaded_image", DEFAULT_IMAGE)

        # Generate a signed URL for the uploaded image
        if img_path != DEFAULT_IMAGE:
            signed_url = generate_signed_url(BUCKET_NAME, img_path, expiration_time=900)
            img_url = signed_url

            # Fetch the image from the signed URL and keep it in memory
            image = get_image_from_signed_url(signed_url)

            # Convert the image to RGB if it has an alpha channel
            if image.mode in ("RGBA", "LA") or (
                image.mode == "P" and "transparency" in image.info
            ):
                image = image.convert("RGB")

            # Save the image to an in-memory file
            img_byte_array = io.BytesIO()
            image.save(img_byte_array, format="PNG")  # Use PNG format for compatibility
            img_byte_array.seek(0)  # Move back to the start of the in-memory file

            # Use ColorThief on the in-memory image
            color_thief = ColorThief(
                img_byte_array
            )  # Use in-memory image with ColorThief

        else:
            img_url = img_path
            color_thief = ColorThief(img_path)

        palette = color_thief.get_palette(color_count=num_colors)

        # Convert colors to the color codes
        colors_list = get_colors_list(palette)

        return render_template(
            "generatePalette.html",
            colors_list=colors_list,
            code=color_code_format,
            color_count=num_colors,
            img_url=img_url,
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
        code="hex",
        color_count=8,
        img_url=session["last_uploaded_image"],
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
