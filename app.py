from flask import Flask, request, send_file
from PIL import Image
import io
import os
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Compressor</title>
        <link rel="stylesheet" href="/static/css/style.css">

        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            input[type="file"], input[type="number"], input[type="submit"], label { margin-top: 10px; }
            #target_size { opacity: 0.5; }
            .disabled { opacity: 0.2; }
        </style>
    </head>
    <body>
        <h1>Image Compressor</h1>
        <form method="post" action="/upload" enctype="multipart/form-data">
            
            <!-- Centered Choose File Button -->
            <input type="file" name="files" multiple required>
            
            <!-- Custom Target Size in the Center -->
            <label for="target_size">Custom Target Size (in KB):</label>
            <input type="number" name="target_size" id="target_size" min="20" placeholder="Enter your value in KB">

            <!-- Optimize checkbox aligned to the right with a tooltip -->
            <div class="checkbox-group">
                <label for="optimize">Optimize</label>
                <input type="checkbox" name="optimize" id="optimize" onclick="toggleCustomSize()">
                <div class="tooltip">?
                    <span class="tooltiptext">Optimizing reduces file size while maintaining quality, suitable for web use.</span>
                </div>
            </div>

            <input type="submit" value="Compress Images">
        </form>

        <script>
            function toggleCustomSize() {
                const targetSizeInput = document.getElementById('target_size');
                if (document.getElementById('optimize').checked) {
                    targetSizeInput.classList.add('disabled');
                    targetSizeInput.disabled = true;
                } else {
                    targetSizeInput.classList.remove('disabled');
                    targetSizeInput.disabled = false;
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files')
    optimize = 'optimize' in request.form
    target_size_kb = request.form.get('target_size', type=int)
    target_size_bytes = target_size_kb * 1024 if target_size_kb else None

    zip_filename = "YourPhotos.zip"
    zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in files:
            if file:
                image = Image.open(file)
                image_bytes = io.BytesIO()

                # Adjustments for optimization mode
                if optimize:
                    # JPEG compression with moderate quality for optimal size reduction
                    format_to_use = 'JPEG' if image.format in ['JPEG', 'JPG'] else image.format
                    if format_to_use == 'JPEG':
                        image.save(image_bytes, format=format_to_use, optimize=True, quality=55)
                    else:
                        # Save other formats with general optimization but no heavy quality loss
                        image.save(image_bytes, format=format_to_use, optimize=True)
                
                elif target_size_bytes:
                    # Save normally, and check for size
                    image.save(image_bytes, format=image.format)
                    current_size = len(image_bytes.getvalue())

                    # Reduce image size to meet target
                    while current_size > target_size_bytes:
                        image_bytes.seek(0)
                        image = image.reduce(2)  # Example: reduce dimensions by half
                        image_bytes = io.BytesIO()
                        image.save(image_bytes, format=image.format if image.format else 'JPEG')
                        current_size = len(image_bytes.getvalue())

                # Write to the zip file
                zipf.writestr(file.filename, image_bytes.getvalue())

    return send_file(zip_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
