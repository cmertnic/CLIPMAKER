import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
from moviepy.video.fx.all import resize
from subtitle_engine import crop_to_shorts_format
from utils import hex_to_rgb, log
from models import FrameSettings

def create_frame_clip(video_clip: VideoFileClip, frame_settings: FrameSettings) -> VideoFileClip:
    """Создание клипа с solid рамками для вертикального формата"""
    try:
        # Если рамки отключены, используем обычную обрезку под шортс
        if not frame_settings.add_frame:
            return crop_to_shorts_format(video_clip, lambda msg, level: None)  # Пустая функция для логирования
            
        target_size = frame_settings.target_size  # (1080, 1920)
        frame_color = frame_settings.frame_color
        
        # Получаем размер исходного видео
        original_w, original_h = video_clip.size
        
        # Вычисляем масштаб чтобы видео полностью влезло в target_size (сохраняя пропорции)
        scale_x = target_size[0] / original_w
        scale_y = target_size[1] / original_h
        scale = min(scale_x, scale_y)  # Берем меньший масштаб чтобы видео полностью влезло
        
        # Размер основного видео
        main_width = int(original_w * scale)
        main_height = int(original_h * scale)
        
        # Создаем основное видео
        main_video = video_clip.resize((main_width, main_height))
        
        # Создаем цветной фон
        from moviepy.editor import ColorClip
        background = ColorClip(size=target_size, color=hex_to_rgb(frame_color))
        background = background.set_duration(video_clip.duration)
        
        # Позиционируем основное видео по центру
        x_pos = (target_size[0] - main_width) // 2
        y_pos = (target_size[1] - main_height) // 2
        
        main_video = main_video.set_position((x_pos, y_pos))
        
        # Композируем: цветной фон + основное видео
        final_video = CompositeVideoClip([
            background,
            main_video
        ])
        
        return final_video
        
    except Exception as e:
        log(f"Ошибка создания solid рамки: {e}", "ERROR")
        return video_clip

def create_blurred_frame_clip(video_clip, frame_settings):
    """Создает размытый фон из того же видео для заполнения пустого пространства"""
    try:
        # Если рамки отключены, используем обычную обрезку под шортс
        if not frame_settings.add_frame:
            return crop_to_shorts_format(video_clip, lambda msg, level: None)  # Пустая функция для логирования
            
        target_size = frame_settings.target_size  # (1080, 1920)
        blur_strength = frame_settings.blur_strength
        
        # Корректируем blur_strength - увеличенное значение по умолчанию
        if blur_strength <= 0:
            blur_strength = 51  # Увеличенное значение по умолчанию
        elif blur_strength % 2 == 0:  # если четное
            blur_strength += 1  # делаем нечетным
        
        # Ограничиваем максимальное значение для производительности
        blur_strength = min(blur_strength, 99)  # максимум 99
        
        # Получаем размер исходного видео
        original_w, original_h = video_clip.size
        
        # Вычисляем масштаб чтобы видео полностью влезло в target_size (сохраняя пропорции)
        scale_x = target_size[0] / original_w
        scale_y = target_size[1] / original_h
        scale = min(scale_x, scale_y)  # Берем меньший масштаб чтобы видео полностью влезло
        
        # Размер основного видео (не размытого)
        main_width = int(original_w * scale)
        main_height = int(original_h * scale)
        
        # Создаем основное видео
        main_video = video_clip.resize((main_width, main_height))
        
        # Создаем размытый фон - растягиваем видео на весь размер шортс
        blurred_bg = video_clip.resize(target_size)
        blurred_bg = blurred_bg.fl_image(lambda frame: cv2.GaussianBlur(frame, (blur_strength, blur_strength), 0))
        
        # Позиционируем основное видео по центру
        x_pos = (target_size[0] - main_width) // 2
        y_pos = (target_size[1] - main_height) // 2
        
        main_video = main_video.set_position((x_pos, y_pos))
        
        # Композируем: размытый фон + основное видео
        final_video = CompositeVideoClip([
            blurred_bg,
            main_video
        ])
        
        return final_video
        
    except Exception as e:
        raise Exception(f"Ошибка создания размытой рамки: {e}")

def crop_to_shorts_format(clip, log_func):
    """Старая проверенная обрезка под вертикальный формат (во весь размер)"""
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
def crop_to_vertical_with_frame(clip: VideoFileClip, frame_settings: FrameSettings) -> VideoFileClip:
    """Обрезка видео под вертикальный формат с рамками"""
    if not frame_settings.add_frame:
        # Используем crop_to_shorts_format который приводит к 1080x1920
        def simple_log(msg, level):
            if level == "ERROR":
                print(f"❌ {msg}")
            elif level == "INFO":
                print(f"ℹ️ {msg}")
        return crop_to_shorts_format(clip, simple_log)
    
    if frame_settings.frame_style == "blur":
        return create_blurred_frame_clip(clip, frame_settings)
    else:
        return create_frame_clip(clip, frame_settings)

def crop_to_vertical(clip: VideoFileClip, target_ratio: float = 9/16) -> VideoFileClip:
    """Обрезка видео под вертикальный формат (9:16 для Shorts/Reels)"""
    w, h = clip.size
    
    target_width = int(h * target_ratio)
    
    if target_width < w:
        x_center = w / 2
        x1 = int(x_center - target_width / 2)
        x2 = int(x_center + target_width / 2)
        return clip.crop(x1=x1, y1=0, x2=x2, y2=h)
    else:
        return clip