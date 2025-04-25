import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
from parser import TelegramParser
from utils import sanitize_filename, download_file, get_domain


class TelegramParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Content Parser")
        self.root.geometry("700x500")

        # Variables
        self.parsing = False
        self.stop_parsing = False
        self.content_types = ["images", "videos", "documents", "audio", "text"]

        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        # File selection frame
        self.file_frame = ttk.LabelFrame(self.root, text="Файл с каналами Telegram")
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=50)
        self.browse_btn = ttk.Button(self.file_frame, text="Обзор...", command=self.browse_file)

        # Settings frame
        self.settings_frame = ttk.LabelFrame(self.root, text="Настройки сохранения")
        self.folder_path_var = tk.StringVar(value="downloaded_content")
        self.folder_entry = ttk.Entry(self.settings_frame, textvariable=self.folder_path_var, width=50)
        self.folder_browse_btn = ttk.Button(self.settings_frame, text="Обзор...", command=self.browse_folder)

        # Content type selection
        self.content_frame = ttk.LabelFrame(self.root, text="Тип контента для парсинга")
        self.content_vars = {ctype: tk.BooleanVar(value=True) for ctype in self.content_types}
        for ctype in self.content_types:
            cb = ttk.Checkbutton(self.content_frame, text=ctype.capitalize(),
                                 variable=self.content_vars[ctype], onvalue=True, offvalue=False)
            cb.pack(side=tk.LEFT, padx=5)

        # Control frame
        self.control_frame = ttk.Frame(self.root)
        self.start_btn = ttk.Button(self.control_frame, text="Начать парсинг", command=self.start_parsing)
        self.stop_btn = ttk.Button(self.control_frame, text="Остановить", command=self.stop_parsing_func,
                                   state=tk.DISABLED)

        # Log frame
        self.log_frame = ttk.LabelFrame(self.root, text="Лог выполнения")
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD)
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100, mode='determinate')

    def setup_layout(self):
        self.file_frame.pack(pady=5, padx=5, fill=tk.X)
        self.file_entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        self.browse_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        self.settings_frame.pack(pady=5, padx=5, fill=tk.X)
        self.folder_entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)
        self.folder_browse_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        self.content_frame.pack(pady=5, padx=5, fill=tk.X)

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
        selected_types = [ctype for ctype, var in self.content_vars.items() if var.get()]

        if not file_path:
            messagebox.showerror("Ошибка", "Укажите файл с каналами Telegram")
            return

        if not selected_types:
            messagebox.showerror("Ошибка", "Выберите хотя бы один тип контента")
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

        Thread(target=self.parse_channels, args=(channels, save_folder, selected_types), daemon=True).start()

    def stop_parsing_func(self):
        self.stop_parsing = True
        self.log_message("⏹ Остановка парсинга...")
        self.stop_btn.config(state=tk.DISABLED)

    def parse_channels(self, channels, save_folder, content_types):
        total_channels = len(channels)
        for i, channel in enumerate(channels):
            if self.stop_parsing:
                break

            try:
                self.log_message(f"\n🔍 Парсинг канала: {channel}")
                self.progress_var.set((i / total_channels) * 100)

                # Get channel content
                try:
                    response = requests.get(channel)
                    response.raise_for_status()
                    content = response.text
                except requests.RequestException as e:
                    self.log_message(f"❌ Ошибка при загрузке канала {channel}: {e}")
                    continue

                # Create channel folder
                channel_name = get_domain(channel) or f"channel_{i}"
                channel_folder = os.path.join(save_folder, channel_name)
                os.makedirs(channel_folder, exist_ok=True)

                # Parse selected content types
                for content_type in content_types:
                    if self.stop_parsing:
                        break

                    if content_type == "text":
                        self.save_text_content(content, channel_folder, channel_name)
                    else:
                        self.save_media_content(content, content_type, channel_folder)

            except Exception as e:
                self.log_message(f"⚠️ Ошибка при обработке канала {channel}: {e}")

        self.parsing = False
        self.root.after(0, self.finish_parsing)

    def save_media_content(self, content, content_type, save_folder):
        parser = TelegramParser()
        links = parser.extract_content(content, content_type)

        if not links:
            self.log_message(f"ℹ️ В канале не найдено {content_type}")
            return

        self.log_message(f"📌 Найдено {len(links)} файлов типа {content_type}")

        type_folder = os.path.join(save_folder, content_type)
        os.makedirs(type_folder, exist_ok=True)

        for link in links:
            if self.stop_parsing:
                return

            filename = sanitize_filename(link.split("/")[-1].split("?")[0])
            save_path = os.path.join(type_folder, filename)

            if os.path.exists(save_path):
                self.log_message(f"ℹ️ Файл уже существует: {filename}")
                continue

            if download_file(link, save_path):
                self.log_message(f"✅ Сохранено: {filename}")
            else:
                self.log_message(f"❌ Ошибка загрузки: {filename}")

    def save_text_content(self, content, save_folder, channel_name):
        parser = TelegramParser()
        text = parser.extract_text(content)

        if not text.strip():
            self.log_message("ℹ️ Текст не найден")
            return

        text_folder = os.path.join(save_folder, "text")
        os.makedirs(text_folder, exist_ok=True)

        filename = f"{channel_name}_text.txt"
        save_path = os.path.join(text_folder, filename)

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.log_message(f"✅ Текст сохранен в {filename}")
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения текста: {e}")

    def finish_parsing(self):
        self.progress_var.set(100)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if not self.stop_parsing:
            self.log_message("\n✅ Парсинг завершен!")
        else:
            self.log_message("\n⏹ Парсинг остановлен пользователем")