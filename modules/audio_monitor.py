import pyaudio
import numpy as np
import threading
import queue

CHUNK          = 2048
FORMAT         = pyaudio.paFloat32
CHANNELS       = 1
RATE           = 16000
INPUT_DEVICE   = 2        # Microphone Array (Realtek) - confirmed working
THRESHOLD      = 0.008    # tuned for your mic (maxVol was 0.018)

audio_queue = queue.Queue()
_running    = False
_audio      = None
_stream     = None


def _monitor():
    global _running, _stream
    try:
        _stream = _audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=INPUT_DEVICE,
            frames_per_buffer=CHUNK
        )
        print(f"Audio monitoring active — "
              f"device [{INPUT_DEVICE}] "
              f"Microphone Array (Realtek) @ {RATE}Hz")
        print(f"Threshold = {THRESHOLD} "
              f"(speak to trigger alert)")

        while _running:
            try:
                data = np.frombuffer(
                    _stream.read(
                        CHUNK,
                        exception_on_overflow=False
                    ),
                    dtype=np.float32
                )
                # Remove NaN / inf values
                data   = data[np.isfinite(data)]
                if len(data) == 0:
                    continue

                volume = float(np.max(np.abs(data)))

                # Debug — uncomment to see live volume:
                # print(f"vol={volume:.5f}")

                if volume > THRESHOLD:
                    audio_queue.put(round(volume, 4))

            except Exception:
                pass

    except Exception as e:
        print(f"Audio stream error: {e}")
    finally:
        try:
            if _stream:
                _stream.stop_stream()
                _stream.close()
        except Exception:
            pass


def start_audio_monitor():
    global _running, _audio
    try:
        _audio   = pyaudio.PyAudio()
        _running = True
        t = threading.Thread(
            target=_monitor,
            daemon=True
        )
        t.start()
        return True
    except Exception as e:
        print(f"Audio monitor failed: {e}")
        return False


def stop_audio_monitor():
    global _running, _audio, _stream
    _running = False
    try:
        if _stream:
            _stream.stop_stream()
            _stream.close()
        if _audio:
            _audio.terminate()
    except Exception:
        pass


def get_audio_alert():
    """Returns volume if talking detected, else None."""
    if not audio_queue.empty():
        return audio_queue.get()
    return None