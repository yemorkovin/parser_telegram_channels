import tkinter as tk
from app import TelegramParserApp

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramParserApp(root)
    root.mainloop()