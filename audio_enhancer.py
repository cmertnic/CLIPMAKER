import os
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, high_pass_filter, low_pass_filter
import tempfile
from pathlib import Path

class AudioPreprocessor:
    def __init__(self):
        self.sample_rate = 16000
    
    def enhance_audio(self, audio_path, output_path=None):
        """Улучшает качество аудио для лучшего распознавания"""
        try:
            print("🔊 Улучшаем качество аудио...")
            
            audio = AudioSegment.from_file(audio_path)
            enhanced_audio = self._apply_enhancements(audio)
            
            if not output_path:
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, f"enhanced_{os.path.basename(audio_path)}.wav")
            
            enhanced_audio.export(output_path, format="wav")
            print(f"✅ Аудио улучшено: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Ошибка улучшения аудио: {e}")
            return audio_path
    
    def _apply_enhancements(self, audio):
        """Применяет различные улучшения к аудио"""
        # 1. Конвертируем в моно для лучшего распознавания
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # 2. Устанавливаем sample rate для Whisper
        if audio.frame_rate != self.sample_rate:
            audio = audio.set_frame_rate(self.sample_rate)
        
        # 3. Нормализация громкости
        audio = self._normalize_volume(audio)
        
        # 4. Шумоподавление (простое)
        audio = self._reduce_noise(audio)
        
        # 5. Подчеркивание высоких частот
        audio = self._enhance_high_frequencies(audio)
        
        return audio
    
    def _normalize_volume(self, audio):
        """Нормализует громкость"""
        target_dBFS = -20.0
        change_in_dBFS = target_dBFS - audio.dBFS
        return audio.apply_gain(change_in_dBFS)
    
    def _reduce_noise(self, audio):
        """Простое шумоподавление"""
        # Обрезаем очень высокие частоты где обычно шум
        return low_pass_filter(audio, 8000)
    
    def _enhance_high_frequencies(self, audio):
        """Подчеркивает высокие частоты для лучшей разборчивости"""
        # Убираем очень низкие частоты (гул)
        return high_pass_filter(audio, 80)