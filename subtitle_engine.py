import os
import re
import torch
import whisper
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip
from audio_enhancer import AudioPreprocessor
from config import CFG

class SubtitlePostProcessor:
    def __init__(self, language="ru"):
        self.language = language
    
    def improve_subtitles(self, subtitles):
        """Улучшает качество субтитров"""
        improved_subtitles = []
        
        for i, subtitle in enumerate(subtitles):
            original_text = subtitle['text']
            improved_text = self._correct_text(original_text)
            
            # УВЕЛИЧЕННАЯ ЧУВСТВИТЕЛЬНОСТЬ: меньше объединяем субтитры
            if i > 0 and self._should_merge(improved_subtitles[-1], subtitle):
                merged = self._merge_subtitles(improved_subtitles[-1], subtitle)
                improved_subtitles[-1] = merged
            else:
                subtitle['text'] = improved_text
                improved_subtitles.append(subtitle)
        
        return improved_subtitles
    
    def _correct_text(self, text):
        """Корректирует текст"""
        if not text:
            return text
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Исправляем пунктуацию
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = re.sub(r'([.,!?])([А-ЯA-Z])', r'\1 \2', text)
        
        return text
    
    def _should_merge(self, prev_sub, current_sub):
        """Определяет, нужно ли объединять субтитры"""
        time_gap = current_sub['start'] - prev_sub['end']
        prev_text = prev_sub['text']
        current_text = current_sub['text']
        
        # УВЕЛИЧЕННАЯ ЧУВСТВИТЕЛЬНОСТЬ: увеличиваем порог объединения
        return (time_gap < 0.5 and  # было 0.3
                len(prev_text + ' ' + current_text) < 60 and  # было 80
                not prev_text.endswith(('.', '!', '?')))
    
    def _merge_subtitles(self, sub1, sub2):
        """Объединяет два субтитра"""
        return {
            'text': sub1['text'] + ' ' + sub2['text'],
            'start': sub1['start'],
            'end': sub2['end'],
            'duration': sub2['end'] - sub1['start']
        }

class UltimateSubtitleEngine:
    def __init__(self):
        self.whisper_engine = ImprovedWhisperEngine()
        self.audio_processor = AudioPreprocessor()
        self.post_processor = SubtitlePostProcessor()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🎯 Субтитры: используется устройство {self.device}")
    
    def get_subtitles(self, source: str, source_type: str = "local", language: str = "ru", 
                     model_size: str = "large") -> Tuple[Optional[List[Dict]], str]:
        """
        Получает субтитры максимального качества
        """
        try:
            if source_type == "youtube":
                subtitles, error = self._get_youtube_subtitles(source, language)
            else:
                subtitles, error = self._get_whisper_subtitles(source, language, model_size)
            
            if error or not subtitles:
                return None, error
            
            # Пост-обработка
            final_subtitles = self.post_processor.improve_subtitles(subtitles)
            
            for sub in final_subtitles:
                sub['source'] = 'youtube' if source_type == "youtube" else 'whisper'
            
            print(f"✅ Получено {len(final_subtitles)} субтитров")
            return final_subtitles, None
            
        except Exception as e:
            return None, f"Ошибка получения субтитров: {e}"
    
    def _get_youtube_subtitles(self, youtube_url: str, language: str) -> Tuple[Optional[List[Dict]], str]:
        """Получает субтитры с YouTube - ПРИОРИТЕТНЫЙ МЕТОД"""
        try:
            video_id = self._extract_video_id(youtube_url)
            if not video_id:
                return None, "Неверный URL YouTube"
            
            print(f"🎯 Получаем субтитры YouTube: {video_id}")
            
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = None
            
            # 1. Пробуем прямые субтитры на нужном языке
            try:
                transcript = transcript_list.find_transcript([language])
                print(f"✅ Найдены прямые субтитры на {language}")
            except:
                # 2. Пробуем автоматические субтитры
                try:
                    transcript = transcript_list.find_transcript([language, 'en'])
                    print(f"✅ Найдены автоматические субтитры")
                except:
                    # 3. Пробуем любой доступный язык и переводим
                    try:
                        available_transcripts = list(transcript_list._manually_created_transcripts.values())
                        if available_transcripts:
                            transcript = available_transcripts[0]
                            if language != transcript.language_code:
                                transcript = transcript.translate(language)
                            print(f"✅ Используем субтитры с переводом")
                    except:
                        pass
            
            if not transcript:
                return None, "Не удалось найти подходящие субтитры"
            
            subtitles_data = transcript.fetch()
            formatted_subtitles = []
            
            for item in subtitles_data:
                clean_text = self._clean_youtube_text(item['text'])
                # УВЕЛИЧЕННАЯ ЧУВСТВИТЕЛЬНОСТЬ: берем даже короткие субтитры
                if clean_text and len(clean_text) >= 1:  # было > 1
                    formatted_subtitles.append({
                        'text': clean_text,
                        'start': item['start'],
                        'end': item['start'] + item['duration'],
                        'duration': item['duration'],
                        'confidence': 0.95
                    })
            
            print(f"✅ Получено {len(formatted_subtitles)} субтитров с YouTube")
            return formatted_subtitles, None
            
        except Exception as e:
            print(f"❌ Ошибка YouTube субтитров: {e}")
            return None, f"Ошибка YouTube: {e}"
    
    def _get_whisper_subtitles(self, audio_path: str, language: str, model_size: str) -> Tuple[Optional[List[Dict]], str]:
        """Получает субтитры через Whisper (резервный метод)"""
        try:
            print("🔊 Используем Whisper как резервный метод...")
            
            # Улучшаем аудио
            enhanced_audio = self.audio_processor.enhance_audio(audio_path)
            
            # Транскрибируем с УВЕЛИЧЕННОЙ ЧУВСТВИТЕЛЬНОСТЬЮ
            subtitles = self.whisper_engine.transcribe_enhanced(
                enhanced_audio, language, model_size, word_level=True  # Включаем word-level для большего количества субтитров
            )
            
            # Очистка временных файлов
            if enhanced_audio != audio_path and os.path.exists(enhanced_audio):
                try:
                    os.remove(enhanced_audio)
                except:
                    pass
            
            return subtitles, None
            
        except Exception as e:
            return None, f"Ошибка Whisper: {e}"
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Извлекает ID видео из YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&?\n]+)',
            r'youtube\.com\/embed\/([^&?\n]+)',
            r'youtube\.com\/v\/([^&?\n]+)',
            r'youtube\.com\/shorts\/([^&?\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _clean_youtube_text(self, text: str) -> str:
        """Очищает текст YouTube субтитров"""
        if not text:
            return ""
        
        # Удаляем [Музыка], [Аплодисменты] и т.д.
        text = re.sub(r'\[.*?\]', '', text)
        # Удаляем специальные символы
        text = re.sub(r'[♪♫▁▏│]', '', text)
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

class ImprovedWhisperEngine:
    def __init__(self):
        self.models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def load_model(self, model_size="base", language="ru"):
        """Загружает модель Whisper"""
        model_key = f"{model_size}_{language}"
        
        if model_key in self.models:
            return self.models[model_key]
        
        try:
            print(f"🔄 Загружаем модель Whisper {model_size}...")
            model = whisper.load_model(model_size, device=self.device)
            self.models[model_key] = model
            print(f"✅ Модель {model_size} загружена")
            return model
        except Exception as e:
            print(f"❌ Ошибка загрузки {model_size}: {e}")
            return None
    
    def transcribe_enhanced(self, audio_path, language="ru", model_size="base", word_level=False):
        """Транскрибирует аудио с УВЕЛИЧЕННОЙ ЧУВСТВИТЕЛЬНОСТЬЮ"""
        model = self.load_model(model_size, language)
        if not model:
            return []
        
        try:
            # УВЕЛИЧЕННАЯ ЧУВСТВИТЕЛЬНОСТЬ: используем более чувствительные настройки
            result = model.transcribe(
                audio_path, 
                language=language, 
                word_timestamps=word_level,
                no_speech_threshold=0.4,  # было 0.6 - меньше фильтруем тишину
                logprob_threshold=-0.8,   # было -1.0 - больше принимаем
                compression_ratio_threshold=2.0  # было 2.4 - меньше сжимаем
            )
            return self._post_process_result(result, word_level)
        except Exception as e:
            print(f"❌ Ошибка транскрипции: {e}")
            return []
    
    def _post_process_result(self, result, word_level=False):
        """Пост-обработка результатов с УВЕЛИЧЕННОЙ ЧУВСТВИТЕЛЬНОСТЬЮ"""
        if word_level:
            # Обработка на уровне слов для большего количества субтитров
            segments = []
            for segment in result.get("segments", []):
                words = segment.get("words", [])
                for word in words:
                    text = word["word"].strip()
                    if text and len(text) > 0:
                        segments.append({
                            'text': text,
                            'start': word['start'],
                            'end': word['end'],
                            'duration': word['end'] - word['start'],
                            'confidence': word.get('probability', 0.7)
                        })
        else:
            # Обычная обработка сегментов
            segments = result.get("segments", [])
        
        improved_segments = []
        
        for segment in segments:
            text = segment["text"].strip()
            # УВЕЛИЧЕННАЯ ЧУВСТВИТЕЛЬНОСТЬ: берем даже очень короткие тексты
            if text and len(text) >= 1:  # было > 1
                improved_segments.append({
                    'text': text,
                    'start': segment['start'],
                    'end': segment['end'],
                    'duration': segment['end'] - segment['start'],
                    'confidence': segment.get('confidence', 0.7)  # было 0.8
                })
        
        print(f"🔊 Whisper: найдено {len(improved_segments)} сегментов")
        return improved_segments

def add_subtitles_to_clip(clip_path: str, settings, log_func) -> str:
    """Добавление субтитров к клипу - УВЕЛИЧЕННАЯ ЧУВСТВИТЕЛЬНОСТЬ"""
    try:
        log_func(f"📝 Добавление субтитров к {clip_path}", "INFO")
        
        # Создаем движок субтитров
        subtitle_engine = UltimateSubtitleEngine()
        
        # Определяем тип источника
        if clip_path.startswith(('http', 'www.', 'youtube.com', 'youtu.be')):
            source_type = "youtube"
            source_url = clip_path
        else:
            source_type = "local" 
            source_url = clip_path
        
        # Получаем субтитры
        subtitles, error = subtitle_engine.get_subtitles(
            source_url, 
            source_type,
            getattr(settings, 'language', 'ru'),
            getattr(settings, 'whisper_model', 'base')
        )
        
        if error or not subtitles:
            log_func(f"⚠️ Не удалось получить субтитры: {error}", "WARNING")
            return clip_path
        
        log_func(f"✅ Получено {len(subtitles)} субтитров", "INFO")
        
        # Загружаем видео
        video = VideoFileClip(clip_path)
        video_w, video_h = video.size
        
        # Создаем субтитры
        subtitle_clips = []
        
        for i, subtitle in enumerate(subtitles):
            try:
                text = subtitle['text'].strip()
                if not text:
                    continue
                
                # Форматируем текст
                text = _format_text_to_lines(text, max_chars_per_line=40, max_lines=2)
                
                start_time = subtitle['start']
                end_time = subtitle['end']
                duration = end_time - start_time
                
                # УВЕЛИЧЕННАЯ ЧУВСТВИТЕЛЬНОСТЬ: показываем более короткие субтитры
                if duration < 0.3 or duration > 15:  # было 0.5-10
                    continue
                
                # Создаем текстовый клип
                txt_clip = _create_text_clip(text, video_w, duration, settings)
                if not txt_clip:
                    continue
                
                # Позиционирование
                pos_y = video_h - txt_clip.h - 50  # 50px от низа
                pos_x = (video_w - txt_clip.w) / 2
                
                # Устанавливаем время и позицию
                txt_clip = txt_clip.set_position((pos_x, pos_y))
                txt_clip = txt_clip.set_start(start_time)
                txt_clip = txt_clip.set_duration(duration)
                
                subtitle_clips.append(txt_clip)
                log_func(f"🎬 Субтитр {i+1}: '{text}' | {start_time:.1f}-{end_time:.1f}с", "DEBUG")
                
            except Exception as e:
                log_func(f"⚠️ Ошибка создания субтитра: {e}", "DEBUG")
                continue
        
        if subtitle_clips:
            # Композитим видео с субтитрами
            final_video = CompositeVideoClip([video] + subtitle_clips)
            
            # Сохраняем результат
            original_path = Path(clip_path)
            output_path = original_path.parent / f"{original_path.stem}_with_subs.mp4"
            
            # Экспортируем видео
            final_video.write_videofile(
                str(output_path),
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None,
                threads=4
            )
            
            # Закрываем клипы
            video.close()
            final_video.close()
            for clip in subtitle_clips:
                clip.close()
            
            log_func(f"✅ Добавлено {len(subtitle_clips)} субтитров: {output_path.name}", "INFO")
            return str(output_path)
        else:
            log_func("⚠️ Не удалось создать ни одного субтитра", "WARNING")
            video.close()
            return clip_path
            
    except Exception as e:
        log_func(f"❌ Ошибка добавления субтитров: {e}", "ERROR")
        return clip_path

def _format_text_to_lines(text, max_chars_per_line=40, max_lines=2):
    """Форматирует текст в несколько строк"""
    if len(text) <= max_chars_per_line:
        return text
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if len(test_line) <= max_chars_per_line:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            
            if len(lines) >= max_lines - 1:
                if current_line:
                    last_line = ' '.join(current_line)
                    if len(last_line) > max_chars_per_line:
                        last_line = last_line[:max_chars_per_line-3] + '...'
                    lines.append(last_line)
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def _create_text_clip(text, video_width, duration, settings):
    """Создает текстовый клип"""
    try:
        font_size = getattr(settings, 'font_size', 42)
        font = getattr(settings, 'font', 'Arial-Bold')
        
        txt_clip = TextClip(
            text,
            fontsize=font_size,
            color='white',
            font=font,
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(video_width * 0.9, None),
            align='center'
        )
        
        txt_clip = txt_clip.set_duration(duration)
        return txt_clip
        
    except Exception as e:
        print(f"❌ Ошибка создания текстового клипа: {e}")
        return None