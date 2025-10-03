import os
import sys
import shutil
from pathlib import Path

def fix_whisper_for_exe():
    """Исправляет пути для Whisper в exe-режиме"""
    if getattr(sys, 'frozen', False):
        # Мы в exe-режиме
        base_path = Path(sys._MEIPASS)
        
        # Создаем необходимые папки для Whisper
        whisper_assets = base_path / "whisper" / "assets"
        whisper_assets.mkdir(parents=True, exist_ok=True)
        
        # Копируем необходимые файлы Whisper
        try:
            import whisper
            whisper_path = Path(whisper.__file__).parent
            
            # Копируем все из assets оригинального Whisper
            original_assets = whisper_path / "assets"
            if original_assets.exists():
                for item in original_assets.iterdir():
                    if item.is_file():
                        shutil.copy2(item, whisper_assets / item.name)
                        print(f"✅ Скопирован файл Whisper: {item.name}")
            
            print("✅ Whisper файлы скопированы для exe-режима")
            
        except Exception as e:
            print(f"⚠️ Ошибка копирования файлов Whisper: {e}")

# Автоматически применяем фикс при импорте
fix_whisper_for_exe()