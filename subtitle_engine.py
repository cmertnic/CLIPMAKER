import pathlib
import time
from config import CFG
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from utils import format_subtitle_text, log
from models import SubtitleSettings
import os
import sys
import re
import random
from pathlib import Path
from typing import List, Tuple

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

def improve_text_grammar(text):
    """Улучшает грамматику текста"""
    if not text:
        return ""
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Исправляем распространенные ошибки
    corrections = {
        r'\bсщ\b': 'сч',
        r'\bзщ\b': 'зч', 
        r'\bжщ\b': 'жч',
        r'\b([кст])([кст])\b': r'\1\2',  # двойные согласные
        r'\b([а-я])\1+\b': r'\1',  # убираем повторяющиеся буквы
    }
    
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)
    
    # Добавляем заглавные буквы в начале предложений
    sentences = re.split(r'([.!?]+\s*)', text)
    result = []
    capitalize_next = True
    
    for part in sentences:
        if capitalize_next and part.strip():
            part = part[0].upper() + part[1:] if part else part
            capitalize_next = False
        if part.strip().endswith(('.', '!', '?')):
            capitalize_next = True
        result.append(part)
    
    text = ''.join(result)
    
    return text

def clean_subtitle_text(text):
    """Улучшенная очистка текста субтитров с грамматической коррекцией"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Удаляем лишние знаки препинания в конце
    text = re.sub(r'[\.\!\?]+$', '', text)
    
    # Удаляем очевидный мусор
    if re.match(r'^[\.\s!?,]+$', text):
        return ""
    
    # Улучшаем грамматику
    text = improve_text_grammar(text)
    
    # Убираем короткие бессмысленные фразы
    meaningless_phrases = ['а', 'но', 'и', 'да', 'нет', 'ну', 'вот', 'это', 'то']
    if text.lower() in meaningless_phrases:
        return ""
    
    return text

def is_garbage_text(text):
    """Определяет, является ли текст мусором"""
    if not text or len(text.strip()) < 2:
        return True
    
    # Текст состоит в основном из пунктуации
    clean_text = re.sub(r'[\.\s!?,]', '', text)
    if len(clean_text) < 2:
        return True
    
    # Проверяем на набор случайных символов
    if re.match(r'^[а-я]*[a-z]+[а-я]*$', text.lower()):
        return True
    
    return False

def load_whisper_model_safe(model_name="base"):
    """Безопасная загрузка модели Whisper"""
    try:
        model = whisper.load_model(model_name)
        return model
    except Exception as e:
        raise Exception(f"❌ Ошибка загрузки Whisper модели: {e}")

def transcribe_audio_with_word_timestamps(model, audio_path, language="ru"):
    """Транскрипция с временными метками для каждого слова"""
    try:
        result = model.transcribe(
            audio_path,
            language=language if language != "auto" else "ru",
            fp16=False,
            verbose=None,
            word_timestamps=True
        )
        return result
    except Exception as e:
        # Fallback на обычную транскрипцию
        try:
            result = model.transcribe(
                audio_path,
                language=language if language != "auto" else "ru",
                fp16=False,
                verbose=None
            )
            return result
        except Exception as e2:
            raise Exception(f"❌ Ошибка транскрипции: {e2}")

def ensure_even_dimensions(width, height):
    """Убеждаемся, что ширина и высота четные числа"""
    width = width if width % 2 == 0 else width - 1
    height = height if height % 2 == 0 else height - 1
    return int(width), int(height)

def resize_to_even_dimensions(clip):
    """Изменяет размер клипа до четных размеров"""
    width, height = clip.size
    new_width, new_height = ensure_even_dimensions(width, height)
    
    if (new_width, new_height) != (width, height):
        return clip.resize(newsize=(new_width, new_height))
    return clip

def safe_video_loading(clip_path: str):
    """Безопасная загрузка видео с обработкой ошибок"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            video = VideoFileClip(clip_path, audio_fps=22050)
            
            # Проверяем корректность видео
            if video.duration <= 0:
                raise ValueError("Нулевая длительность видео")
                
            video = resize_to_even_dimensions(video)
            return video
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(0.5)
            continue

def detect_speech_activity(audio_path, threshold=0.01):
    """Обнаружение речевой активности для точной синхронизации"""
    try:
        from pydub import AudioSegment
        from pydub.silence import detect_nonsilent
        
        # Загружаем аудио
        audio = AudioSegment.from_file(audio_path)
        
        # Обнаруживаем не-тихие сегменты (речь)
        nonsilent_segments = detect_nonsilent(
            audio, 
            min_silence_len=100,  # 100ms тишины
            silence_thresh=threshold * audio.dBFS  # Порог тишины
        )
        
        # Конвертируем в секунды
        speech_segments = [(start/1000, end/1000) for start, end in nonsilent_segments]
        return speech_segments
        
    except Exception as e:
        print(f"⚠️ Ошибка детектирования речи: {e}")
        return []

def create_phrase_subtitles(segments, video_width: int, video_height: int, settings: SubtitleSettings, speech_segments=None) -> List[TextClip]:
    """Создает субтитры фразами с синхронизацией по голосу"""
    subtitle_clips = []
    
    for i, segment in enumerate(segments):
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()
        
        # Пропускаем слишком короткие или мусорные сегменты
        duration = end - start
        if duration < 0.3 or is_garbage_text(text):
            continue
        
        # Очищаем и улучшаем текст
        cleaned_text = clean_subtitle_text(text)
        if not cleaned_text:
            continue
        
        # Проверяем, есть ли речь в этом сегменте (если доступны данные о речи)
        if speech_segments:
            has_speech = any(
                speech_start <= end and speech_end >= start 
                for speech_start, speech_end in speech_segments
            )
            if not has_speech:
                continue  # Пропускаем субтитры без речи
        
        try:
            # Создаем субтитр для одной фразы
            subtitle_clip = create_single_subtitle_clip(
                cleaned_text, 
                duration,
                video_width, video_height, settings
            )
            subtitle_clip = subtitle_clip.set_start(start)
            subtitle_clips.append(subtitle_clip)
            
        except Exception as e:
            continue
    
    return subtitle_clips

def create_single_subtitle_clip(text: str, duration: float, video_width: int, video_height: int, settings: SubtitleSettings) -> TextClip:
    """Создание одного субтитра"""
    try:
        # Форматируем текст (максимум 2 строки)
        formatted_text = format_subtitle_text(text, settings.max_chars_per_line)
        
        # Получаем безопасный путь к шрифту
        safe_font = get_safe_font_path(settings.font)
        
        # Создаем текстовый клип с белым текстом и тонкой черной обводкой для читаемости
        txt_clip = TextClip(
            formatted_text,
            fontsize=settings.font_size,
            color='white',
            font=safe_font,
            stroke_color='black',  # Тонкая обводка для контраста
            stroke_width=1.5,      # Улучшает читаемость
            method='caption',
            size=(video_width * 0.9, None)
        )
        
        # Устанавливаем точную длительность
        txt_clip = txt_clip.set_duration(duration)
        
        # Позиционирование внизу с небольшим отступом
        pos_y = video_height - txt_clip.h - settings.margin
        pos_x = (video_width - txt_clip.w) / 2
        
        txt_clip = txt_clip.set_position((pos_x, pos_y))
        
        return txt_clip
        
    except Exception as e:
        raise Exception(f"Ошибка создания субтитра: {e}")

def extract_phrases_from_segments(segments, min_duration=0.5, max_duration=8.0):
    """Улучшенное извлечение фраз из сегментов с грамматической коррекцией"""
    phrases = []
    
    for i, segment in enumerate(segments):
        text = segment.get('text', '').strip()
        start = segment['start']
        end = segment['end']
        duration = end - start
        
        # Пропускаем мусор и слишком короткие/длинные сегменты
        if (is_garbage_text(text) or 
            duration < min_duration or 
            duration > max_duration):
            continue
        
        # Очищаем и улучшаем текст
        cleaned_text = clean_subtitle_text(text)
        if not cleaned_text:
            continue
        
        # Корректируем время отображения на основе содержания
        extended_end = end
        
        # Автоматически определяем оптимальное время отображения
        word_count = len(cleaned_text.split())
        base_duration = max(duration, word_count * 0.4)  # Минимум 0.4 сек на слово
        
        if i == len(segments) - 1:
            # Последняя фраза - продлеваем
            extended_end = end + min(2.0, base_duration * 0.3)
        else:
            next_start = segments[i + 1]['start']
            gap = next_start - end
            
            # Продлеваем если большой промежуток
            if gap > 1.5:
                extended_end = end + min(gap * 0.6, 3.0)
            else:
                extended_end = end + min(base_duration * 0.2, 1.0)
        
        # Объединяем короткие последовательные фразы
        if phrases and (start - phrases[-1]['end']) < 0.5:
            last_phrase = phrases[-1]
            combined_text = last_phrase['text'] + ' ' + cleaned_text
            
            # Проверяем длину и логичность объединения
            if (len(combined_text) <= 80 and 
                len(combined_text.split()) <= 12 and
                not re.search(r'[.!?]\s*[а-я]', last_phrase['text'])):  # Не объединяем разные предложения
                
                last_phrase['text'] = combined_text
                last_phrase['end'] = extended_end
                continue
        
        # Добавляем как новую фразу
        phrases.append({
            'text': cleaned_text,
            'start': start,
            'end': extended_end
        })
    
    return phrases

def safe_video_export(final_video, output_path, log_func):
    """Безопасный экспорт видео с обработкой ошибок"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Убеждаемся, что финальное видео имеет четные размеры
            final_video = resize_to_even_dimensions(final_video)
            
            # Используем многопоточность (все ядра кроме 1)
            import multiprocessing
            available_threads = max(multiprocessing.cpu_count() - 1, 1)
            
            log_func(f"⚡ Используется {available_threads} потоков для экспорта", "INFO")
            
            # Упрощенные настройки экспорта для стабильности
            final_video.write_videofile(
                str(output_path), 
                codec="libx264", 
                audio_codec="aac", 
                verbose=False, 
                logger=None,
                threads=available_threads,  # Используем все ядра кроме 1
                preset='fast',
                ffmpeg_params=[
                    '-pix_fmt', 'yuv420p',
                    '-crf', '23',
                    '-movflags', '+faststart',
                    '-avoid_negative_ts', 'make_zero',
                    '-max_muxing_queue_size', '1024'
                ]
            )
            return True
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            log_func(f"⚠️ Повторная попытка экспорта ({attempt + 1}/2)...", "WARNING")
            time.sleep(1)
            continue

def crop_to_shorts_format(clip, log_func):
    """Старая проверенная обрезка под вертикальный формат с solid рамками"""
    width, height = clip.size
    
    log_func(f"📏 Исходное разрешение: {width}x{height}", "INFO")
    
    # Целевое соотношение для Shorts (9:16)
    target_ratio = 9/16
    current_ratio = width / height
    
    # Вычисляем новые размеры
    if current_ratio > target_ratio:
        # Видео слишком широкое - обрезаем по бокам
        new_width = int(height * target_ratio)
        new_height = height
        x_center = width // 2
        x1 = x_center - new_width // 2
        x2 = x1 + new_width
        cropped_clip = clip.crop(x1=x1, y1=0, x2=x2, y2=height)
    else:
        # Видео слишком высокое - обрезаем сверху и снизу
        new_width = width
        new_height = int(width / target_ratio)
        y_center = height // 2
        y1 = y_center - new_height // 2
        y2 = y1 + new_height
        cropped_clip = clip.crop(x1=0, y1=y1, x2=width, y2=y2)
    
    # Изменяем размер к стандартному вертикальному разрешению
    final_clip = cropped_clip.resize(height=1920)
    
    log_func(f"🎯 Обрезка под Shorts: {final_clip.w}x{final_clip.h}", "INFO")
    return final_clip

def add_subtitles_to_clip_advanced(clip_path: str, settings: SubtitleSettings, log_func) -> str:
    """Добавление субтитров фразами с улучшенной грамматикой и синхронизацией по голосу"""
    start_time = time.time()
    log_func(f"📝 Добавление улучшенных субтитров к {pathlib.Path(clip_path).name}", "INFO")
    
    # Загружаем модель Whisper
    try:
        model = whisper.load_model(settings.whisper_model)
        log_func(f"🤖 Модель Whisper загружена: {settings.whisper_model}", "INFO")
    except Exception as e:
        log_func(f"❌ Ошибка загрузки модели Whisper: {e}", "ERROR")
        return clip_path
    
    # Транскрибируем аудио
    try:
        result = transcribe_audio_with_word_timestamps(
            model, clip_path, 
            language=settings.language if settings.language != "auto" else None
        )
        segments = result["segments"]
        log_func(f"📄 Транскрипция: {len(segments)} сегментов", "INFO")
        
    except Exception as e:
        log_func(f"❌ Ошибка транскрипции: {e}", "ERROR")
        return clip_path
    
    # Детектируем речевую активность для точной синхронизации
    speech_segments = []
    try:
        speech_segments = detect_speech_activity(clip_path)
        log_func(f"🎤 Обнаружено {len(speech_segments)} сегментов речи", "INFO")
    except Exception as e:
        log_func(f"⚠️ Детектирование речи недоступно: {e}", "WARNING")
    
    # Извлекаем и улучшаем фразы
    phrases = extract_phrases_from_segments(segments)
    log_func(f"💬 Извлечено {len(phrases)} улучшенных фраз", "INFO")
    
    # Логируем примеры улучшенных фраз
    for i, phrase in enumerate(phrases[:3]):
        log_func(f"📝 Фраза {i+1}: '{phrase['text']}'", "DEBUG")
    
    if not phrases:
        log_func("ℹ️ Не найдено фраз для субтитров", "INFO")
        return clip_path
    
    # Загружаем видео с безопасной обработкой
    try:
        video = safe_video_loading(clip_path)
        original_w, original_h = video.size
        log_func(f"🎬 Видео загружено: {original_w}x{original_h}, длительность: {video.duration:.2f}с", "INFO")
        
        # Обрезаем под Shorts формат
        video = crop_to_shorts_format(video, log_func)
        video_w, video_h = video.size
        
    except Exception as e:
        log_func(f"❌ Ошибка загрузки видео: {e}", "ERROR")
        return clip_path
    
    # Создаем субтитры фразами с синхронизацией по голосу
    try:
        phrase_segments = [
            {'start': p['start'], 'end': p['end'], 'text': p['text']}
            for p in phrases
        ]
        
        subtitle_clips = create_phrase_subtitles(
            phrase_segments, video_w, video_h, settings, speech_segments
        )
        log_func(f"🎬 Создано {len(subtitle_clips)} синхронизированных субтитров", "INFO")
        
    except Exception as e:
        log_func(f"❌ Ошибка создания субтитров: {e}", "ERROR")
        subtitle_clips = []
    
    # Композитим видео с субтитрами
    try:
        if subtitle_clips:
            final_video = CompositeVideoClip([video] + subtitle_clips)
            log_func(f"🎨 Композит: {len(subtitle_clips)} фраз добавлено", "INFO")
        else:
            final_video = video
            log_func("⚠️ Субтитры не были созданы", "WARNING")
        
        # Сохраняем результат
        original_path = pathlib.Path(clip_path)
        output_path = original_path.parent / f"{original_path.stem}_with_subs.mp4"
        
        # Безопасный экспорт
        safe_video_export(final_video, output_path, log_func)
        
        # Закрываем клипы
        video.close()
        for clip in subtitle_clips:
            clip.close()
        if subtitle_clips:
            final_video.close()
        
        process_time = time.time() - start_time
        log_func(f"✅ Улучшенные субтитры добавлены: {output_path.name} (время: {process_time:.1f}с)", "INFO")
        return str(output_path)
        
    except Exception as e:
        log_func(f"❌ Ошибка сохранения видео с субтитрами: {e}", "ERROR")
        try:
            video.close()
            if 'final_video' in locals():
                final_video.close()
        except:
            pass
        
        return clip_path

def create_simple_compatible_video(input_path, log_func):
    """Создает простую совместимую версию видео"""
    try:
        log_func("🔄 Создаем совместимую версию видео...", "INFO")
        
        video = safe_video_loading(input_path)
        
        # Обрезаем под Shorts формат
        video = crop_to_shorts_format(video, log_func)
        
        original_path = pathlib.Path(input_path)
        output_path = original_path.parent / f"{original_path.stem}_compatible.mp4"
        
        safe_video_export(video, output_path, log_func)
        video.close()
            
        log_func(f"✅ Создана совместимая версия: {output_path.name}", "INFO")
        return str(output_path)
        
    except Exception as e:
        log_func(f"❌ Ошибка создания совместимой версии: {e}", "ERROR")
        return input_path