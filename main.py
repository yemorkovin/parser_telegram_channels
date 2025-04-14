import os

import requests
import re

def extract_image_links(text):
    # Регулярное выражение для поиска URL изображений
    pattern = r'https?://[^\s]+?\.(?:jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?'
    image_links = re.findall(pattern, text, re.IGNORECASE)
    return image_links

def sanitize_filename(filename):
    # Удаляем недопустимые символы в именах файлов для Windows
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Укорачиваем имя файла, если оно слишком длинное
    max_length = 100  # Ограничиваем длину имени файла
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    return filename


def download_image(url, save_folder="downloaded_images"):
    try:
        os.makedirs(save_folder, exist_ok=True)

        # Получаем имя файла из URL и очищаем его
        original_filename = url.split("/")[-1].split("?")[0]
        safe_filename = sanitize_filename(original_filename)

        # Если имя файла пустое (например, URL заканчивается на /), задаем стандартное имя
        if not safe_filename:
            safe_filename = "image.jpg"

        save_path = os.path.join(save_folder, safe_filename)

        # Загружаем изображение
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"✅ Изображение сохранено: {save_path}")
        return save_path
    except Exception as e:
        print(f"❌ Ошибка при загрузке: {e}")
        return None

d = requests.get('https://t.me/s/itmemes')
imgs = extract_image_links(d.text)
for img in imgs:
    download_image(img)
    #download_image(img)
