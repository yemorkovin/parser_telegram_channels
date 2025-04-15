import os
import re
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread


class TelegramImageParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Image Parser")
        self.root.geometry("600x400")

        self.create_widgets()
        self.setup_layout()

        # Переменные состояния
        self.parsing = False
        self.stop_parsing = False

    def create_widgets(self):
        # Фрейм для ввода файла с каналами
        self.file_frame = ttk.LabelFrame(self.root, text="Файл с каналами Telegram")
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=50)
        self.browse_btn = ttk.Button(self.file_frame, text="Обзор...", command=self.browse_file)

        # Фрейм для настроек
        self.settings_frame = ttk.LabelFrame(self.root, text="Настройки сохранения")
        self.folder_path_var = tk.StringVar(value="downloaded_images")
        self.folder_entry = ttk.Entry(self.settings_frame, textvariable=self.folder_path_var, width=50)
        self.folder_browse_btn = ttk.Button(self.settings_frame, text="Обзор...", command=self.browse_folder)

        # Фрейм для управления
        self.control_frame = ttk.Frame(self.root)
        self.start_btn = ttk.Button(self.control_frame, text="Начать парсинг", command=self.start_parsing)
        self.stop_btn = ttk.Button(self.control_frame, text="Остановить", command=self.stop_parsing_func,
                                   state=tk.DISABLED)

        # Фрейм для логов
        self.log_frame = ttk.LabelFrame(self.root, text="Лог выполнения")
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD)
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)

        # Прогресс бар
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100, mode='determinate')

    def setup_layout(self):
        # Расположение элементов
        self.file_frame.pack(pady=5, padx=5, fill=tk.X)
        self.file_entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        self.browse_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        self.settings_frame.pack(pady=5, padx=5, fill=tk.X)
        self.folder_entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        self.folder_browse_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        self.control_frame.pack(pady=5, padx=5, fill=tk.X)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.log_frame.pack(pady=5, padx=5, expand=True, fill=tk.BOTH)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.progress_bar.pack(pady=5, padx=5, fill=tk.X)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.file_path_var.set(file_path)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_path_var.set(folder_path)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def start_parsing(self):
        file_path = self.file_path_var.get()
        save_folder = self.folder_path_var.get()

        if not file_path:
            messagebox.showerror("Ошибка", "Укажите файл с каналами Telegram")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                channels = [line.strip() for line in f.readlines() if line.strip()]
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл: {e}")
            return

        if not channels:
            messagebox.showerror("Ошибка", "Файл не содержит каналов для парсинга")
            return

        self.parsing = True
        self.stop_parsing = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.progress_var.set(0)

        # Запуск парсинга в отдельном потоке
        Thread(target=self.parse_channels, args=(channels, save_folder), daemon=True).start()

    def stop_parsing_func(self):
        self.stop_parsing = True
        self.log_message("⏹ Остановка парсинга...")
        self.stop_btn.config(state=tk.DISABLED)

    def parse_channels(self, channels, save_folder):
        total_channels = len(channels)
        for i, channel in enumerate(channels):
            if self.stop_parsing:
                break

            try:
                self.log_message(f"🔍 Парсинг канала: {channel}")
                self.progress_var.set((i / total_channels) * 100)

                # Получаем HTML страницы канала
                try:
                    response = requests.get(channel)
                    response.raise_for_status()
                except requests.RequestException as e:
                    self.log_message(f"❌ Ошибка при загрузке канала {channel}: {e}")
                    continue

                # Извлекаем ссылки на изображения
                image_links = self.extract_image_links(response.text)

                if not image_links:
                    self.log_message(f"ℹ️ В канале {channel} не найдено изображений")
                    continue

                self.log_message(f"📸 Найдено {len(image_links)} изображений")

                # Создаем подпапку для канала
                channel_name = channel.split('/')[-1] or f"channel_{i}"
                channel_folder = os.path.join(save_folder, channel_name)
                os.makedirs(channel_folder, exist_ok=True)

                # Загружаем изображения
                total_images = len(image_links)
                for j, img_url in enumerate(image_links):
                    if self.stop_parsing:
                        break

                    self.download_image(img_url, channel_folder)
                    self.progress_var.set(((i + (j + 1) / total_images) / total_channels * 100))

            except Exception as e:
                self.log_message(f"⚠️ Ошибка при обработке канала {channel}: {e}")

        self.parsing = False
        self.root.after(0, self.finish_parsing)

    def finish_parsing(self):
        self.progress_var.set(100)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if not self.stop_parsing:
            self.log_message("✅ Парсинг завершен!")
        else:
            self.log_message("⏹ Парсинг остановлен пользователем")

    @staticmethod
    def extract_image_links(text):
        pattern = r'https?://[^\s]+?\.(?:jpg|jpeg|png|gif|bmp|webp)(?:\?[^\s]*)?'
        image_links = re.findall(pattern, text, re.IGNORECASE)
        return image_links

    @staticmethod
    def sanitize_filename(filename):
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)
        max_length = 100
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext)] + ext
        return filename

    def download_image(self, url, save_folder):
        try:
            original_filename = url.split("/")[-1].split("?")[0]
            safe_filename = self.sanitize_filename(original_filename)

            if not safe_filename:
                safe_filename = "image.jpg"

            save_path = os.path.join(save_folder, safe_filename)

            if os.path.exists(save_path):
                self.log_message(f"ℹ️ Файл уже существует: {safe_filename}")
                return save_path

            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            with open(save_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    if self.stop_parsing:
                        return None
                    file.write(chunk)

            self.log_message(f"✅ Сохранено: {safe_filename}")
            return save_path

        except Exception as e:
            self.log_message(f"❌ Ошибка при загрузке {url}: {e}")
            return None


if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramImageParserApp(root)
    root.mainloop()