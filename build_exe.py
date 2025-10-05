import os
import subprocess
import sys
import time
import urllib.request
import zipfile
import tempfile
import shutil
from pathlib import Path

def download_with_progress(url, filename):
    """Скачивание файла с индикатором прогресса"""
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, int(downloaded * 100 / total_size))
        bar_length = 30
        filled_length = int(bar_length * percent // 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        sys.stdout.write(f'\r📥 {filename}: [{bar}] {percent}%')
        sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filename, progress_hook)
        sys.stdout.write('\n')
        return True
    except Exception as e:
        print(f"\n❌ Ошибка скачивания {filename}: {e}")
        return False

def install_ffmpeg():
    """Установка FFmpeg в папку dist"""
    ffmpeg_dir = Path('dist/ffmpeg')
    ffmpeg_exe = ffmpeg_dir / 'bin' / 'ffmpeg.exe'
    
    if ffmpeg_exe.exists():
        print("✅ FFmpeg уже установлен")
        return True
    
    print("🔧 Устанавливаем FFmpeg...")
    
    # URL для FFmpeg (официальная сборка для Windows)
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            print(f"📥 Скачиваем FFmpeg...")
            if not download_with_progress(ffmpeg_url, tmp_file.name):
                return False
            
            # Создаем временную папку для распаковки
            temp_extract = Path('ffmpeg_temp')
            if temp_extract.exists():
                shutil.rmtree(temp_extract)
            
            print("📦 Распаковываем FFmpeg...")
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
                zip_ref.extractall(temp_extract)
            
            # Находим папку с бинарниками
            bin_dir = None
            for item in temp_extract.rglob('ffmpeg.exe'):
                bin_dir = item.parent
                break
            
            if bin_dir and bin_dir.exists():
                # Копируем в целевую папку
                ffmpeg_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(bin_dir, ffmpeg_dir / 'bin')
                print("✅ FFmpeg успешно установлен")
            else:
                print("❌ Не найдены исполняемые файлы FFmpeg")
                return False
            
            # Очистка
            shutil.rmtree(temp_extract)
            os.unlink(tmp_file.name)
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка установки FFmpeg: {e}")
        return False

def install_whisper_model():
    """Скачивание модели Whisper"""
    models_dir = Path('dist/models')
    models_dir.mkdir(exist_ok=True)
    
    # Базовая модель Whisper
    model_name = "base"
    model_url = f"https://openaipublic.azureedge.net/main/whisper/models/81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524/{model_name}.pt"
    model_path = models_dir / f"{model_name}.pt"
    
    if model_path.exists():
        print(f"✅ Модель Whisper {model_name} уже загружена")
        return True
    
    print(f"🔧 Загружаем модель Whisper ({model_name})...")
    try:
        if download_with_progress(model_url, model_path):
            print(f"✅ Модель Whisper {model_name} загружена")
            return True
        else:
            print(f"❌ Не удалось загрузить модель Whisper")
            return False
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        return False

def check_python_dependencies():
    """Проверка и установка Python зависимостей"""
    print("🔍 Проверка Python зависимостей...")
    
    dependencies = [
        'torch',
        'torchvision', 
        'torchaudio',
        'openai-whisper',
        'moviepy',
        'opencv-python',
        'pydub',
        'numpy',
        'Pillow',
        'tqdm'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  📥 Устанавливаем {dep}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
                print(f"  ✅ {dep} установлен")
            except subprocess.CalledProcessError:
                print(f"  ❌ Не удалось установить {dep}")

def create_assets_folder():
    """Создает полную структуру папки assets"""
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    # Создаем подпапки
    subfolders = ['fonts', 'images', 'frames', 'icons']
    for folder in subfolders:
        (assets_dir / folder).mkdir(exist_ok=True)
    
    # Создаем базовую иконку если её нет
    icon_path = assets_dir / 'icons' / 'icon.ico'
    if not icon_path.exists():
        # Создаем простую инструкцию для иконки
        icon_help = assets_dir / 'icons' / 'README.txt'
        icon_help.write_text("""Добавьте сюда файлы иконок:
- icon.ico - основная иконка приложения (32x32, 48x48, 256x256)
- icon.png - иконка для разных размеров

Рекомендуемые инструменты:
• https://convertio.co/ru/png-ico/ - онлайн конвертер
• IcoFX - программа для создания иконок
• GIMP + плагин для ICO
""")
        print("⚠️ Иконка не найдена, создана инструкция")
    
    # Создаем README для шрифтов
    fonts_readme = assets_dir / 'fonts' / 'README.txt'
    fonts_readme.write_text("""Добавьте сюда шрифты для субтитров:
- .ttf или .otf файлы
- Рекомендуемые шрифты: Arial, Times New Roman, Roboto
- Шрифты с поддержкой эмодзи: Segoe UI Emoji, Noto Color Emoji
""")
    
    print("✅ Создана структура папки assets")

def build_exe():
    print("🚀 Запуск улучшенной сборки AI Video Clipper...")
    print("=" * 50)
    
    # Проверяем существование необходимых файлов
    required_files = [
        'main.py',
        'config.py', 
        'utils.py',
        'models.py',
        'frame_processor.py',
        'subtitle_engine.py',
        'video_processor.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        print("💡 Убедитесь, что все файлы находятся в одной папке")
        return False
    
    # Создаем папку assets если её нет
    if not Path('assets').exists():
        create_assets_folder()
    
    # Очистка предыдущих сборок
    print("🧹 Очистка предыдущих сборок...")
    for folder in ['dist', 'build', '__pycache__']:
        if os.path.exists(folder):
            try:
                # Даем время на освобождение файлов
                time.sleep(1)
                shutil.rmtree(folder)
                print(f"  ✅ Очищена папка {folder}")
            except Exception as e:
                print(f"  ⚠️ Не удалось очистить {folder}: {e}")
    
    # Проверяем и устанавливаем зависимости
    print("\n📦 Подготовка зависимостей...")
    check_python_dependencies()
    
    # Создаем команду для PyInstaller с улучшенными настройками
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        'main.py',
        '--name=AI_Video_Clipper',
        '--onefile',
        '--windowed',
        '--add-data=assets;assets',
        '--add-data=assets/*;assets/',
        '--add-data=config.py;.',
        '--add-data=utils.py;.', 
        '--add-data=models.py;.',
        '--add-data=frame_processor.py;.',
        '--add-data=subtitle_engine.py;.',
        '--add-data=video_processor.py;.',
        # Whisper зависимости
        '--hidden-import=whisper',
        '--hidden-import=whisper.audio',
        '--hidden-import=whisper.model',
        '--hidden-import=whisper.transcribe',
        '--hidden-import=whisper.decoding',
        '--hidden-import=whisper.timing',
        '--hidden-import=whisper.normalizers',
        '--hidden-import=whisper.tokenizer',
        # MoviePy зависимости
        '--hidden-import=moviepy',
        '--hidden-import=moviepy.video.io.VideoFileClip',
        '--hidden-import=moviepy.video.VideoClip',
        '--hidden-import=moviepy.video.fx.all',
        '--hidden-import=moviepy.audio.io.AudioFileClip',
        '--hidden-import=moviepy.audio.AudioClip',
        '--hidden-import=moviepy.audio.fx.all',
        # Другие зависимости
        '--hidden-import=pydub',
        '--hidden-import=pydub.utils',
        '--hidden-import=pydub.silence',
        '--hidden-import=pydub.effects',
        '--hidden-import=cv2',
        '--hidden-import=cv2.data',
        '--hidden-import=numpy',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=PIL.ImageFont',
        '--hidden-import=PIL.ImageOps',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=torch',
        '--hidden-import=torchvision',
        # Сбор данных
        '--collect-all=moviepy',
        '--collect-all=pydub', 
        '--collect-all=whisper',
        '--collect-data=whisper',
        '--collect-data=torch',
        '--collect-data=torchvision',
        '--clean',
        '--noconfirm'
    ]
    
    # Добавляем иконку если она существует
    icon_path = 'assets/icons/icon.ico'
    if os.path.exists(icon_path):
        cmd.append(f'--icon={icon_path}')
        print("✅ Используется иконка из assets")
    else:
        print("⚠️ Сборка без иконки")
    
    print(f"\n🔨 Запускаем PyInstaller...")
    print(f"Команда: {' '.join(cmd[:5])} ... [скрыто для читаемости]")
    
    try:
        # Запускаем сборку
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Сборка PyInstaller завершена успешно!")
        
        # Устанавливаем дополнительные зависимости
        print("\n🔧 Установка дополнительных компонентов...")
        install_ffmpeg()
        install_whisper_model()
        
        # Проверяем результат
        exe_path = Path('dist') / 'AI_Video_Clipper.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n🎉 Файл создан: {exe_path}")
            print(f"📁 Размер: {size_mb:.1f} MB")
            
            # Создаем инструкцию
            create_instruction_file()
            
            return True
        else:
            print("❌ EXE файл не найден!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка сборки (код {e.returncode}):")
        if e.stdout:
            # Выводим последние строки лога
            lines = e.stdout.split('\n')
            print("Последние строки лога:")
            for line in lines[-10:]:
                if line.strip():
                    print(f"  {line}")
        if e.stderr:
            print(f"STDERR: {e.stderr[-500:]}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_instruction_file():
    """Создает подробную инструкцию"""
    instruction_content = """🎯 AI Video Clipper - Полная инструкция

📁 СОДЕРЖИМОЕ ПАПКИ:
• AI_Video_Clipper.exe - главное приложение
• ffmpeg/ - движок обработки видео (автоустановка)
• models/ - модели AI для распознавания речи
• ИНСТРУКЦИЯ.txt - этот файл

🚀 БЫСТРЫЙ СТАРТ:

1. ЗАПУСК ПРИЛОЖЕНИЯ
   Дважды щелкните на AI_Video_Clipper.exe

2. ВЫБОР ВИДЕО
   • Нажмите "Выбрать видео"
   • Выберите файл (MP4, AVI, MOV, MKV)
   • Подождите загрузки

3. НАСТРОЙКИ
   • Количество клипов: 1-10
   • Длительность: 15-60 секунд
   • Анализ: всей записи или только начала
   • Формат: Shorts (9:16) или оригинал

4. ОБРАБОТКА
   • Нажмите "Начать обработку"
   • Ждите завершения (зависит от размера видео)
   • Результаты в папке "output"

🔧 АВТОМАТИЧЕСКИ УСТАНАВЛИВАЕТСЯ:

✓ FFmpeg - обработка видео и аудио
✓ Whisper AI - распознавание речи  
✓ Все Python библиотеки
✓ Модели машинного обучения

⚠️ РЕШЕНИЕ ПРОБЛЕМ:

1. Приложение не запускается
   • Проверьте антивирус (может блокировать)
   • Запустите от администратора
   • Убедитесь в наличии .NET Framework 4.5+

2. Ошибки с видео
   • Проверьте, что файл не поврежден
   • Попробуйте другой формат (MP4 лучше всего)
   • Убедитесь, что есть звуковая дорожка

3. Долгая обработка
   • Большие файлы обрабатываются дольше
   • Закройте другие программы
   • Для ускорения анализируйте только начало

🎬 ПОДДЕРЖИВАЕМЫЕ ВОЗМОЖНОСТИ:

• Автоматическое определение интересных моментов
• Распознавание речи и субтитры
• Вертикальный формат для Shorts/TikTok
• Стильные рамки для видео
• Обрезка и нарезка клипов
• Сохранение в MP4 с хорошим качеством

📞 ТЕХНИЧЕСКАЯ ПОДДЕРЖКА:

Если проблемы остаются:
1. Перезапустите приложение
2. Проверьте место на диске (нужно 2+ GB свободно)
3. Попробуйте другое видео для теста
4. Убедитесь, что все файлы в одной папке

💡 СОВЕТЫ:

• Для лучшего качества используйте MP4 с H.264
• Оптимальная длительность исходного видео: 5-30 минут
• Для точного определения моментов важен четкий звук
• Рамки добавляют профессиональный вид клипам

🎉 Удачи в создании крутых видео!"""

    instruction_path = Path('dist') / 'ИНСТРУКЦИЯ.txt'
    try:
        instruction_path.write_text(instruction_content, encoding='utf-8')
        print(f"📄 Создана инструкция: {instruction_path}")
    except Exception as e:
        print(f"⚠️ Не удалось создать инструкцию: {e}")

if __name__ == "__main__":
    print("🛠️  Улучшенный сборщик AI Video Clipper")
    print("Этот скрипт автоматически установит все зависимости!\n")
    
    # Даем время на освобождение файлов
    time.sleep(2)
    
    success = build_exe()
    
    if success:
        print("\n" + "="*50)
        print("🎊 СБОРКА ЗАВЕРШЕНА УСПЕШНО!")
        print("="*50)
        print("\n📋 Что было сделано:")
        print("  ✅ Собран EXE файл с PyInstaller")
        print("  ✅ Установлен FFmpeg для обработки видео")
        print("  ✅ Загружены модели AI для распознавания речи")
        print("  ✅ Установлены все Python зависимости")
        print("  ✅ Создана подробная инструкция")
        
        print("\n🚀 Теперь вы можете:")
        print("  1. Запустить dist/AI_Video_Clipper.exe")
        print("  2. Следовать инструкции в ИНСТРУКЦИЯ.txt")
        print("  3. Создавать крутые видео клипы!")
        
    else:
        print("\n💡 Советы по устранению ошибок:")
        print("  • Запустите командную строку от администратора")
        print("  • Убедитесь, что интернет подключен для загрузки зависимостей")
        print("  • Проверьте, что Python 3.8+ установлен корректно")
        print("  • Попробуйте: pip install --upgrade pyinstaller")
        print("  • Закройте все программы, использующие папку dist")
    
    input("\nНажмите Enter для выхода...")