import pyaudio
import numpy as np

CHUNK    = 1024
FORMAT   = pyaudio.paFloat32
CHANNELS = 1
RATE     = 44100

audio = pyaudio.PyAudio()

print("=" * 50)
print("Available audio INPUT devices:")
print("=" * 50)
found = False
for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"  [{i}] {info['name']}")
        found = True

if not found:
    print("  NO INPUT DEVICES FOUND!")
    print("  Check your microphone is connected.")

print("=" * 50)
print("Speak now — watch the volume level")
print("Threshold is 0.08 — must exceed this to alert")
print("Press Ctrl+C to stop")
print("=" * 50)

try:
    stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    input_device_index=17,    # Realtek Mic Array
    frames_per_buffer=CHUNK
)

    while True:
        data   = np.frombuffer(
            stream.read(CHUNK, exception_on_overflow=False),
            dtype=np.float32
        )
        volume = float(np.max(np.abs(data)))
        bars   = int(volume * 100)
        bar    = '#' * min(bars, 40)

        if volume > 0.08:
            status = "<<< TALKING DETECTED >>>"
            color  = "\033[91m"   # red
        elif volume > 0.02:
            status = "background noise"
            color  = "\033[93m"   # yellow
        else:
            status = "silent"
            color  = "\033[92m"   # green

        print(f"\r{color}Vol:{volume:.4f}  "
              f"[{bar:<40}]  {status}\033[0m",
              end="", flush=True)

except KeyboardInterrupt:
    print("\n\nTest stopped.")
except Exception as e:
    print(f"\nERROR: {e}")
    print("Try running: pip install pyaudio")
finally:
    try:
        stream.stop_stream()
        stream.close()
    except Exception:
        pass
    audio.terminate()