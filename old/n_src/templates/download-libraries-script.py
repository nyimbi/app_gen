import os
import requests
from urllib.parse import urlparse

# List of CSS and JS libraries to download
LIBRARIES = [
    # CSS files
    "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-slider/11.0.2/css/bootstrap-slider.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-tagsinput/0.8.0/bootstrap-tagsinput.css",
    "https://cdnjs.cloudflare.com/ajax/libs/easymde/2.16.1/easymde.min.css",
    "https://unpkg.com/leaflet@1.7.1/dist/leaflet.css",
    "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/css/intlTelInput.css",
    "https://cdnjs.cloudflare.com/ajax/libs/raty/3.1.1/jquery.raty.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/spectrum/1.8.1/spectrum.min.css",
    "https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.css",
    "https://cdn.quilljs.com/1.3.6/quill.snow.css",
    "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css",

    # JavaScript files
    "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-slider/11.0.2/bootstrap-slider.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-tagsinput/0.8.0/bootstrap-tagsinput.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.12/ace.js",
    "https://cdnjs.cloudflare.com/ajax/libs/easymde/2.16.1/easymde.min.js",
    "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js",
    "https://cdnjs.cloudflare.com/ajax/libs/jquery-maskmoney/3.0.2/jquery.maskMoney.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/intlTelInput.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/raty/3.1.1/jquery.raty.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/duration-picker/2.0.0/duration-picker.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/spectrum/1.8.1/spectrum.min.js",
    "https://cdn.jsdelivr.net/momentjs/latest/moment.min.js",
    "https://cdn.jsdelivr.net/npm/daterangepicker/daterangepicker.min.js",
    "https://cdn.quilljs.com/1.3.6/quill.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.full.min.js",
]

def download_file(url, directory):
    """Download a file from a URL and save it to the specified directory."""
    filename = os.path.basename(urlparse(url).path)
    filepath = os.path.join(directory, filename)
    
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad responses
    
    with open(filepath, 'wb') as f:
        f.write(response.content)
    
    print(f"Downloaded: {filename}")

def main():
    # Define the base directory for your Flask-AppBuilder project
    base_dir = "."  # Change this to your project's base directory if needed
    
    # Create directories if they don't exist
    static_dir = os.path.join(base_dir, "app", "static")
    css_dir = os.path.join(static_dir, "css")
    js_dir = os.path.join(static_dir, "js")
    
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)
    
    # Download each library
    for url in LIBRARIES:
        if url.endswith('.css'):
            download_file(url, css_dir)
        elif url.endswith('.js'):
            download_file(url, js_dir)
        else:
            print(f"Skipping unknown file type: {url}")

    print("All libraries downloaded successfully!")

if __name__ == "__main__":
    main()
