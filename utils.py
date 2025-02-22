import random
import sqlite3
from flask import g
import io
from werkzeug.utils import secure_filename

DATABASE = "color_craftr.db"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
DEFAULT_IMAGE = "default.jpg"


def get_db():
    # Opens a connection to the SQLite database
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def query_db(query, args=(), one=False):
    conn = get_db().execute(query, args)
    rv = conn.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv


def allowed_file(filename):
    # Checks if the uploaded file has an allowed extension.
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    # Saves the uploaded image as a BLOB in the database and returns the filename.
    if not file or not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)

    # Don't save if it's named the same as default image
    if filename == DEFAULT_IMAGE:
        return DEFAULT_IMAGE

    delete_previous_image()  # Remove old images

    image_data = file.read()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO images (filename, image_data) VALUES (?, ?)",
        (filename, image_data),
    )
    conn.commit()

    return filename


def delete_previous_image():
    # Deletes the previously uploaded image from the database (excluding default.jpg).
    last_uploaded = query_db(
        "SELECT filename FROM images ORDER BY id DESC LIMIT 1", one=True
    )

    if last_uploaded and last_uploaded["filename"] != DEFAULT_IMAGE:
        db = get_db()
        db.execute(
            "DELETE FROM images WHERE filename = ?", (last_uploaded["filename"],)
        )
        db.commit()


def get_image(filename):
    # Retrieves the image data from the database.
    image = query_db(
        "SELECT image_data FROM images WHERE filename = ?", (filename,), one=True
    )
    if image:
        return io.BytesIO(image["image_data"])
    return None


def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    k = 1 - max(r, g, b)
    c = (1 - r - k) / (1 - k) if (1 - k) != 0 else 0
    m = (1 - g - k) / (1 - k) if (1 - k) != 0 else 0
    y = (1 - b - k) / (1 - k) if (1 - k) != 0 else 0
    return f"cmyk({int(c * 100)}%, {int(m * 100)}%, {int(y * 100)}%, {int(k * 100)}%)"


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    h = s = l = (mx + mn) / 2
    c = mx - mn

    if c != 0:
        if mx == r:
            h = (60 * ((g - b) / c) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / c) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / c) + 240) % 360

        s = 0 if c == 0 else (c / (1 - abs(2 * l - 1)))

    return f"hsl({int(h)}, {int(s * 100)}%, {int(l * 100)}%)"


def rgb_to_hex(color):
    return "%02x%02x%02x" % color


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    else:
        return None  # Invalid hex


def get_colors_list(palette):
    colors_list = []
    for color in palette:
        r, g, b = color
        color_info = {
            "rgb": f"rgb({r}, {g}, {b})",
            "hex": rgb_to_hex(color),
            "hsl": rgb_to_hsl(r, g, b),
            "cmyk": rgb_to_cmyk(r, g, b),
        }
        colors_list.append(color_info)
    return colors_list


def calculate_color_distance(color1_hex, color2_hex):
    # Convert hex to RGB
    color1_rgb = hex_to_rgb(color1_hex)
    color2_rgb = hex_to_rgb(color2_hex)

    # Calculate Euclidean distance in RGB space
    distance = (
        (color2_rgb[0] - color1_rgb[0]) ** 2
        + (color2_rgb[1] - color1_rgb[1]) ** 2
        + (color2_rgb[2] - color1_rgb[2]) ** 2
    ) ** 0.5

    return distance


def find_similar_colors(target_color_hex, color_list):
    color_distances = []

    for color_name, color_hex in color_list:
        distance = calculate_color_distance(target_color_hex, color_hex)
        if distance > 0:
            color_distances.append((color_name, color_hex, distance))

    # Sort by the smallest distance
    sorted_colors = sorted(color_distances, key=lambda x: x[2])

    # Return the top closest colors
    return sorted_colors[:25]


def generate_random_hex():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def calculate_accuracy(distance):
    max_distance = (255**2 + 255**2 + 255**2) ** 0.5  # Maximum RGB distance
    accuracy = max(0, 100 * (1 - (distance / max_distance)))
    return accuracy
