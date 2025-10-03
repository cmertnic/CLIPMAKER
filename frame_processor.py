import cv2
import numpy as np
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
from moviepy.video.fx.all import resize
from utils import hex_to_rgb, log
from models import FrameSettings

def create_frame_clip(video_clip: VideoFileClip, frame_settings: FrameSettings) -> VideoFileClip:
    """Создание клипа с рамками для вертикального формата"""
    try:
        original_w, original_h = video_clip.size
        duration = video_clip.duration
        
        # Целевые размеры для вертикального формата (9:16)
        target_width = int(original_h * 9/16)
        target_height = int(target_width * 16/9)
        
        if original_w <= target_width:
            # Если видео уже вертикальное, добавляем рамки сверху и снизу
            vertical_padding = (target_height - original_h) // 2
            
            if vertical_padding > 0:
                top_frame = ColorClip(
                    size=(target_width, vertical_padding), 
                    color=hex_to_rgb(frame_settings.frame_color),
                    duration=duration
                ).set_position(("center", "top"))
                
                bottom_frame = ColorClip(
                    size=(target_width, vertical_padding), 
                    color=hex_to_rgb(frame_settings.frame_color),
                    duration=duration
                ).set_position(("center", "bottom"))
                
                # Центрируем видео
                video_clip = video_clip.set_position(("center", vertical_padding))
                
                # Композитируем
                final_clip = CompositeVideoClip([
                    top_frame,
                    video_clip,
                    bottom_frame
                ], size=(target_width, target_height))
                
                return final_clip
            else:
                return video_clip
        else:
            # Если видео горизонтальное, обрезаем и добавляем рамки
            x_center = original_w / 2
            x1 = int(x_center - target_width / 2)
            x2 = int(x_center + target_width / 2)
            cropped_clip = video_clip.crop(x1=x1, y1=0, x2=x2, y2=original_h)
            
            # Добавляем рамки сверху и снизу
            vertical_padding = (target_height - original_h) // 2
            
            if vertical_padding > 0:
                top_frame = ColorClip(
                    size=(target_width, vertical_padding), 
                    color=hex_to_rgb(frame_settings.frame_color),
                    duration=duration
                ).set_position(("center", "top"))
                
                bottom_frame = ColorClip(
                    size=(target_width, vertical_padding), 
                    color=hex_to_rgb(frame_settings.frame_color),
                    duration=duration
                ).set_position(("center", "bottom"))
                
                # Центрируем обрезанное видео
                cropped_clip = cropped_clip.set_position(("center", vertical_padding))
                
                # Композитируем
                final_clip = CompositeVideoClip([
                    top_frame,
                    cropped_clip,
                    bottom_frame
                ], size=(target_width, target_height))
                
                return final_clip
            else:
                return cropped_clip
                
    except Exception as e:
        log(f"Ошибка создания рамки: {e}", "ERROR")
        return video_clip

def create_blurred_frame_clip(video_clip: VideoFileClip, frame_settings: FrameSettings) -> VideoFileClip:
    """Создание клипа с размытыми рамками"""
    try:
        original_w, original_h = video_clip.size
        duration = video_clip.duration
        
        # Целевые размеры для вертикального формата (9:16)
        target_width = int(original_h * 9/16)
        target_height = int(target_width * 16/9)
        
        # Создаем размытый фон из оригинального видео
        blurred_bg = video_clip.fx(resize, width=target_width).fx(
            lambda gf, t: cv2.GaussianBlur(gf(t), (frame_settings.blur_intensity, frame_settings.blur_intensity), 0)
        )
        
        if original_w <= target_width:
            # Если видео уже вертикальное, центрируем
            y_pos = (target_height - original_h) // 2
            video_clip = video_clip.set_position(("center", y_pos))
        else:
            # Если видео горизонтальное, обрезаем
            x_center = original_w / 2
            x1 = int(x_center - target_width / 2)
            x2 = int(x_center + target_width / 2)
            video_clip = video_clip.crop(x1=x1, y1=0, x2=x2, y2=original_h)
            y_pos = (target_height - original_h) // 2
            video_clip = video_clip.set_position(("center", y_pos))
        
        # Композитируем
        final_clip = CompositeVideoClip([
            blurred_bg,
            video_clip
        ], size=(target_width, target_height))
        
        return final_clip
            
    except Exception as e:
        log(f"Ошибка создания размытой рамки: {e}", "ERROR")
        return create_frame_clip(video_clip, frame_settings)

def crop_to_vertical_with_frame(clip: VideoFileClip, frame_settings: FrameSettings) -> VideoFileClip:
    """Обрезка видео под вертикальный формат с рамками"""
    if not frame_settings.add_frame:
        return crop_to_vertical(clip)
    
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