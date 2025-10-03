from pathlib import Path

def create_default_assets():
    """Создает базовую структуру папки assets"""
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    # Создаем README для шрифтов
    readme = assets_dir / 'FONTS_README.txt'
    readme.write_text("""Шрифты для субтитров

Для использования кастомных шрифтов:
1. Скачайте .ttf файлы шрифтов
2. Поместите в эту папку
3. В config.py укажите имя файла в настройках font

Рекомендуемые шрифты:
- Arial.ttf (уже доступен в системе)
- Roboto-Regular.ttf 
- OpenSans-Regular.ttf

Скачать бесплатные шрифты:
https://fonts.google.com/
""", encoding='utf-8')
    
    print("✅ Создана структура папки assets")

if __name__ == "__main__":
    create_default_assets()