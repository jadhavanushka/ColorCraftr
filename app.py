from flask import Flask, render_template, request, redirect, url_for
from colorthief import ColorThief
import os
from PIL import Image

app = Flask(__name__)

app.secret_key = 'secret_key'

# Make sure you have a folder to store the uploaded images
UPLOAD_FOLDER = 'static\\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate_palette", methods=["GET", "POST"])
def generatePalette():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        num_colors = int(request.form.get('color-count', 4))
        color_code_format = request.form.get("color-code")
        
        print(file, num_colors, color_code_format)
            
        # if file.filename == "":
        #     return redirect(request.url)

        if file:
            # Save the uploaded image
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(img_path)

            # Use ColorThief to extract colors
            color_thief = ColorThief(img_path)
            palette = color_thief.get_palette(color_count=num_colors)

            # Convert colors to the requested color code format
            colors_list = []
            for color in palette:
                if color_code_format == 'hex':
                    colors_list.append({"hex": "%02x%02x%02x" % color})
                elif color_code_format == 'rgb':
                    colors_list.append({"rgb": f"rgb({color[0]}, {color[1]}, {color[2]})"})

            print(colors_list)
            return render_template("generatePalette.html", colors_list=colors_list, img_url=url_for('static', filename=f'uploads/{file.filename}'))
    
    return render_template("generatePalette.html")

if __name__ == "__main__":
    app.run(debug=True)
