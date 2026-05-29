import pyaudio
import numpy as np

audio = pyaudio.PyAudio()

print("Testing all input devices - SPEAK LOUDLY during each...\n")

for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    if info['maxInputChannels'] < 1:
        continue

    name = info['name']
    skip = ['stereo mix', 'midi', 'speaker', 'wave']
    if any(s in name.lower() for s in skip):
        continue

    for rate in [16000, 44100]:
        try:
            s = audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=rate,
                input=True,
                input_device_index=i,
                frames_per_buffer=2048
            )
            vols = []
            for _ in range(15):
                d = np.frombuffer(
                    s.read(2048, exception_on_overflow=False),
                    dtype=np.float32
                )
                vols.append(float(np.max(np.abs(d))))
            s.stop_stream()
            s.close()

            maxvol = max(vols)
            status = "<<< WORKS!" if maxvol > 0.005 else "silent"
            print(f"[{i}] {name[:40]:40s} "
                  f"@ {rate}Hz  "
                  f"maxVol={maxvol:.5f}  {status}")
            break

        except Exception as e:
            print(f"[{i}] {name[:40]:40s} "
                  f"@ {rate}Hz  FAILED: {e}")

audio.terminate()
print("\nDone! Tell me which device shows WORKS!")