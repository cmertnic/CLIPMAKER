import tkinter as tk
from tkinter import ttk, colorchooser
from models import SubtitleSettings, FrameSettings
from PIL import Image, ImageTk
import os
class SubtitleSettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings: SubtitleSettings):
        super().__init__(parent)
        self.state('zoomed')
        self.title("Настройки субтитров")
        self.geometry("1920x1080")
        self.resizable(True, True)
        
        self.settings = settings
        self.result = None
        self.background_image = None
        self.photo_image = None
        
        self.create_widgets()
        self.load_settings()
        self.load_background_image()
        self.update_preview()
        
    def load_background_image(self):
        """Загрузка фонового изображения для предпросмотра"""
        try:
            # Создаем простое изображение с градиентом если нет файла
            from config import CFG
            assets_dir = CFG.get("ASSETS_DIR", "assets")
            image_path = os.path.join(assets_dir, "preview_bg.jpg")
            
            if os.path.exists(image_path):
                # Загружаем существующее изображение
                self.background_image = Image.open(image_path)
            else:
                # Создаем градиентное изображение
                self.create_gradient_background()
                
        except Exception as e:
            print(f"Не удалось загрузить фоновое изображение: {e}")
            self.create_gradient_background()
    
    def create_gradient_background(self):
        """Создание градиентного фона для предпросмотра"""
        try:
            # Создаем изображение с градиентом от синего к фиолетовому
            width, height = 800, 450
            image = Image.new('RGB', (width, height))
            pixels = image.load()
            
            for x in range(width):
                for y in range(height):
                    # Градиент от синего (#3498db) к фиолетовому (#9b59b6)
                    r = int(52 + (155 - 52) * y / height)
                    g = int(152 + (89 - 152) * y / height)
                    b = int(219 + (182 - 219) * y / height)
                    pixels[x, y] = (r, g, b)
            
            # Добавляем некоторые детали для реалистичности
            self.background_image = image
            
        except Exception as e:
            print(f"Не удалось создать градиентный фон: {e}")
            # Создаем простое синее изображение как запасной вариант
            self.background_image = Image.new('RGB', (800, 450), (52, 152, 219))
    
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Основные настройки
        text_frame = ttk.LabelFrame(main_frame, text="Текст", padding="10")
        text_frame.pack(fill="x", pady=5)
        
        ttk.Label(text_frame, text="Шрифт:").grid(row=0, column=0, sticky="w", pady=2)
        self.font_var = tk.StringVar()
        font_combo = ttk.Combobox(text_frame, textvariable=self.font_var, 
                    values=["Arial-Bold", "Arial", "Times-New-Roman-Bold", "Verdana-Bold", "Impact", 
                           "Helvetica-Bold", "Georgia-Bold", "Courier-Bold"])
        font_combo.grid(row=0, column=1, sticky="ew", pady=2, padx=5)
        font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        ttk.Label(text_frame, text="Размер:").grid(row=1, column=0, sticky="w", pady=2)
        self.font_size_var = tk.IntVar()
        font_size_spin = ttk.Spinbox(text_frame, from_=24, to=96, textvariable=self.font_size_var, width=15)
        font_size_spin.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        font_size_spin.bind('<KeyRelease>', lambda e: self.update_preview())
        font_size_spin.bind('<ButtonRelease>', lambda e: self.update_preview())
        
        ttk.Label(text_frame, text="Цвет:").grid(row=2, column=0, sticky="w", pady=2)
        color_frame = ttk.Frame(text_frame)
        color_frame.grid(row=2, column=1, sticky="w", pady=2, padx=5)
        self.font_color_btn = ttk.Button(color_frame, text="Выбрать", command=self.choose_font_color)
        self.font_color_btn.pack(side="left")
        self.color_preview = tk.Label(color_frame, text="     ", bg=self.settings.font_color, relief="solid", bd=1)
        self.color_preview.pack(side="left", padx=5)
        
        # Обводка
        ttk.Label(text_frame, text="Обводка:").grid(row=3, column=0, sticky="w", pady=2)
        stroke_frame = ttk.Frame(text_frame)
        stroke_frame.grid(row=3, column=1, sticky="w", pady=2, padx=5)
        
        ttk.Label(stroke_frame, text="Цвет:").pack(side="left")
        self.stroke_color_btn = ttk.Button(stroke_frame, text="Выбрать", command=self.choose_stroke_color)
        self.stroke_color_btn.pack(side="left", padx=5)
        self.stroke_color_preview = tk.Label(stroke_frame, text="     ", bg=self.settings.stroke_color, relief="solid", bd=1)
        self.stroke_color_preview.pack(side="left", padx=5)
        
        ttk.Label(stroke_frame, text="Толщина:").pack(side="left", padx=(10, 0))
        self.stroke_width_var = tk.IntVar()
        ttk.Spinbox(stroke_frame, from_=0, to=5, textvariable=self.stroke_width_var, width=5,
                   command=self.update_preview).pack(side="left", padx=5)
        
        ttk.Label(text_frame, text="Макс. символов:").grid(row=4, column=0, sticky="w", pady=2)
        self.max_chars_var = tk.IntVar()
        ttk.Spinbox(text_frame, from_=20, to=50, textvariable=self.max_chars_var, width=15,
                   command=self.update_preview).grid(row=4, column=1, sticky="ew", pady=2, padx=5)
        
        # Позиция
        position_frame = ttk.LabelFrame(main_frame, text="Позиция", padding="10")
        position_frame.pack(fill="x", pady=5)
        
        ttk.Label(position_frame, text="Позиция:").grid(row=0, column=0, sticky="w", pady=2)
        self.position_var = tk.StringVar()
        position_combo = ttk.Combobox(position_frame, textvariable=self.position_var, 
                                    values=["top", "center", "bottom"])
        position_combo.grid(row=0, column=1, sticky="ew", pady=2, padx=5)
        position_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        ttk.Label(position_frame, text="Выравнивание:").grid(row=1, column=0, sticky="w", pady=2)
        self.alignment_var = tk.StringVar()
        alignment_combo = ttk.Combobox(position_frame, textvariable=self.alignment_var, 
                                     values=["left", "center", "right"])
        alignment_combo.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        alignment_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        ttk.Label(position_frame, text="Отступ:").grid(row=2, column=0, sticky="w", pady=2)
        self.margin_var = tk.IntVar()
        margin_scale = ttk.Scale(position_frame, from_=20, to=200, variable=self.margin_var, orient="horizontal")
        margin_scale.grid(row=2, column=1, sticky="ew", pady=2, padx=5)
        margin_scale.bind('<ButtonRelease>', lambda e: self.update_preview())
        ttk.Label(position_frame, textvariable=self.margin_var, width=4).grid(row=2, column=2, sticky="w", padx=5)
        
        # Фон текста
        ttk.Label(position_frame, text="Фон текста:").grid(row=3, column=0, sticky="w", pady=2)
        bg_frame = ttk.Frame(position_frame)
        bg_frame.grid(row=3, column=1, sticky="w", pady=2, padx=5)
        
        self.bg_color_var = tk.StringVar(value="none")
        ttk.Radiobutton(bg_frame, text="Без фона", variable=self.bg_color_var, value="none",
                       command=self.update_preview).pack(side="left")
        ttk.Radiobutton(bg_frame, text="Черный", variable=self.bg_color_var, value="black",
                       command=self.update_preview).pack(side="left", padx=10)
        ttk.Radiobutton(bg_frame, text="Полупрозрачный", variable=self.bg_color_var, value="transparent",
                       command=self.update_preview).pack(side="left", padx=10)
        
        # Whisper
        whisper_frame = ttk.LabelFrame(main_frame, text="Whisper", padding="10")
        whisper_frame.pack(fill="x", pady=5)
        
        ttk.Label(whisper_frame, text="Модель:").grid(row=0, column=0, sticky="w", pady=2)
        self.whisper_model_var = tk.StringVar()
        ttk.Combobox(whisper_frame, textvariable=self.whisper_model_var, 
                    values=["tiny", "base", "small", "medium", "large"]).grid(row=0, column=1, sticky="ew", pady=2, padx=5)
        
        ttk.Label(whisper_frame, text="Язык:").grid(row=1, column=0, sticky="w", pady=2)
        self.language_var = tk.StringVar()
        ttk.Combobox(whisper_frame, textvariable=self.language_var, values=["auto", "ru", "en"]).grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        
        ttk.Label(whisper_frame, text="Порог уверенности:").grid(row=2, column=0, sticky="w", pady=2)
        self.confidence_var = tk.DoubleVar()
        ttk.Scale(whisper_frame, from_=0.0, to=1.0, variable=self.confidence_var, orient="horizontal").grid(row=2, column=1, sticky="ew", pady=2, padx=5)
        ttk.Label(whisper_frame, textvariable=self.confidence_var, width=6).grid(row=2, column=2, sticky="w", padx=5)
        
        # Опции
        options_frame = ttk.LabelFrame(main_frame, text="Опции", padding="10")
        options_frame.pack(fill="x", pady=5)
        
        self.fixed_size_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Фиксированный размер субтитров", variable=self.fixed_size_var,
                       command=self.update_preview).grid(row=0, column=0, sticky="w", pady=2)
        
        self.animation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Анимация появления", variable=self.animation_var).grid(row=1, column=0, sticky="w", pady=2)
        
        # Предпросмотр
        preview_frame = ttk.LabelFrame(main_frame, text="Предпросмотр субтитров", padding="10")
        preview_frame.pack(fill="both", expand=True, pady=10)
        
        self.preview_canvas = tk.Canvas(preview_frame, bg="#1a1a1a")
        self.preview_canvas.pack(fill="both", expand=True, pady=10)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.on_cancel).pack(side="right", padx=5)
        
        # Настройка колонок для растягивания
        for frame in [text_frame, position_frame, whisper_frame, options_frame]:
            frame.columnconfigure(1, weight=1)
        
        # Привязываем изменение размера окна к обновлению предпросмотра
        self.bind('<Configure>', lambda e: self.update_preview())
    
    def choose_font_color(self):
        color = colorchooser.askcolor(title="Выберите цвет шрифта", initialcolor=self.settings.font_color)
        if color[1]:
            self.settings.font_color = color[1]
            self.color_preview.config(bg=color[1])
            self.update_preview()
    
    def choose_stroke_color(self):
        color = colorchooser.askcolor(title="Выберите цвет обводки", initialcolor=self.settings.stroke_color)
        if color[1]:
            self.settings.stroke_color = color[1]
            self.stroke_color_preview.config(bg=color[1])
            self.update_preview()
    
    def load_settings(self):
        self.font_var.set(self.settings.font)
        self.font_size_var.set(self.settings.font_size)
        self.position_var.set(self.settings.position)
        self.alignment_var.set(self.settings.alignment)
        self.whisper_model_var.set(self.settings.whisper_model)
        self.language_var.set(self.settings.language)
        self.margin_var.set(self.settings.margin)
        self.max_chars_var.set(self.settings.max_chars_per_line)
        self.fixed_size_var.set(self.settings.fixed_size)
        self.animation_var.set(self.settings.animation)
        self.confidence_var.set(self.settings.confidence_threshold)
        self.stroke_width_var.set(self.settings.stroke_width)
        self.color_preview.config(bg=self.settings.font_color)
        self.stroke_color_preview.config(bg=self.settings.stroke_color)
    
    def save_settings(self):
        self.settings.font = self.font_var.get()
        self.settings.font_size = self.font_size_var.get()
        self.settings.position = self.position_var.get()
        self.settings.alignment = self.alignment_var.get()
        self.settings.whisper_model = self.whisper_model_var.get()
        self.settings.language = self.language_var.get()
        self.settings.margin = self.margin_var.get()
        self.settings.max_chars_per_line = self.max_chars_var.get()
        self.settings.fixed_size = self.fixed_size_var.get()
        self.settings.animation = self.animation_var.get()
        self.settings.confidence_threshold = self.confidence_var.get()
        self.settings.stroke_width = self.stroke_width_var.get()
    
    def update_preview(self, event=None):
        """Обновление предпросмотра субтитров с фоновым изображением"""
        self.preview_canvas.delete("all")
        
        # Получаем актуальные размеры canvas
        canvas_w = self.preview_canvas.winfo_width() or 600
        canvas_h = self.preview_canvas.winfo_height() or 300
        
        if canvas_w < 100 or canvas_h < 100:
            canvas_w, canvas_h = 600, 300
        
        # Рисуем фоновое изображение
        if self.background_image:
            try:
                # Масштабируем изображение под размер canvas
                bg_resized = self.background_image.copy()
                bg_resized = bg_resized.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
                self.photo_image = ImageTk.PhotoImage(bg_resized)
                self.preview_canvas.create_image(0, 0, image=self.photo_image, anchor="nw")
            except Exception as e:
                # Запасной вариант - градиентный фон
                self.preview_canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill="#34495e", outline="")
        else:
            # Градиентный фон как запасной вариант
            self.preview_canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill="#34495e", outline="")
        
        # Текст для предпросмотра
        sample_texts = [
            "Это пример текста субтитров",
            "который будет отображаться в видео"
        ]
        
        # Обрезаем текст если нужно
        max_chars = self.max_chars_var.get()
        sample_texts = [text[:max_chars] + "..." if len(text) > max_chars else text 
                       for text in sample_texts]
        
        # Параметры текста
        font_size = self.font_size_var.get()
        margin = self.margin_var.get()
        font_family = self.font_var.get()
        text_color = self.settings.font_color
        stroke_color = self.settings.stroke_color
        stroke_width = self.stroke_width_var.get()
        
        # Вычисляем общую высоту текста
        line_height = font_size * 1.2
        total_text_height = len(sample_texts) * line_height
        
        # Позиционирование текста
        if self.position_var.get() == 'top':
            y_start = margin
        elif self.position_var.get() == 'bottom':
            y_start = canvas_h - margin - total_text_height
        else:  # center
            y_start = (canvas_h - total_text_height) / 2
        
        # Выравнивание
        if self.alignment_var.get() == 'left':
            x_pos = margin
            anchor = "nw"
        elif self.alignment_var.get() == 'right':
            x_pos = canvas_w - margin
            anchor = "ne"
        else:  # center
            x_pos = canvas_w / 2
            anchor = "n"
        
        # Рисуем фон для текста если выбран
        if self.bg_color_var.get() != "none":
            # Вычисляем размеры фона
            max_line_width = max(len(text) for text in sample_texts) * font_size * 0.6
            bg_width = min(max_line_width + 40, canvas_w - margin * 2)
            bg_height = total_text_height + 20
            
            # Вычисляем позицию фона
            if anchor == "nw":
                bg_x = x_pos - 10
            elif anchor == "ne":
                bg_x = x_pos - bg_width + 10
            else:  # center
                bg_x = x_pos - bg_width / 2
            
            bg_y = y_start - 10
            
            # Рисуем фон
            if self.bg_color_var.get() == "black":
                self.preview_canvas.create_rectangle(
                    bg_x, bg_y, bg_x + bg_width, bg_y + bg_height,
                    fill="#000000", outline="", stipple=""
                )
            else:  # transparent
                self.preview_canvas.create_rectangle(
                    bg_x, bg_y, bg_x + bg_width, bg_y + bg_height,
                    fill="#000000", outline="", stipple="gray50"
                )
        
        # Рисуем текст с обводкой
        for i, text in enumerate(sample_texts):
            y_pos = y_start + i * line_height
            
            # Рисуем обводку (тень)
            if stroke_width > 0:
                for dx in [-stroke_width, 0, stroke_width]:
                    for dy in [-stroke_width, 0, stroke_width]:
                        if dx != 0 or dy != 0:
                            self.preview_canvas.create_text(
                                x_pos + dx, y_pos + dy,
                                text=text,
                                fill=stroke_color,
                                font=(font_family, font_size, "bold"),
                                anchor=anchor
                            )
            
            # Рисуем основной текст
            self.preview_canvas.create_text(
                x_pos, y_pos,
                text=text,
                fill=text_color,
                font=(font_family, font_size, "bold"),
                anchor=anchor
            )
        
        # Подпись
        self.preview_canvas.create_text(
            canvas_w/2, canvas_h - 10,
            text="Реалистичный предпросмотр субтитров на фоне видео",
            fill="#95a5a6",
            font=("Arial", 10),
            anchor="s"
        )
    
    def on_ok(self):
        self.save_settings()
        self.result = self.settings
        self.destroy()
    
    def on_cancel(self):
        self.result = None
        self.destroy()

class FrameSettingsDialog(tk.Toplevel):
    def __init__(self, parent, frame_settings: FrameSettings):
        super().__init__(parent)
        self.title("Настройки рамок")
        self.geometry("800x900")
        self.minsize(500, 550)
        self.resizable(True, True)
        
        self.frame_settings = frame_settings
        self.result = None
        
        self.create_widgets()
        self.load_settings()
        
        # Центрируем диалог
        self.transient(parent)
        self.grab_set()
        self.center_window()
    
    def center_window(self):
        """Центрирование окна на экране"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Основные настройки
        frame_frame = ttk.LabelFrame(main_frame, text="Настройки рамок", padding="10")
        frame_frame.pack(fill="x", pady=5)
        
        # Добавление рамок
        self.add_frame_var = tk.BooleanVar()
        ttk.Checkbutton(frame_frame, text="Добавлять рамки", variable=self.add_frame_var, 
                       command=self.toggle_frame_settings).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        
        # Стиль рамки
        ttk.Label(frame_frame, text="Стиль рамки:").grid(row=1, column=0, sticky="w", pady=2)
        self.frame_style_var = tk.StringVar()
        frame_style_combo = ttk.Combobox(frame_frame, textvariable=self.frame_style_var, 
                                       values=["solid", "blur"], state="readonly")
        frame_style_combo.grid(row=1, column=1, sticky="ew", pady=2, padx=5)
        frame_style_combo.bind('<<ComboboxSelected>>', self.on_style_change)
        
        # Цвет рамки (только для solid)
        ttk.Label(frame_frame, text="Цвет рамки:").grid(row=2, column=0, sticky="w", pady=2)
        color_frame = ttk.Frame(frame_frame)
        color_frame.grid(row=2, column=1, sticky="w", pady=2, padx=5)
        self.frame_color_btn = ttk.Button(color_frame, text="Выбрать", command=self.choose_frame_color)
        self.frame_color_btn.pack(side="left")
        self.frame_color_preview = tk.Label(color_frame, text="     ", bg=self.frame_settings.frame_color, relief="solid", bd=1)
        self.frame_color_preview.pack(side="left", padx=5)
        
        # Ширина рамки (только для solid)
        ttk.Label(frame_frame, text="Ширина рамки:").grid(row=3, column=0, sticky="w", pady=2)
        self.frame_width_var = tk.IntVar()
        frame_width_scale = ttk.Scale(frame_frame, from_=10, to=200, variable=self.frame_width_var, orient="horizontal")
        frame_width_scale.grid(row=3, column=1, sticky="ew", pady=2, padx=5)
        frame_width_scale.bind('<ButtonRelease>', lambda e: self.update_preview())
        self.frame_width_label = ttk.Label(frame_frame, textvariable=self.frame_width_var)
        self.frame_width_label.grid(row=3, column=2, sticky="w", padx=5)
        
        # Интенсивность размытия (только для blur)
        ttk.Label(frame_frame, text="Интенсивность размытия:").grid(row=4, column=0, sticky="w", pady=2)
        self.blur_intensity_var = tk.IntVar()
        blur_scale = ttk.Scale(frame_frame, from_=5, to=50, variable=self.blur_intensity_var, orient="horizontal")
        blur_scale.grid(row=4, column=1, sticky="ew", pady=2, padx=5)
        blur_scale.bind('<ButtonRelease>', lambda e: self.update_preview())
        self.blur_intensity_label = ttk.Label(frame_frame, textvariable=self.blur_intensity_var)
        self.blur_intensity_label.grid(row=4, column=2, sticky="w", padx=5)
        
        # Предпросмотр
        preview_frame = ttk.LabelFrame(main_frame, text="Предпросмотр рамок", padding="10")
        preview_frame.pack(fill="both", expand=True, pady=10)
        
        self.preview_canvas = tk.Canvas(preview_frame, bg="white")
        self.preview_canvas.pack(fill="both", expand=True, pady=10)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Применить", command=self.on_apply).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.on_cancel).pack(side="right", padx=5)
        
        # Настройка колонок
        frame_frame.columnconfigure(1, weight=1)
        
        # Обновляем предпросмотр
        self.update_preview()
        
        # Привязываем изменение размера окна к обновлению предпросмотра
        self.bind('<Configure>', lambda e: self.update_preview())
    
    def toggle_frame_settings(self):
        """Включение/выключение настроек рамок"""
        state = "normal" if self.add_frame_var.get() else "disabled"
        
        for widget in [self.frame_style_var, self.frame_color_btn, self.frame_width_var, self.blur_intensity_var]:
            if hasattr(widget, 'configure'):
                widget.configure(state=state)
        
        self.update_preview()
    
    def on_style_change(self, event=None):
        """Изменение стиля рамки"""
        self.update_preview()
    
    def choose_frame_color(self):
        color = colorchooser.askcolor(title="Выберите цвет рамки", initialcolor=self.frame_settings.frame_color)
        if color[1]:
            self.frame_settings.frame_color = color[1]
            self.frame_color_preview.config(bg=color[1])
            self.update_preview()
    
    def load_settings(self):
        self.add_frame_var.set(self.frame_settings.add_frame)
        self.frame_style_var.set(self.frame_settings.frame_style)
        self.frame_width_var.set(self.frame_settings.frame_width)
        self.blur_intensity_var.set(self.frame_settings.blur_intensity)
        self.frame_color_preview.config(bg=self.frame_settings.frame_color)
        self.toggle_frame_settings()
    
    def save_settings(self):
        self.frame_settings.add_frame = self.add_frame_var.get()
        self.frame_settings.frame_style = self.frame_style_var.get()
        self.frame_settings.frame_width = self.frame_width_var.get()
        self.frame_settings.blur_intensity = self.blur_intensity_var.get()
    
    def update_preview(self, event=None):
        """Обновление предпросмотра рамки"""
        self.preview_canvas.delete("all")
        
        # Получаем актуальные размеры canvas
        canvas_w = self.preview_canvas.winfo_width() or 460
        canvas_h = self.preview_canvas.winfo_height() or 250
        
        if canvas_w < 100 or canvas_h < 100:
            canvas_w, canvas_h = 460, 250
        
        # Рисуем фон
        self.preview_canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill="#f0f0f0", outline="")
        
        if self.add_frame_var.get():
            if self.frame_style_var.get() == "solid":
                # Рисуем сплошную рамку
                frame_color = self.frame_settings.frame_color
                frame_width = min(self.frame_width_var.get() / 200 * canvas_h, canvas_h * 0.4)
                
                # Рисуем рамки сверху и снизу
                self.preview_canvas.create_rectangle(0, 0, canvas_w, frame_width, fill=frame_color, outline="")
                self.preview_canvas.create_rectangle(0, canvas_h - frame_width, canvas_w, canvas_h, fill=frame_color, outline="")
                
                # Рисуем центральную область (видео)
                video_w = canvas_w
                video_h = canvas_h - 2 * frame_width
                if video_h > 0:
                    self.preview_canvas.create_rectangle(0, frame_width, video_w, frame_width + video_h, fill="#3498db", outline="")
                
                # Текст
                self.preview_canvas.create_text(canvas_w/2, canvas_h/2, text="ВИДЕО", fill="white", font=("Arial", 16, "bold"))
                self.preview_canvas.create_text(canvas_w/2, 15, text="Сплошные рамки", fill="white", font=("Arial", 10, "bold"))
                
            else:
                # Рисуем размытый фон
                self.preview_canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill="#2c3e50", outline="")
                
                # Рисуем центральную область (видео)
                video_w = canvas_w * 0.8
                video_h = canvas_h * 0.6
                video_x = (canvas_w - video_w) / 2
                video_y = (canvas_h - video_h) / 2
                
                self.preview_canvas.create_rectangle(video_x, video_y, video_x + video_w, video_y + video_h, 
                                                   fill="#3498db", outline="white", width=3)
                
                # Текст
                self.preview_canvas.create_text(canvas_w/2, canvas_h/2, text="ВИДЕО", fill="white", font=("Arial", 16, "bold"))
                self.preview_canvas.create_text(canvas_w/2, 20, text="Размытый фон", fill="white", font=("Arial", 12, "bold"))
                
                # Эффект размытия
                blur_intensity = min(self.blur_intensity_var.get() / 2, 10)
                for i in range(int(blur_intensity)):
                    blur_offset = i * 2
                    self.preview_canvas.create_rectangle(
                        video_x - blur_offset, video_y - blur_offset,
                        video_x + video_w + blur_offset, video_y + video_h + blur_offset,
                        outline="#34495e", width=1
                    )
        else:
            # Без рамок - просто видео
            self.preview_canvas.create_rectangle(0, 0, canvas_w, canvas_h, fill="#3498db", outline="")
            self.preview_canvas.create_text(canvas_w/2, canvas_h/2, text="ВИДЕО\n(без рамок)", fill="white", 
                                          font=("Arial", 16, "bold"), justify="center")
        
        # Подпись
        self.preview_canvas.create_text(
            canvas_w/2, canvas_h - 10,
            text="Предпросмотр вертикального формата (9:16)",
            fill="#7f8c8d",
            font=("Arial", 9),
            anchor="s"
        )
    
    def on_ok(self):
        self.save_settings()
        self.result = self.frame_settings
        self.destroy()
    
    def on_apply(self):
        """Применить настройки без закрытия окна"""
        self.save_settings()
        self.result = self.frame_settings
        self.update_preview()
    
    def on_cancel(self):
        self.result = None
        self.destroy()