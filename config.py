import pathlib
import os
import subprocess
import sys
from pathlib import Path

# Автоматическое определение потоков
MAX_WORKERS = max(1, os.cpu_count() - 1)

print(f"🖥️ Используется {MAX_WORKERS} потоков (CPU: {os.cpu_count()})")

def get_asset_path(filename):
    """Получает правильный путь к файлам в exe и обычном режиме"""
    if getattr(sys, 'frozen', False):
        # В exe режиме
        base_path = Path(sys._MEIPASS)
    else:
        # В обычном режиме
        base_path = Path(__file__).parent
    
    # Пробуем несколько возможных мест
    possible_paths = [
        base_path / 'assets' / filename,
        base_path / filename,
        Path('assets') / filename,
        Path(filename)
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # Если файл не найден, возвращаем None
    return None

def get_safe_font_path(font_name):
    """Безопасное получение пути к шрифту"""
    # Если это системный шрифт (без расширения), возвращаем как есть
    if '.' not in font_name:
        return font_name
    
    # Если это файл шрифта, ищем в assets
    asset_path = get_asset_path(font_name)
    
    if asset_path and os.path.exists(asset_path):
        return asset_path
    
    # Если не нашли, пробуем системные шрифты
    try:
        import matplotlib.font_manager as fm
        system_fonts = [
            "Arial", "Helvetica", "Tahoma", "Verdana", 
            "DejaVu Sans", "Liberation Sans", "Courier New",
            "Times New Roman"
        ]
        
        for font in system_fonts:
            try:
                font_path = fm.findfont(fm.FontProperties(family=font))
                if font_path and os.path.exists(font_path):
                    print(f"✅ Используется системный шрифт: {font}")
                    return font_path
            except:
                continue
    except Exception as e:
        print(f"⚠️ Ошибка поиска системных шрифтов: {e}")
    
    # Если ничего не нашли, возвращаем стандартный Arial
    return "Arial"

# Конфигурация приложения
CFG = {
    "OUTPUT_DIR": pathlib.Path("output"),
    "TEMP_DIR": pathlib.Path("temp"),
    "STATE_FILE": pathlib.Path("state.json"),
    "SUBTITLE_SETTINGS": {
        "font": "Arial",  # Системный шрифт вместо файла
        "font_size": 52,
        "font_color": "#FFFFFF",
        "bg_color": "#000000",
        "bg_opacity": 0.7,
        "stroke_color": "#FFFFFF",
        "stroke_width": 3,
        "position": "bottom",
        "margin": 120,
        "alignment": "center",
        "whisper_model": "base",
        "language": "ru",
        "style": "boxed",
        "line_spacing": 8,
        "max_lines": 2,
        "min_segment_duration": 0.5,  
        "max_segment_duration": 15.0, 
        "animation": True,
        "fixed_size": True,
        "max_chars_per_line": 30,
        "confidence_threshold":-1.0
    },
    "FRAME_SETTINGS": {
        "add_frame": True,
        "frame_color": "#000000",
        "frame_width": 50,
        "frame_style": "solid",
        "blur_intensity": 10
    },
    "VERBOSE_LOGGING": True
}

# Настройки окружения
FFMPEG_BINARY = os.getenv('FFMPEG_BINARY', 'ffmpeg-imageio')
IMAGEMAGICK_BINARY = "C:\\Program Files\\ImageMagick-7.0.8-Q16\\magick.exe"

OUT = CFG["OUTPUT_DIR"]

def setup_imagemagick():
    """Настройка ImageMagick для MoviePy"""
    try:
        # Получаем точный путь к magick.exe
        result = subprocess.run(['where', 'magick'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            magick_path = result.stdout.strip().split('\n')[0]
            # Убедимся, что это полный путь к .exe
            if not magick_path.endswith('.exe'):
                magick_path += '.exe'
            
            print(f"✅ ImageMagick найден: {magick_path}")
            
            # Устанавливаем переменную окружения
            os.environ['IMAGEMAGICK_BINARY'] = magick_path
            
            # Принудительно настраиваем MoviePy
            try:
                from moviepy.config import change_settings
                change_settings({"IMAGEMAGICK_BINARY": magick_path})
                print(f"✅ MoviePy настроен с: {magick_path}")
            except Exception as e:
                print(f"⚠️ Ошибка настройки MoviePy: {e}")
            
            return True
        else:
            print("❌ ImageMagick не найден через 'where' команду")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка настройки ImageMagick: {e}")
        return False

def check_dependencies():
    """Проверка доступности зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    # Проверка FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg доступен")
        else:
            print("❌ FFmpeg не доступен")
    except:
        print("❌ FFmpeg не найден")
    
    # Проверка ImageMagick
    setup_imagemagick()
    
    # Проверка шрифтов
    font_path = get_safe_font_path("Arial")
    if font_path and font_path != "Arial":
        print(f"✅ Шрифты доступны: {os.path.basename(font_path)}")
    else:
        print("✅ Используются системные шрифты")

# Автоматическая проверка при импорте
if __name__ != "__main__":
    check_dependencies()