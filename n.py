import requests
import os
import re


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


# Ваша ссылка на изображение
image_url = "https://cdn4.cdn-telegram.org/file/vK7Cbcp6aNmK5fFBd8pPWnEkxdT0TdFAWjkCj5AeKWPXdzFhsjM-_kwJXDPxti2ydfVNqKJfzoD1-U6QTcy2I1HOMvWiwXCOeZqxQo4hKlkA_b-x4x08s0dvM5a2XV8wQYN_6hENXtRAINj_rkksd5rwfHT2N5SpyqLjx0SpJykkLYWW2FZCjVbGXlLdyoRqdNtdb0B4jCm6CXY3Ddkwkaaetx4rjlH6EqwiWkrBtcdo2W8EEmT5YHZTjj_91ZHxeoPA7hXrq-2iizPsqcnr00BUnmvWYZP5SogXMhSvk3H8CkSLfXQpGUn41z0aN4zK6Lu7F7g84rMNwdvdoVT5uA.jpg"

# Скачиваем
download_image(image_url)