import os
from flask import Flask, request, redirect, url_for, render_template, flash, send_from_directory, abort, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import zipfile

app = Flask(__name__)

image_folder = 'image'
upload_folder = 'upload'
allowed_extensions = {'pdf', 'jpeg', 'jpg', 'png', 'gif', 'tif'}

if not os.path.exists(image_folder):
    os.makedirs(image_folder)

if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

app.secret_key = "my_secret_key"


def allowed_type(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def compress_image(image_path, filename):
    img = Image.open(image_path)
    w, h = img.size
    img = img.resize((w//2, h//2), Image.Resampling.LANCZOS)
    img.save(os.path.join(upload_folder, filename))


@app.route('/', methods=['POST', 'GET'])
def homepage():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash("No file part", 'danger')
            return redirect(request.url)

        images = request.files.getlist('files[]')
        image_names = []
        file_urls = []

        for image in images:
            if image and allowed_type(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(image_folder, filename)
                image.save(image_path)
                compress_image(image_path, filename)
                image_names.append(filename)
                file_urls.append(url_for('get_file', filename=filename))

            else:
                flash("That image extension is not allowed", 'danger')
                return render_template('index.html')

        return render_template('index.html', file_urls=file_urls, image_names=image_names)

    return render_template('index.html')


@app.route('/image/<filename>')
def get_file(filename):
    return send_from_directory(upload_folder, filename)


@app.route('/download', methods=['GET'])
def download_file():
    upload_path = os.path.abspath(upload_folder)

    upload_files = os.listdir(upload_path)
    if len(upload_files) < 2:
        if upload_files:
            latest_file = max(upload_files, key=lambda x: os.path.getmtime(os.path.join(upload_path, x)))
            return send_from_directory(upload_path, latest_file, as_attachment=True)
        else:
            return "No files available for download."
    elif len(upload_files) > 1:
        zip_filename = "images.zip"
        zip_filepath = os.path.join(upload_folder, zip_filename)

        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for root, dirs, files in os.walk(upload_folder):
                for file in files:
                    if file != zip_filename:
                        zipf.write(os.path.join(root, file), arcname=file)

        return send_file(zip_filepath, as_attachment=True)
    return redirect(url_for('/'))


@app.route('/back_to_homepage', methods=['POST', 'GET'])
def go_back_to_homepage():
    upload_path = os.path.abspath(upload_folder)
    image_paths = os.path.abspath(image_folder)

    try:
        for filename in os.listdir(upload_path):
            file_path = os.path.join(upload_path, filename)
            os.remove(file_path)
        for filename in os.listdir(image_paths):
            file_path = os.path.join(image_paths, filename)
            os.remove(file_path)
    except FileNotFoundError:
        return "File not found"

    return redirect(url_for("homepage"))


if __name__ == "__main__":
    app.run(debug=True)
