import subprocess
import asyncio
from pathlib import Path


def _check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


async def _edge_tts(text, output_path):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, 'ru-RU-SvetlanaNeural')
        await communicate.save(str(output_path))
        return True
    except Exception:
        return False


def _pyttsx3_tts(text, output_path):
    try:
        import pyttsx3
        import os

        engine = pyttsx3.init(driverName='sapi5')

        voices = engine.getProperty('voices')
        russian_voice = None
        for v in voices:
            if 'russian' in v.name.lower() or 'ru' in v.id.lower():
                russian_voice = v.id
                break
        if russian_voice:
            engine.setProperty('voice', russian_voice)

        engine.setProperty('rate', 200)

        temp_wav = output_path.with_suffix('.wav')
        engine.save_to_file(text, str(temp_wav))
        engine.runAndWait()

        if _check_ffmpeg():
            subprocess.run([
                'ffmpeg', '-y', '-i', str(temp_wav),
                '-codec:a', 'libmp3lame', '-qscale:a', '2',
                str(output_path)
            ], capture_output=True, check=True)
            os.remove(temp_wav)
        else:
            import shutil
            shutil.move(str(temp_wav), str(output_path.with_suffix('.wav')))

        return True
    except Exception:
        return False


async def text_to_speech(text, output_path):
    output_path = Path(output_path)

    ok = await _edge_tts(text, output_path)
    if ok:
        return True

    ok = _pyttsx3_tts(text, output_path)
    if ok:
        return True

    print(f'  WARNING: не удалось озвучить, нет TTS')
    return False
