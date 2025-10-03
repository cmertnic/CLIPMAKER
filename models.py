import json
import pathlib
from typing import Dict, Any
from config import CFG

class SubtitleSettings:
    def __init__(self, data: Dict[str, Any] = None):
        data = data or CFG["SUBTITLE_SETTINGS"]
        self.font = data.get("font", "Arial-Bold")
        self.font_size = data.get("font_size", 48)
        self.font_color = data.get("font_color", "#FFFFFF")
        self.bg_color = data.get("bg_color", "#000000")
        self.bg_opacity = data.get("bg_opacity", 0.8)
        self.stroke_color = data.get("stroke_color", "#000000")
        self.stroke_width = data.get("stroke_width", 3)
        self.position = data.get("position", "bottom")
        self.margin = data.get("margin", 100)
        self.alignment = data.get("alignment", "center")
        self.whisper_model = data.get("whisper_model", "base")
        self.language = data.get("language", "ru")
        self.style = data.get("style", "boxed")
        self.line_spacing = data.get("line_spacing", 8)
        self.max_lines = data.get("max_lines", 2)
        self.min_segment_duration = data.get("min_segment_duration", 0.3)
        self.max_segment_duration = data.get("max_segment_duration", 8.0)
        self.animation = data.get("animation", True)
        self.fixed_size = data.get("fixed_size", True)
        self.max_chars_per_line = data.get("max_chars_per_line", 35)
        self.confidence_threshold = data.get("confidence_threshold", 0.5)
        
    def to_dict(self) -> Dict[str, Any]:
        return {attr: getattr(self, attr) for attr in [
            "font", "font_size", "font_color", "bg_color", "bg_opacity",
            "stroke_color", "stroke_width", "position", "margin", "alignment",
            "whisper_model", "language", "style", "line_spacing", "max_lines",
            "min_segment_duration", "max_segment_duration", "animation",
            "fixed_size", "max_chars_per_line", "confidence_threshold"
        ]}

class FrameSettings:
    def __init__(self, data: Dict[str, Any] = None):
        data = data or CFG["FRAME_SETTINGS"]
        self.add_frame = data.get("add_frame", True)
        self.frame_color = data.get("frame_color", "#000000")
        self.frame_width = data.get("frame_width", 50)
        self.frame_style = data.get("frame_style", "solid")
        self.blur_intensity = data.get("blur_intensity", 10)
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "add_frame": self.add_frame,
            "frame_color": self.frame_color,
            "frame_width": self.frame_width,
            "frame_style": self.frame_style,
            "blur_intensity": self.blur_intensity
        }

class ProcessingState:
    def __init__(self):
        self.video_path = ""
        self.clip_count = 5
        self.clip_duration = 25.0
        self.min_clip_duration = 8.0
        self.max_clip_duration = 45.0
        self.analysis_duration = 600
        self.use_subtitles = True
        self.crop_to_shorts = True
        self.create_all_clips = False
        self.add_frame = True
        self.is_processing = False
        self.is_paused = False
        self.is_stopped = False
        self.progress = 0.0
        self.current_stage = ""
        self.current_substage = ""
        self.stage_progress = 0.0
        self.total_clips = 0
        self.current_clip = 0
        self.clips_created = []
        self.start_time = None
        self.subtitle_settings = SubtitleSettings()
        self.frame_settings = FrameSettings()
        
    def clear(self):
        self.is_processing = False
        self.is_paused = False
        self.is_stopped = False
        self.progress = 0.0
        self.current_stage = ""
        self.current_substage = ""
        self.stage_progress = 0.0
        self.total_clips = 0
        self.current_clip = 0
        self.clips_created = []
        self.start_time = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_path": self.video_path,
            "clip_count": self.clip_count,
            "clip_duration": self.clip_duration,
            "min_clip_duration": self.min_clip_duration,
            "max_clip_duration": self.max_clip_duration,
            "analysis_duration": self.analysis_duration,
            "use_subtitles": self.use_subtitles,
            "crop_to_shorts": self.crop_to_shorts,
            "create_all_clips": self.create_all_clips,
            "add_frame": self.add_frame,
            "subtitle_settings": self.subtitle_settings.to_dict(),
            "frame_settings": self.frame_settings.to_dict()
        }
        
    def save_to_file(self, file_path: pathlib.Path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            from utils import log
            log(f"Ошибка сохранения состояния: {e}", "ERROR")
            
    def load_from_file(self, file_path: pathlib.Path) -> bool:
        if not file_path.exists():
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.video_path = data.get("video_path", "")
            self.clip_count = data.get("clip_count", 5)
            self.clip_duration = data.get("clip_duration", 25.0)
            self.min_clip_duration = data.get("min_clip_duration", 8.0)
            self.max_clip_duration = data.get("max_clip_duration", 45.0)
            self.analysis_duration = data.get("analysis_duration", 600)
            self.use_subtitles = data.get("use_subtitles", True)
            self.crop_to_shorts = data.get("crop_to_shorts", True)
            self.create_all_clips = data.get("create_all_clips", False)
            self.add_frame = data.get("add_frame", True)
            self.subtitle_settings = SubtitleSettings(data.get("subtitle_settings", {}))
            self.frame_settings = FrameSettings(data.get("frame_settings", {}))
            return True
        except Exception as e:
            from utils import log
            log(f"Ошибка загрузки состояния: {e}", "ERROR")
            return False