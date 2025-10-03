import os
import subprocess
import sys
from config import setup_imagemagick

def check_dependencies():
    """Проверка зависимостей"""
    try:
        # Проверяем наличие FFmpeg
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️ FFmpeg не найден. Убедитесь, что FFmpeg установлен и добавлен в PATH")
        
        # Проверяем наличие ImageMagick
        result = subprocess.run(['magick', '-version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️ ImageMagick не найден. Убедитесь, что ImageMagick установлен и добавлен в PATH")
        
    except Exception as e:
        print(f"⚠️ Ошибка проверки зависимостей: {e}")

def main():
    """Основная функция приложения"""
    # Настраиваем ImageMagick
    setup_imagemagick()
    
    # Проверяем зависимости
    check_dependencies()
    
    # Импортируем MoviePy после настройки
    try:
        from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
        from moviepy.video.fx import fadein, fadeout
        print("✅ MoviePy импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта MoviePy: {e}")
        sys.exit(1)
    
    # Импортируем остальные зависимости
    try:
        import cv2
        import numpy as np
        from pydub import AudioSegment
        import whisper
        from tqdm import tqdm
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Установите необходимые пакеты: pip install moviepy pydub tqdm opencv-python numpy openai-whisper")
        exit(1)
    
    # Запускаем приложение
    try:
        import tkinter as tk
        from ui_main import VideoClipperApp
        
        root = tk.Tk()
        app = VideoClipperApp(root)
        
        # Обработка закрытия окна
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Запуск приложения
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()