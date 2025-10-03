import os
import subprocess
import sys
import time
from pathlib import Path

def build_exe():
    print("🚀 Сборка AI Video Clipper...")
    
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
        return False
    
    # Проверяем папку assets
    assets_dir = Path('assets')
    if not assets_dir.exists():
        print("⚠️ Папка assets не найдена, создаем...")
        assets_dir.mkdir(exist_ok=True)
        # Создаем простую иконку если нет
        icon_path = assets_dir / 'icon.ico'
        if not icon_path.exists():
            print("⚠️ Иконка не найдена, сборка продолжится без нее")
    
    # Очистка предыдущих сборок
    for folder in ['dist', 'build', '__pycache__']:
        if os.path.exists(folder):
            try:
                import shutil
                shutil.rmtree(folder)
                print(f"✅ Очищена папка {folder}")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Не удалось очистить {folder}: {e}")
    
    # Создаем команду для PyInstaller
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
        '--hidden-import=whisper',
        '--hidden-import=whisper.audio',
        '--hidden-import=whisper.model',
        '--hidden-import=whisper.transcribe',
        '--hidden-import=whisper.decoding',
        '--hidden-import=whisper.timing',
        '--hidden-import=config',
        '--hidden-import=utils',
        '--hidden-import=models', 
        '--hidden-import=frame_processor',
        '--hidden-import=subtitle_engine',
        '--hidden-import=video_processor',
        '--hidden-import=moviepy.video.io.VideoFileClip',
        '--hidden-import=moviepy.video.VideoClip',
        '--hidden-import=moviepy.video.fx.all',
        '--hidden-import=pydub.utils',
        '--hidden-import=pydub.silence',
        '--hidden-import=cv2',
        '--hidden-import=cv2.data',
        '--hidden-import=numpy',
        '--hidden-import=PIL',
        '--hidden-import=tkinter',
        '--collect-all=moviepy', 
        '--collect-data=whisper',
        '--clean',
        '--noconfirm'
    ]
    
    # Добавляем иконку если она существует
    icon_path = 'assets/icon.ico'
    if os.path.exists(icon_path):
        cmd.append(f'--icon={icon_path}')
        print("✅ Используется иконка из assets")
    else:
        print("⚠️ Сборка без иконки")
    
    # Добавляем папку assets если она существует и не пуста
    if assets_dir.exists() and any(assets_dir.iterdir()):
        cmd.append('--add-data=assets;assets')
        print("✅ Добавлена папка assets")
    
    print("🔨 Запускаем PyInstaller...")
    print(f"Команда: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Сборка завершена успешно!")
        
        # Проверяем результат
        exe_path = Path('dist') / 'AI_Video_Clipper.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"🎉 Файл создан: {exe_path}")
            print(f"📁 Размер: {size_mb:.1f} MB")
            
            # Создаем инструкцию
            create_instruction_file()
            
            # Проверяем зависимости
            print("🔍 Проверяем основные зависимости...")
            check_dependencies()
            
            return True
        else:
            print("❌ EXE файл не найден!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки (код {e.returncode}):")
        if e.stdout:
            print(f"STDOUT: {e.stdout[-500:]}")  # Последние 500 символов
        if e.stderr:
            print(f"STDERR: {e.stderr[-500:]}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def check_dependencies():
    """Проверка основных зависимостей"""
    deps = [
        'cv2', 'numpy', 'moviepy', 'pydub', 'PIL', 'tkinter'
    ]
    
    print("📦 Проверка зависимостей в системе:")
    for dep in deps:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError as e:
            print(f"  ❌ {dep}: {e}")

def create_assets_folder():
    """Создает базовую структуру папки assets"""
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    # Создаем README для assets
    readme = assets_dir / 'README.txt'
    readme.write_text("""Папка для ресурсов приложения

Разместите здесь:
- icon.ico - иконка приложения
- fonts/ - шрифты для субтитров  
- images/ - изображения для интерфейса
- frames/ - рамки для видео

Для иконки можно использовать онлайн-конвертер:
https://convertio.co/ru/png-ico/
""")
    print("✅ Создана папка assets с инструкцией")

def create_instruction_file():
    """Создает файл инструкции после успешной сборки"""
    instruction_content = """🎯 AI Video Clipper - Инструкция по использованию

📁 РАСПОЛОЖЕНИЕ ФАЙЛОВ:
• AI_Video_Clipper.exe - главный исполняемый файл
• assets/ - папка с ресурсами (иконки, шрифты, рамки)

🚀 ЗАПУСК ПРИЛОЖЕНИЯ:
1. Дважды щелкните на AI_Video_Clipper.exe
2. Или запустите из командной строки: AI_Video_Clipper.exe

🎬 КАК ИСПОЛЬЗОВАТЬ:

1. ВЫБОР ВИДЕО
   • Нажмите "Выбрать видео" и выберите файл
   • Поддерживаются: MP4, AVI, MOV, MKV

2. НАСТРОЙКИ ОБРАБОТКИ
   • Количество клипов: сколько моментов найти (1-10)
   • Длительность клипа: продолжительность каждого клипа
   • Анализ первых: анализировать только начало видео
   • Создать все клипы: найти все возможные моменты

3. ФОРМАТ ВЫВОДА
   • Shorts/TikTok: вертикальное видео 9:16
   • Добавить рамку: стильные рамки вокруг видео
   • Субтитры: автоматическое распознавание речи

4. ОБРАБОТКА
   • Нажмите "Начать обработку"
   • Дождитесь завершения анализа и создания клипов
   • Готовые клипы появятся в папке "output"

⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ:

• Для работы нужны ffmpeg.exe и ffprobe.exe в той же папке
• Видео должно иметь звуковую дорожку для анализа аудио
• Большие видеофайлы обрабатываются дольше
• Рекомендуется использовать видео до 1 часа

🔧 ЕСЛИ ВОЗНИКЛИ ПРОБЛЕМЫ:

1. Проверьте, что ffmpeg.exe есть в папке
2. Убедитесь, что видеофайл не поврежден
3. Попробуйте перезапустить приложение
4. Для больших видео увеличьте время анализа

📞 ПОДДЕРЖКА:
Если проблемы сохраняются, проверьте:
1. Наличие всех DLL файлов
2. Достаточно ли места на диске
3. Не блокирует ли антивирус приложение

🎉 Успешного использования!"""
    
    instruction_path = Path('dist') / 'ИНСТРУКЦИЯ.txt'
    try:
        instruction_path.write_text(instruction_content, encoding='utf-8')
        print(f"📄 Создана инструкция: {instruction_path}")
    except Exception as e:
        print(f"⚠️ Не удалось создать инструкцию: {e}")

if __name__ == "__main__":
    # Создаем папку assets если её нет
    if not Path('assets').exists():
        create_assets_folder()
    
    # Даем время на освобождение файлов
    time.sleep(2)
    
    success = build_exe()
    
    if success:
        print("\n🎊 Сборка завершена успешно!")
        print("💡 Советы:")
        print("  - Если есть проблемы с запуском, попробуйте:")
        print("    python main.py (для проверки исходного кода)")
        print("  - EXE файл в папке: dist/AI_Video_Clipper.exe")
        print("  - Инструкция создана: dist/ИНСТРУКЦИЯ.txt")
    else:
        print("\n💡 Советы по устранению ошибок:")
        print("  - Убедитесь что все файлы .py в той же папке")
        print("  - Закройте все программы, использующие папку dist")
        print("  - Попробуйте запустить командную строку от администратора")
        print("  - Проверьте что Python и PyInstaller установлены корректно")
    
    input("\nНажмите Enter для выхода...")