import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from utils import format_subtitle_text, log
from models import SubtitleSettings
import os
import sys
import re
from pathlib import Path

def get_asset_path(filename):
    """Получает правильный путь к файлам в exe и обычном режиме"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    
    possible_paths = [
        base_path / 'assets' / filename,
        base_path / filename,
        Path('assets') / filename,
        Path(filename)
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    return None

def get_safe_font_path(font_name):
    """Безопасное получение пути к шрифту"""
    if '.' not in font_name:
        return font_name
    
    asset_path = get_asset_path(font_name)
    if asset_path and os.path.exists(asset_path):
        return asset_path
    
    return "Arial"

def clean_subtitle_text(text):
    """Очистка и улучшение текста субтитров"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы и точки
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\.{2,}', '...', text)  # Заменяем многоточия
    
    # Удаляем очевидный мусор
    if re.match(r'^[ОоAa\.\s]+$', text):  # Только "О", "А", точки и пробелы
        return ""
    
    # Удаляем тексты, состоящие в основном из точек и коротких фрагментов
    if len(text.replace('.', '').replace(' ', '')) < 2:
        return ""
    
    # Исправляем распространенные ошибки распознавания
    replacements = {
        r'\bсщ\b': 'съ',
        r'\bщ[ия]\b': 'щи',
        r'\bпр[иі]в[еє]т\b': 'привет',
        r'\bк[ао]к\b': 'как',
        r'\bд[еэ]л[ао]\b': 'дела',
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Удаляем одиночные буквы в начале/конце (кроме предлогов)
    allowed_single_chars = {'а', 'и', 'в', 'к', 'с', 'у', 'о', 'я'}
    words = text.split()
    if len(words) > 1:
        if len(words[0]) == 1 and words[0].lower() not in allowed_single_chars:
            words = words[1:]
        if len(words[-1]) == 1 and words[-1].lower() not in allowed_single_chars:
            words = words[:-1]
        text = ' '.join(words)
    
    # Убедимся, что есть осмысленный текст
    if len(text.strip()) < 2:
        return ""
    
    # Убедимся, что первая буква заглавная
    if text and len(text) > 1:
        text = text[0].upper() + text[1:]
    
    return text

def is_garbage_text(text):
    """Определяет, является ли текст мусором"""
    if not text or len(text.strip()) < 2:
        return True
    
    # Текст состоит в основном из точек и коротких фрагментов
    clean_text = text.replace('.', '').replace(' ', '').replace(',', '').replace('!', '').replace('?', '')
    if len(clean_text) < 2:
        return True
    
    # Паттерны мусорного текста
    garbage_patterns = [
        r'^[ОоAa\.\s]+$',  # Только "О", "А", точки
        r'^\.+$',  # Только точки
        r'^[,\s\.]+$',  # Только знаки препинания
        r'^\w\s*\.\s*\w$',  # Одна буква, точка, одна буква
    ]
    
    for pattern in garbage_patterns:
        if re.match(pattern, text):
            return True
    
    return False

def create_subtitle_clip(text: str, duration: float, video_width: int, video_height: int, settings: SubtitleSettings) -> TextClip:
    """Создание субтитра с улучшенным оформлением"""
    try:
        # Очищаем и улучшаем текст
        cleaned_text = clean_subtitle_text(text)
        formatted_text = format_subtitle_text(cleaned_text, settings.max_chars_per_line)
        safe_font = get_safe_font_path(settings.font)
        
        # Стиль для белых субтитров с хорошей читаемостью
        font_color = "#FFFFFF"  # Белый
        stroke_color = "#000000"  # Черная обводка для контраста
        stroke_width = 2
        
        if settings.fixed_size:
            txt_clip = TextClip(
                formatted_text,
                fontsize=settings.font_size,
                color=font_color,
                font=safe_font,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method='caption',
                size=(video_width * 0.8, None),  # Уже для лучшей читаемости
                bg_color=settings.bg_color if hasattr(settings, 'bg_color') else None,
                transparent=not hasattr(settings, 'bg_color')
            )
        else:
            txt_clip = TextClip(
                formatted_text,
                fontsize=settings.font_size,
                color=font_color,
                font=safe_font,
                stroke_color=stroke_color,
                stroke_width=stroke_width
            )
        
        txt_clip = txt_clip.set_duration(duration)
        
        # Позиционирование - ближе к центру для лучшей видимости
        if settings.position == 'top':
            pos_y = settings.margin + 50  # Чуть ниже верха
        elif settings.position == 'bottom':
            pos_y = video_height - txt_clip.h - settings.margin - 50  # Чуть выше низа
        else:
            pos_y = (video_height - txt_clip.h) / 2
        
        if settings.alignment == 'left':
            pos_x = settings.margin + 50
        elif settings.alignment == 'right':
            pos_x = video_width - txt_clip.w - settings.margin - 50
        else:
            pos_x = (video_width - txt_clip.w) / 2
        
        txt_clip = txt_clip.set_position((pos_x, pos_y))
        
        # Плавная анимация
        if settings.animation:
            txt_clip = txt_clip.crossfadein(0.5).crossfadeout(0.5)
        
        return txt_clip
        
    except Exception as e:
        raise Exception(f"Ошибка создания субтитра: {e}")

def load_whisper_model_safe(model_name="base"):
    """Безопасная загрузка модели Whisper для exe"""
    try:
        model = whisper.load_model(model_name)
        return model
    except Exception as e:
        raise Exception(f"❌ Ошибка загрузки Whisper модели: {e}")

def transcribe_audio_safe(model, audio_path, language="ru"):
    """Транскрипция с улучшенными настройками для русского языка"""
    try:
        result = model.transcribe(
            audio_path,
            language=language if language != "auto" else "ru",  # Принудительно русский
            fp16=False,
            verbose=None,
            temperature=0.0,  # Более стабильные результаты
            best_of=3,  # Улучшает качество
            no_speech_threshold=0.6  # Лучше определяет речь
        )
        return result
        
    except Exception as e:
        # Fallback на простую транскрипцию
        try:
            result = model.transcribe(audio_path, language="ru")
            return result
        except Exception as e2:
            raise Exception(f"❌ Ошибка транскрипции: {e2}")

def add_subtitles_to_clip_advanced(clip_path: str, settings: SubtitleSettings, log_func) -> str:
    """Добавление субтитров к клипу с улучшенным качеством"""
    import time
    from config import CFG
    
    start_time = time.time()
    log_func(f"📝 Добавление субтитров к {os.path.basename(clip_path)}", "INFO")
    
    # Загружаем модель Whisper
    try:
        model = load_whisper_model_safe(settings.whisper_model)
        log_func(f"🤖 Модель Whisper загружена: {settings.whisper_model}", "INFO")
    except Exception as e:
        log_func(f"❌ Ошибка загрузки модели Whisper: {e}", "ERROR")
        return clip_path
    
    # Транскрибируем аудио с улучшенными настройками
    try:
        result = model.transcribe(
            audio_path,
            language="ru",  # Принудительно русский
            fp16=False,
            verbose=None,
            task="transcribe",  # Явно указываем транскрипцию
            no_speech_threshold=0.8,  # Более строгий порог определения речи
            logprob_threshold=-0.5  # Порог уверенности
        )
        segments = result["segments"]
        log_func(f"📄 Транскрипция: {len(segments)} сегментов", "INFO")
            
    except Exception as e:
        log_func(f"❌ Ошибка транскрипции: {e}", "ERROR")
        return clip_path
    
    # СТРОГАЯ фильтрация сегментов
    filtered_segments = []
    for seg in segments:
        duration = seg["end"] - seg["start"]
        original_text = seg["text"].strip()
        confidence = seg.get('avg_logprob', 0) if 'avg_logprob' in seg else 0
        
        # Очищаем текст
        cleaned_text = clean_subtitle_text(original_text)
        
        # СТРОГИЕ УСЛОВИЯ ФИЛЬТРАЦИИ:
        is_valid_duration = (1.0 <= duration <= 12.0)  # Более узкий диапазон
        is_not_garbage = not is_garbage_text(cleaned_text) and cleaned_text
        has_minimum_length = len(cleaned_text) >= 3  # Минимум 3 символа
        has_reasonable_confidence = confidence > -1.0  # Более строгий порог уверенности
        
        if all([is_valid_duration, is_not_garbage, has_minimum_length, has_reasonable_confidence]):
            formatted_text = format_subtitle_text(cleaned_text, settings.max_chars_per_line)
            seg["text"] = formatted_text
            filtered_segments.append(seg)
            log_func(f"✅ Сегмент: '{cleaned_text[:40]}...' ({duration:.1f}с, уверенность: {confidence:.2f})", "DEBUG")
        else:
            log_func(f"❌ Отфильтрован: '{original_text[:40]}...' (длительность: {duration:.1f}с, уверенность: {confidence:.2f})", "DEBUG")
    
    log_func(f"📄 После фильтра: {len(filtered_segments)} сегментов", "INFO")
    
    # Если нет хороших сегментов, возвращаем оригинальный клип
    if not filtered_segments:
        log_func("⚠️ Нет качественных сегментов для субтитров", "WARNING")
        return clip_path
    
    # Загружаем видео
    try:
        video = VideoFileClip(clip_path)
        video_w, video_h = video.size
        
        # Проверяем формат видео
        log_func(f"📹 Формат видео: {video_w}x{video_h}", "DEBUG")
    except Exception as e:
        log_func(f"❌ Ошибка загрузки видео: {e}", "ERROR")
        return clip_path
    
    # Создаем субтитры с обработкой ошибок
    subtitle_clips = []
    for i, segment in enumerate(filtered_segments):
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        duration = end - start
        
        try:
            txt_clip = create_subtitle_clip(text, duration, video_w, video_h, settings)
            txt_clip = txt_clip.set_start(start)
            subtitle_clips.append(txt_clip)
            log_func(f"📝 Субтитр {i+1}: '{text[:40]}...' ({start:.1f}-{end:.1f}с)", "DEBUG")
        except Exception as e:
            log_func(f"⚠️ Ошибка создания субтитра {i+1}: {e}", "WARNING")
            continue
    
    # Композитим видео с субтитрами с обработкой ошибок
    try:
        if subtitle_clips:
            # Убедимся, что все клипы имеют одинаковый размер
            final_video = CompositeVideoClip([video] + subtitle_clips)
            log_func(f"🎨 Композит: {len(subtitle_clips)} субтитров добавлено", "INFO")
        else:
            final_video = video
            log_func("⚠️ Субтитры не были созданы", "WARNING")
        
        # Сохраняем результат
        import pathlib
        original_path = pathlib.Path(clip_path)
        output_path = original_path.parent / f"{original_path.stem}_with_subs.mp4"
        
        # Явно указываем параметры видео для совместимости
        final_video.write_videofile(
            str(output_path), 
            codec="libx264", 
            audio_codec="aac", 
            verbose=False, 
            logger=None,
            threads=4,
            temp_audiofile=str(CFG["TEMP_DIR"] / "temp_audio.m4a"),
            ffmpeg_params=['-pix_fmt', 'yuv420p']  # Стандартный пиксельный формат
        )
        
        # Закрываем клипы
        video.close()
        for clip in subtitle_clips:
            clip.close()
        if subtitle_clips:
            final_video.close()
        
        process_time = time.time() - start_time
        log_func(f"✅ Субтитры добавлены: {output_path.name} (время: {process_time:.1f}с)", "INFO")
        return str(output_path)
        
    except Exception as e:
        log_func(f"❌ Ошибка сохранения видео с субтитрами: {e}", "ERROR")
        try:
            video.close()
        except:
            pass
        return clip_path