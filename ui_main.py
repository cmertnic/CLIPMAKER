import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logging
import os
import subprocess
import sys

from config import CFG
from models import ProcessingState
from video_processor import process_video_thread
from ui_dialogs import SubtitleSettingsDialog, FrameSettingsDialog
from utils import log

class VideoClipperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Viral Video Clipper")
        
        # Устанавливаем размер окна
        window_width = 800
        window_height = 800
        
        # Центрируем окно
        self.center_window(window_width, window_height)
        
        # Устанавливаем иконку (опционально)
        try:
            self.root.iconbitmap("icon.ico")  # Если есть файл иконки
        except:
            pass  # Игнорируем ошибку если иконки нет
        
        self.state = ProcessingState()
        self.state.load_from_file(CFG["STATE_FILE"])
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.create_widgets()
        self.update_ui()

    def center_window(self, width, height):
        """Центрирование главного окна на экране"""
        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Вычисляем позицию для центрирования
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Устанавливаем геометрию окна
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Устанавливаем минимальный размер окна
        self.root.minsize(600, 600)
        
    def create_widgets(self):
        # Основная рамка
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Выбор видео
        video_frame = ttk.LabelFrame(main_frame, text="Видео", padding="10")
        video_frame.pack(fill="x", pady=5)
        
        self.video_path_var = tk.StringVar()
        ttk.Entry(video_frame, textvariable=self.video_path_var, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(video_frame, text="Выбрать", command=self.select_video).pack(side="right")
        
        # Настройки клипов
        clip_frame = ttk.LabelFrame(main_frame, text="Настройки клипов", padding="10")
        clip_frame.pack(fill="x", pady=5)
        
        # Количество клипов
        ttk.Label(clip_frame, text="Количество клипов:").grid(row=0, column=0, sticky="w", pady=2)
        self.clip_count_var = tk.IntVar(value=self.state.clip_count)
        ttk.Spinbox(clip_frame, from_=1, to=50, textvariable=self.clip_count_var, width=10).grid(row=0, column=1, sticky="ew", pady=2)
        
        # Длительность клипа
        ttk.Label(clip_frame, text="Длительность клипа (с):").grid(row=1, column=0, sticky="w", pady=2)
        self.clip_duration_var = tk.DoubleVar(value=self.state.clip_duration)
        ttk.Spinbox(clip_frame, from_=10, to=300, increment=5, textvariable=self.clip_duration_var, width=10).grid(row=1, column=1, sticky="ew", pady=2)
        
        # Мин/макс длительность
        ttk.Label(clip_frame, text="Мин. длительность клипа (с):").grid(row=2, column=0, sticky="w", pady=2)
        self.min_clip_duration_var = tk.DoubleVar(value=self.state.min_clip_duration)
        ttk.Spinbox(clip_frame, from_=5, to=60, increment=1, textvariable=self.min_clip_duration_var, width=10).grid(row=2, column=1, sticky="ew", pady=2)
        
        ttk.Label(clip_frame, text="Макс. длительность клипа (с):").grid(row=3, column=0, sticky="w", pady=2)
        self.max_clip_duration_var = tk.DoubleVar(value=self.state.max_clip_duration)
        ttk.Spinbox(clip_frame, from_=10, to=300, increment=5, textvariable=self.max_clip_duration_var, width=10).grid(row=3, column=1, sticky="ew", pady=2)
        
        # Длительность анализа
        ttk.Label(clip_frame, text="Длительность анализа (с):").grid(row=4, column=0, sticky="w", pady=2)
        self.analysis_duration_var = tk.IntVar(value=self.state.analysis_duration)
        ttk.Spinbox(clip_frame, from_=60, to=3600, increment=60, textvariable=self.analysis_duration_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
        
        # Опции обработки
        options_frame = ttk.LabelFrame(main_frame, text="Опции обработки", padding="10")
        options_frame.pack(fill="x", pady=5)
        
        self.use_subtitles_var = tk.BooleanVar(value=self.state.use_subtitles)
        ttk.Checkbutton(options_frame, text="Добавлять субтитры", variable=self.use_subtitles_var).grid(row=0, column=0, sticky="w", pady=2)
        
        self.crop_to_shorts_var = tk.BooleanVar(value=self.state.crop_to_shorts)
        ttk.Checkbutton(options_frame, text="Обрезать под вертикальный формат (Shorts/Reels)", variable=self.crop_to_shorts_var).grid(row=0, column=1, sticky="w", pady=2)
        
        self.create_all_clips_var = tk.BooleanVar(value=self.state.create_all_clips)
        ttk.Checkbutton(options_frame, text="Создать все возможные клипы", variable=self.create_all_clips_var).grid(row=1, column=0, sticky="w", pady=2)
        
        self.add_frame_var = tk.BooleanVar(value=self.state.add_frame)
        ttk.Checkbutton(options_frame, text="Добавлять рамки", variable=self.add_frame_var).grid(row=1, column=1, sticky="w", pady=2)
        
        # Кнопки настроек
        settings_frame = ttk.Frame(options_frame)
        settings_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        
        ttk.Button(settings_frame, text="Настройки субтитров", command=self.open_subtitle_settings).pack(side="left", padx=5)
        ttk.Button(settings_frame, text="Настройки рамок", command=self.open_frame_settings).pack(side="left", padx=5)
        
        # Прогресс
        progress_frame = ttk.LabelFrame(main_frame, text="Прогресс обработки", padding="10")
        progress_frame.pack(fill="x", pady=5)
        
        self.stage_var = tk.StringVar(value="Готов к работе")
        ttk.Label(progress_frame, textvariable=self.stage_var).pack(anchor="w")
        
        self.substage_var = tk.StringVar()
        ttk.Label(progress_frame, textvariable=self.substage_var).pack(anchor="w")
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(anchor="e")

        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="Начать обработку", command=self.start_processing)
        self.start_btn.pack(side="left", padx=5)
        
        self.pause_btn = ttk.Button(button_frame, text="Пауза", command=self.pause_processing, state="disabled")
        self.pause_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Стоп", command=self.stop_processing, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Открыть папку с результатами", command=self.open_output_folder).pack(side="right", padx=5)        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="10")
        log_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        
        
        # Настройка колонок
        clip_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
    
    def select_video(self):
        """Выбор видео файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите видео файл",
            filetypes=[
                ("Видео файлы", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                ("Все файлы", "*.*")
            ]
        )
        if file_path:
            self.video_path_var.set(file_path)
            self.state.video_path = file_path
            self.log_message(f"✅ Видео выбран: {os.path.basename(file_path)}", "INFO")
    
    def open_subtitle_settings(self):
        """Открытие диалога настроек субтитров"""
        from models import SubtitleSettings
        current_settings = SubtitleSettings(self.state.subtitle_settings.to_dict())
        
        dialog = SubtitleSettingsDialog(self.root, self.state.subtitle_settings)
        self.root.wait_window(dialog)
        
        if dialog.result:
            self.state.subtitle_settings = dialog.result
            self.log_message("✅ Настройки субтитров обновлены", "INFO")
        else:
            self.state.subtitle_settings = current_settings
            self.log_message("ℹ️ Настройки субтитров не изменены", "INFO")
    
    def open_frame_settings(self):
        """Открытие диалога настроек рамок"""
        from models import FrameSettings
        current_settings = FrameSettings(self.state.frame_settings.to_dict())
        
        dialog = FrameSettingsDialog(self.root, self.state.frame_settings)
        self.root.wait_window(dialog)
        
        if dialog.result:
            self.state.frame_settings = dialog.result
            self.log_message("✅ Настройки рамок обновлены", "INFO")
        else:
            self.state.frame_settings = current_settings
            self.log_message("ℹ️ Настройки рамок не изменены", "INFO")
    
    def update_ui(self):
        """Обновление интерфейса в зависимости от состояния"""
        if self.state.is_processing:
            self.start_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            
            if self.state.is_paused:
                self.pause_btn.config(text="Продолжить")
            else:
                self.pause_btn.config(text="Пауза")
        else:
            self.start_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.pause_btn.config(text="Пауза")
        
        # Обновление прогресса
        self.progress_var.set(self.state.progress)
        self.progress_label.config(text=f"{self.state.progress:.1f}%")
        self.stage_var.set(self.state.current_stage)
        self.substage_var.set(self.state.current_substage)
        
        # Планируем следующее обновление
        self.root.after(100, self.update_ui)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Добавление сообщения в лог"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        self.log_text.insert("end", formatted_message + "\n")
        self.log_text.see("end")
        
        # Цветовое кодирование в зависимости от уровня
        if level == "ERROR":
            self.log_text.tag_add("error", "end-2l", "end-1l")
            self.log_text.tag_config("error", foreground="red")
        elif level == "WARNING":
            self.log_text.tag_add("warning", "end-2l", "end-1l")
            self.log_text.tag_config("warning", foreground="orange")
        elif level == "INFO":
            self.log_text.tag_add("info", "end-2l", "end-1l")
            self.log_text.tag_config("info", foreground="blue")
        elif level == "DEBUG":
            self.log_text.tag_add("debug", "end-2l", "end-1l")
            self.log_text.tag_config("debug", foreground="gray")
    
    def update_progress(self, progress: float, substage: str = ""):
        """Обновление прогресса обработки"""
        self.state.progress = progress
        self.state.current_substage = substage
    
    def start_processing(self):
        """Запуск обработки видео"""
        self.save_settings()
        
        if not self.state.video_path or not os.path.exists(self.state.video_path):
            messagebox.showerror("Ошибка", "Пожалуйста, выберите видео файл")
            return
        
        try:
            from config import OUT, CFG
            OUT.mkdir(exist_ok=True)
            CFG["TEMP_DIR"].mkdir(exist_ok=True)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать директории: {e}")
            return
        
        self.state.clear()
        self.state.video_path = self.video_path_var.get()
        
        self.processing_thread = threading.Thread(
            target=process_video_thread,
            args=(self.state, self.update_progress, self.log_message),
            daemon=True
        )
        self.processing_thread.start()
        
        self.log_message("🚀 Запуск обработки видео...", "INFO")
    
    def pause_processing(self):
        """Пауза/продолжение обработки"""
        if self.state.is_processing:
            if self.state.is_paused:
                self.state.is_paused = False
                self.log_message("▶️ Продолжение обработки", "INFO")
            else:
                self.state.is_paused = True
                self.log_message("⏸️ Обработка приостановлена", "INFO")
    
    def stop_processing(self):
        """Остановка обработки"""
        self.state.is_stopped = True
        self.log_message("🛑 Остановка обработки...", "INFO")
    
    def open_output_folder(self):
        """Открытие папки с результатами"""
        try:
            from config import OUT
            if os.path.exists(OUT):
                if os.name == 'nt':
                    os.startfile(OUT)
                elif os.name == 'posix':
                    subprocess.run(['open', OUT] if sys.platform == 'darwin' else ['xdg-open', OUT])
            else:
                messagebox.showinfo("Информация", "Папка с результатами еще не создана")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")
    
    def save_settings(self):
        """Сохранение текущих настроек"""
        self.state.clip_count = self.clip_count_var.get()
        self.state.clip_duration = self.clip_duration_var.get()
        self.state.min_clip_duration = self.min_clip_duration_var.get()
        self.state.max_clip_duration = self.max_clip_duration_var.get()
        self.state.analysis_duration = self.analysis_duration_var.get()
        self.state.use_subtitles = self.use_subtitles_var.get()
        self.state.crop_to_shorts = self.crop_to_shorts_var.get()
        self.state.create_all_clips = self.create_all_clips_var.get()
        self.state.add_frame = self.add_frame_var.get()
        
        self.state.save_to_file(CFG["STATE_FILE"])
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if self.state.is_processing:
            if messagebox.askokcancel("Выход", "Обработка еще выполняется. Вы уверены, что хотите выйти?"):
                self.state.is_stopped = True
                self.save_settings()
                self.root.destroy()
        else:
            self.save_settings()
            self.root.destroy()