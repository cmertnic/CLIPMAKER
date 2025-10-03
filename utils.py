import datetime
import logging
from config import CFG

def log(message: str, level: str = "INFO"):
    """Логирование сообщений с уровнем"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {level}: {message}"
    print(full_msg)
    logging.log(getattr(logging, level), full_msg)

def log_debug(message: str):
    """Детальное логирование (только если VERBOSE_LOGGING=True)"""
    if CFG["VERBOSE_LOGGING"]:
        log(message, "DEBUG")

def format_subtitle_text(text: str, max_chars: int = 35) -> str:
    """Форматирование текста субтитров с переносами"""
    text = ' '.join(text.split()).strip()
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        if len(' '.join(current_line + [word])) <= max_chars:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            if len(lines) >= 2:  # Максимум 2 строки
                break
    
    if current_line and len(lines) < 2:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def hex_to_rgb(hex_color: str):
    """Конвертирует HEX цвет в RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))