import os
import re
import requests
from urllib.parse import urlparse


def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    max_length = 100
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    return filename


def download_file(url, save_path, timeout=10):
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return True
    except Exception as e:
        return False


def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split('/')[0]