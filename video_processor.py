import time
import cv2
import numpy as np
import sys
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import subprocess
import os

from config import CFG
from utils import log
from models import ProcessingState, FrameSettings
from frame_processor import crop_to_vertical_with_frame, crop_to_vertical
from subtitle_engine import add_subtitles_to_clip_advanced

def safe_progress_bar(iterable, desc="", log_callback=None, progress_callback=None, total=None):
    """Безопасный прогресс-бар для exe и обычного Python"""
    items = list(iterable)
    if total is None:
        total = len(items)
    
    for i, item in enumerate(items):
        # Обновляем прогресс каждые 100 итераций или на последней
        if i % 100 == 0 or i == len(items) - 1:
            progress_percent = (i / len(items)) * 100
            status = f"{desc}: {progress_percent:.1f}%"
            
            if log_callback:
                log_callback(status)
            
            if progress_callback:
                # Передаем абсолютный прогресс (0-100) и текст статуса
                progress_callback(progress_percent * 0.5, status)
        
        yield item

def analyze_video_advanced(video_path: str, analysis_duration: int, log_func, state: ProcessingState, progress_callback) -> list:
    """Продвинутый анализ видео для поиска самых вирусных моментов"""
    start_time = time.time()
    log_func("🔍 Расширенный анализ видео на вирусные моменты...", "INFO")
    
    # Загружаем видео
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Не удалось открыть видео")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    log_func(f"📊 Параметры видео: FPS={fps}, Frames={total_frames}, Duration={duration:.1f}с", "INFO")
    
    # Ограничиваем анализ
    analysis_frames = min(int(analysis_duration * fps), total_frames)
    
    # Извлекаем аудио для расширенного анализа
    audio_path = CFG["TEMP_DIR"] / "temp_audio.wav"
    try:
        subprocess.run([
            'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', 
            '-ar', '44100', '-ac', '2', str(audio_path), '-y'
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        log_func("⚠️ Не удалось извлечь аудио", "WARNING")
        return []

    # Анализ аудио - ищем моменты с высокой энергией
    audio = AudioSegment.from_file(str(audio_path))
    audio_samples = np.array(audio.get_array_of_samples())
    if audio.channels == 2:
        audio_samples = audio_samples.reshape((-1, 2)).mean(axis=1)
    
    # Анализ по сегментам (0.5 секунды)
    segment_length = int(audio.frame_rate * 0.5)
    audio_energy = []
    
    for i in range(0, len(audio_samples) - segment_length, segment_length):
        segment = audio_samples[i:i+segment_length]
        energy = np.sqrt(np.mean(segment**2))
        time_sec = i / audio.frame_rate
        audio_energy.append((time_sec, energy))
    
    # Находим пики энергии (топ 10%)
    energy_values = [e[1] for e in audio_energy]
    energy_threshold = np.percentile(energy_values, 90)
    audio_peaks = [e[0] for e in audio_energy if e[1] > energy_threshold]
    
    log_func(f"🔊 Найдено {len(audio_peaks)} аудио-пиков", "INFO")
    
    # Анализ движения с улучшенным детектированием
    motion_scores = []
    optical_flow_scores = []
    
    ret, prev_frame = cap.read()
    if not ret:
        return []
        
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
    
    # Детектор особенностей для оптического потока
    feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
    p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, **feature_params)
    
    # ЗАМЕНА: используем безопасный прогресс-бар вместо tqdm
    frame_range = range(1, analysis_frames, max(1, int(fps/2)))
    for frame_num in safe_progress_bar(
        frame_range, 
        desc="Анализ движения",
        log_callback=log_func,
        progress_callback=progress_callback,
        total=len(frame_range)
    ):
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Детектирование движения через разницу кадров
        frame_delta = cv2.absdiff(prev_gray, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_area = sum(cv2.contourArea(c) for c in contours)
        motion_scores.append((frame_num / fps, motion_area))
        
        # Оптический поток для детектирования сложного движения
        if p0 is not None:
            p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, gray, p0, None)
            if p1 is not None:
                good_new = p1[st == 1]
                good_old = p0[st == 1]
                if len(good_new) > 0:
                    flow_magnitude = np.mean(np.sqrt(np.sum((good_new - good_old)**2, axis=1)))
                    optical_flow_scores.append((frame_num / fps, flow_magnitude))
        
        prev_gray = gray
        if p0 is not None:
            p0 = cv2.goodFeaturesToTrack(prev_gray, mask=None, **feature_params)
        
        if state.is_stopped:
            break
            
        # Прогресс теперь обрабатывается в safe_progress_bar
    
    cap.release()
    
    # Находим пики движения
    motion_values = [m[1] for m in motion_scores]
    motion_threshold = np.percentile(motion_values, 85)
    motion_peaks = [m[0] for m in motion_scores if m[1] > motion_threshold]
    
    # Находим пики оптического потока
    if optical_flow_scores:
        flow_values = [f[1] for f in optical_flow_scores]
        flow_threshold = np.percentile(flow_values, 85)
        flow_peaks = [f[0] for f in optical_flow_scores if f[1] > flow_threshold]
    else:
        flow_peaks = []
    
    log_func(f"🎥 Найдено {len(motion_peaks)} пиков движения, {len(flow_peaks)} пиков оптического потока", "INFO")
    
    # Объединяем все пики
    all_peaks = set(audio_peaks + motion_peaks + flow_peaks)
    
    # Группируем близкие пики и оцениваем интенсивность
    peak_groups = []
    sorted_peaks = sorted(all_peaks)
    
    current_group = []
    for peak in sorted_peaks:
        if not current_group or peak - current_group[-1] <= 5.0:
            current_group.append(peak)
        else:
            if len(current_group) >= 2:
                peak_groups.append(current_group)
            current_group = [peak]
    
    if len(current_group) >= 2:
        peak_groups.append(current_group)
    
    # Выбираем лучшие моменты на основе плотности пиков
    best_moments = []
    for group in peak_groups:
        if len(group) >= 3:
            center = np.mean(group)
            intensity = len(group)
            best_moments.append((center, intensity))
    
    # Сортируем по интенсивности
    best_moments.sort(key=lambda x: x[1], reverse=True)
    
    # Если включена опция "все клипы", возвращаем все моменты
    if state.create_all_clips:
        selected_moments = [moment[0] for moment in best_moments]
        log_func(f"🎯 Режим 'Все клипы': найдено {len(selected_moments)} моментов", "INFO")
    else:
        selected_moments = [moment[0] for moment in best_moments[:min(state.clip_count, len(best_moments))]]
        log_func(f"🎯 Найдено {len(selected_moments)} вирусных моментов", "INFO")
    
    analysis_time = time.time() - start_time
    log_func(f"⏱️ Время анализа: {analysis_time:.1f}с", "INFO")
    
    return selected_moments

def create_clips_from_best_moments(video_path: str, moments: list, clip_count: int, clip_duration: float, 
                                 min_clip_duration: float, max_clip_duration: float, crop_to_shorts: bool, 
                                 create_all_clips: bool, add_frame: bool, frame_settings: FrameSettings,
                                 log_func, state: ProcessingState, progress_callback) -> list:
    """Создание клипов из лучших моментов"""
    start_time = time.time()
    
    if create_all_clips:
        log_func(f"🎬 Создание всех {len(moments)} вирусных клипов", "INFO")
        actual_clip_count = len(moments)
    else:
        log_func(f"🎬 Создание {clip_count} клипов из {len(moments)} лучших моментов", "INFO")
        actual_clip_count = min(clip_count, len(moments))
    
    try:
        video = VideoFileClip(video_path)
        total_duration = video.duration
        
        clips_created = []
        used_moments = set()
        
        for i in range(actual_clip_count):
            if state.is_stopped:
                break
                
            moment = moments[i]
            
            if moment in used_moments:
                continue
                
            # Определяем границы клипа
            start_time_clip = max(0, moment - clip_duration / 2)
            end_time_clip = min(total_duration, moment + clip_duration / 2)
            
            # Корректируем для Shorts
            target_duration = 59.0
            if crop_to_shorts:
                if end_time_clip - start_time_clip > target_duration:
                    start_time_clip = max(0, moment - target_duration / 2)
                    end_time_clip = min(total_duration, start_time_clip + target_duration)
            
            # Создаем клип
            try:
                clip = video.subclip(start_time_clip, end_time_clip)
                
                # Обрезаем под вертикальный формат если включена опция Shorts
                if crop_to_shorts:
                    if add_frame:
                        clip = crop_to_vertical_with_frame(clip, frame_settings)
                        frame_style = frame_settings.frame_style
                        log_func(f"📱 Обрезка под вертикальный формат с {frame_style} рамками", "DEBUG")
                    else:
                        clip = crop_to_vertical(clip)
                        log_func(f"📱 Обрезка под вертикальный формат (9:16)", "DEBUG")
                
                from config import OUT
                if create_all_clips:
                    output_path = OUT / f"viral_clip_{i+1:02d}_{int(start_time_clip)}s-{int(end_time_clip)}s.mp4"
                else:
                    output_path = OUT / f"shorts_clip_{i+1:02d}_{int(start_time_clip)}s-{int(end_time_clip)}s.mp4"
                
                clip.write_videofile(
                    str(output_path), 
                    codec="libx264", 
                    audio_codec="aac", 
                    verbose=False, 
                    logger=None,
                    threads=4,
                    temp_audiofile=str(CFG["TEMP_DIR"] / f"temp_audio_{i}.m4a")
                )
                clip.close()
                
                clips_created.append(str(output_path))
                used_moments.add(moment)
                
                if create_all_clips:
                    log_func(f"✅ Вирусный клип {i+1}: {output_path.name} (центр: {moment:.1f}с)", "INFO")
                else:
                    log_func(f"✅ Shorts клип {i+1}: {output_path.name} (центр: {moment:.1f}с)", "INFO")
                
            except Exception as e:
                log_func(f"⚠️ Ошибка создания клипа {i+1}: {e}", "WARNING")
                continue
            
            progress = (i + 1) / actual_clip_count * 100
            progress_callback(33.33 + progress * 0.33, f"Создание клипа {i+1}/{actual_clip_count}")
        
        video.close()
        
        process_time = time.time() - start_time
        if create_all_clips:
            log_func(f"🎬 Создано {len(clips_created)} вирусных клипов за {process_time:.1f}с", "INFO")
        else:
            log_func(f"🎬 Создано {len(clips_created)} Shorts клипов за {process_time:.1f}с", "INFO")
        return clips_created
        
    except Exception as e:
        log_func(f"❌ Ошибка создания клипов: {e}", "ERROR")
        return []

def process_video_thread(state: ProcessingState, progress_callback, log_callback):
    """Основная функция обработки в отдельном потоке"""
    try:
        state.is_processing = True
        state.start_time = time.time()
        state.progress = 0.0
        state.current_stage = "Расширенный анализ видео"
        
        log_callback("🚀 Начинаем расширенную обработку видео...", "INFO")
        
        # Создаем директории
        from config import OUT, CFG
        OUT.mkdir(exist_ok=True)
        CFG["TEMP_DIR"].mkdir(exist_ok=True)
        
        # Шаг 1: Расширенный анализ видео
        progress_callback(0, "Поиск вирусных моментов...")
        moments = analyze_video_advanced(state.video_path, state.analysis_duration, log_callback, state, progress_callback)
        
        if state.is_stopped or not moments:
            log_callback("🛑 Обработка остановлена или моменты не найдены", "INFO")
            return
        
        # Шаг 2: Создание клипов
        state.current_stage = "Создание вирусных клипов"
        progress_callback(33.33, "Создание клипов...")
        clips = create_clips_from_best_moments(
            state.video_path, moments, state.clip_count, state.clip_duration, 
            state.min_clip_duration, state.max_clip_duration, state.crop_to_shorts,
            state.create_all_clips, state.add_frame, state.frame_settings,
            log_callback, state, progress_callback
        )
        
        if state.is_stopped or not clips:
            log_callback("🛑 Обработка остановлена или клипы не созданы", "INFO")
            return
        
        # Шаг 3: Добавление субтитров
        if state.use_subtitles:
            state.current_stage = "Добавление субтитров"
            progress_callback(66.66, "Добавление субтитров...")
            
            successful_clips = []
            for i, clip_path in enumerate(clips):
                if state.is_stopped:
                    break
                    
                try:
                    new_clip_path = add_subtitles_to_clip_advanced(clip_path, state.subtitle_settings, log_callback)
                    if new_clip_path != clip_path:
                        import os
                        if os.path.exists(clip_path):
                            os.remove(clip_path)
                        successful_clips.append(new_clip_path)
                    else:
                        successful_clips.append(clip_path)
                        
                except Exception as e:
                    log_callback(f"⚠️ Ошибка обработки клипа {i+1}: {e}", "WARNING")
                    successful_clips.append(clip_path)
                
                progress = (i + 1) / len(clips) * 100
                progress_callback(66.66 + progress * 0.33, f"Субтитры к клипу {i+1}/{len(clips)}")
            
            clips = successful_clips
        
        # Завершение
        state.clips_created = clips
        state.progress = 100.0
        state.current_stage = "Готово"
        
        total_time = time.time() - state.start_time
        if state.create_all_clips:
            log_callback(f"✅ Обработка завершена! Создано {len(clips)} вирусных клипов за {total_time:.1f}с", "INFO")
        else:
            log_callback(f"✅ Обработка завершена! Создано {len(clips)} Shorts клипов за {total_time:.1f}с", "INFO")
        
    except Exception as e:
        import traceback
        log_callback(f"❌ Ошибка обработки: {e}", "ERROR")
        log_callback(traceback.format_exc(), "DEBUG")
    finally:
        state.is_processing = False
        state.is_paused = False