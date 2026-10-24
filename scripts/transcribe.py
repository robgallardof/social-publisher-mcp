# Transcribe videos (Spanish) to understand them before writing copy. Needs faster-whisper + numpy + imageio-ffmpeg.
# Usage: python transcribe.py <out dir> <video>...
import sys, os, subprocess
import numpy as np, imageio_ffmpeg
from faster_whisper import WhisperModel
try:
    m = WhisperModel("small", device="cuda", compute_type="float16")
except Exception:
    m = WhisperModel("small", device="cpu", compute_type="int8")
out = sys.argv[1]
for f in sys.argv[2:]:
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True, stdin=subprocess.DEVNULL).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, info = m.transcribe(audio, language="es", vad_filter=True)
    text = " ".join(s.text.strip() for s in segs)
    open(os.path.join(out, os.path.basename(f)[:6] + ("b" if " 2" in f else "") + ".txt"), "w", encoding="utf-8").write(text)
    print("==", os.path.basename(f), "\n", text, flush=True)
