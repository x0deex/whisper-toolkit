import whisper
import argparse
import os
import sys
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

# ----------------------------------- Баннер (опционально) -----------------------------------
def print_banner():
    banner = [
        r" __        ___     _                    _____                              _ _               ",
        r" \ \      / / |__ (_)___ _ __   ___ _ _|_   _| __ __ _ _ __  ___  ___ _ __(_) |__   ___ _ __ ",
        r"  \ \ /\ / /| '_ \| / __| '_ \ / _ \ '__|| || '__/ _` | '_ \/ __|/ __| '__| | '_ \ / _ \ '__|",
        r"   \ V  V / | | | | \__ \ |_) |  __/ |   | || | | (_| | | | \__ \ (__| |  | | |_) |  __/ |   ",
        r"    \_/\_/  |_| |_|_|___/ .__/ \___|_|   |_||_|  \__,_|_| |_|___/\___|_|  |_|_.__/ \___|_|   ",
        r"                        |_|                                                                  ",
        "                                                                                              ",
        "                    АУДИО/ВИДЕО ТРАНСКРИБАТОР",
        "                       На основе Whisper",
        "                          𝑩𝒚 𝒙𝟎𝒅𝒆𝒙\n",
    ]
    for line in banner:
        print(line)

# ----------------------------------- Функции транскрибации -----------------------------------
def transcribe_audio(input_path, model_size="small", language="Russian", output_format="txt", callback=None):
    """
    Транскрибирует аудиофайл и вызывает callback с результатом или ошибкой.
    callback принимает два аргумента: (success, message, result_text)
    """
    if not os.path.exists(input_path):
        if callback:
            callback(False, f"❌ Файл '{input_path}' не найден!", "")
        return

    try:
        if callback:
            callback(True, f"🔧 Загружаем модель '{model_size}'...", "")

        model = whisper.load_model(model_size)

        if callback:
            callback(True, f"🎙️  Транскрибируем '{input_path}' на языке {language}...", "")

        lang_code = "ru" if language.lower() in ["russian", "russkiy", "русский", "ru"] else language.lower()

        # Транскрибация (verbose=False, чтобы не засорять консоль)
        result = model.transcribe(input_path, language=lang_code, verbose=False)

        # Сохраняем результат
        base_name = Path(input_path).stem
        output_filename = f"{base_name}.{output_format}"

        if output_format == "txt":
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(result["text"])
        elif output_format == "srt":
            save_srt(result, output_filename)
        elif output_format == "vtt":
            save_vtt(result, output_filename)
        elif output_format == "tsv":
            save_tsv(result, output_filename)
        elif output_format == "json":
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        if callback:
            callback(True, f"✅ Готово! Результат сохранён в {output_filename}", result["text"])

    except Exception as e:
        if callback:
            callback(False, f"❌ Ошибка: {e}", "")

def save_srt(result, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"]):
            start = format_time(segment["start"])
            end = format_time(segment["end"])
            f.write(f"{i+1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{segment['text'].strip()}\n\n")

def save_vtt(result, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, segment in enumerate(result["segments"]):
            start = format_time(segment["start"])
            end = format_time(segment["end"])
            f.write(f"{i+1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{segment['text'].strip()}\n\n")

def save_tsv(result, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("start\tend\ttext\n")
        for segment in result["segments"]:
            f.write(f"{segment['start']:.2f}\t{segment['end']:.2f}\t{segment['text'].strip()}\n")

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

# ----------------------------------- Графический интерфейс -----------------------------------
class WhisperApp:
    def __init__(self, root):
        self.root = root
        root.title("Whisper Транскрибатор")
        root.geometry("700x700")
        root.resizable(True, True)

        # Переменные
        self.input_path = tk.StringVar()
        self.model_var = tk.StringVar(value="small")
        self.language_var = tk.StringVar(value="Russian")
        self.format_var = tk.StringVar(value="txt")
        self.status_var = tk.StringVar(value="Готов к работе")

        # Фрейм выбора файла
        file_frame = ttk.LabelFrame(root, text="Файл", padding=5)
        file_frame.pack(fill="x", padx=10, pady=5)

        ttk.Entry(file_frame, textvariable=self.input_path, width=60).pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(file_frame, text="Обзор...", command=self.browse_file).pack(side="right", padx=5)

        # Фрейм параметров
        params_frame = ttk.LabelFrame(root, text="Параметры", padding=5)
        params_frame.pack(fill="x", padx=10, pady=5)

        # Модель
        ttk.Label(params_frame, text="Модель:").grid(row=0, column=0, sticky="w", padx=5)
        model_combo = ttk.Combobox(params_frame, textvariable=self.model_var,
                                   values=["tiny", "base", "small", "medium", "large"], state="readonly", width=10)
        model_combo.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(params_frame, text="(чем больше, тем точнее, но медленнее)").grid(row=0, column=2, sticky="w", padx=5)

        # Язык
        ttk.Label(params_frame, text="Язык:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        lang_entry = ttk.Entry(params_frame, textvariable=self.language_var, width=15)
        lang_entry.grid(row=1, column=1, sticky="w", padx=5)
        ttk.Label(params_frame, text="(например: Russian, English, или ru, en)").grid(row=1, column=2, sticky="w", padx=5)

        # Формат вывода
        ttk.Label(params_frame, text="Формат вывода:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        format_combo = ttk.Combobox(params_frame, textvariable=self.format_var,
                                    values=["txt", "srt", "vtt", "tsv", "json"], state="readonly", width=10)
        format_combo.grid(row=2, column=1, sticky="w", padx=5)

        # Кнопка запуска
        self.run_button = ttk.Button(root, text="▶ Запустить транскрибацию", command=self.run_transcription)
        self.run_button.pack(pady=10)

        # Статус
        status_frame = ttk.Frame(root)
        status_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(status_frame, textvariable=self.status_var, foreground="blue").pack(side="left")

        # Прогресс-бар
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(fill="x", padx=10, pady=5)

        # Область вывода результата
        result_frame = ttk.LabelFrame(root, text="Результат транскрибации", padding=5)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.result_text.pack(fill="both", expand=True)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите аудио/видео файл",
            filetypes=[("Медиа файлы", "*.mp3 *.wav *.m4a *.mp4 *.avi *.mov *.mkv *.flac *.ogg"),
                       ("Все файлы", "*.*")]
        )
        if filename:
            self.input_path.set(filename)

    def run_transcription(self):
        input_path = self.input_path.get().strip()
        if not input_path:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите файл.")
            return

        # Блокируем кнопку на время работы
        self.run_button.config(state="disabled")
        self.status_var.set("Идёт транскрибация...")
        self.progress.start()
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Ожидайте завершения...\n")

        # Запускаем транскрибацию в отдельном потоке, чтобы GUI не зависал
        thread = threading.Thread(target=self._transcribe_thread, daemon=True)
        thread.start()

    def _transcribe_thread(self):
        # Получаем параметры
        input_path = self.input_path.get().strip()
        model = self.model_var.get()
        language = self.language_var.get()
        output_format = self.format_var.get()

        # Определяем callback для обновления GUI из потока
        def update_status(success, message, result_text):
            # Все обновления GUI выполняем через root.after
            self.root.after(0, lambda: self._update_gui(success, message, result_text))

        # Запускаем транскрибацию
        transcribe_audio(input_path, model, language, output_format, callback=update_status)

    def _update_gui(self, success, message, result_text):
        # Останавливаем прогресс
        self.progress.stop()
        self.run_button.config(state="normal")

        if success:
            self.status_var.set("✅ " + message)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result_text)
        else:
            self.status_var.set("❌ " + message)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Ошибка:\n" + message)

# ----------------------------------- Точка входа -----------------------------------
if __name__ == "__main__":
    print_banner()
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()