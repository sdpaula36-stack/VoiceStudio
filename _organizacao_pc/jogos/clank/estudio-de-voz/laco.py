# Uso: python3 laco.py entrada.wav saida.ogg  -> laço sem emenda (cauda cruzada sobre o início), pico -1 dBFS.
import subprocess, sys, numpy as np
ent, sai = sys.argv[1:]
sr = 44100
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", ent, "-f", "f32le", "-ac", "2", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()
# corta silêncio final
lvl = np.abs(x).max(axis=1); fim = np.nonzero(lvl > 10 ** (-50 / 20))[0][-1] + 1; x = x[:fim]
xf = int(3.0 * sr)
corpo, cauda = x[:-xf].copy(), x[-xf:]
r = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
corpo[:xf] = corpo[:xf] * np.sqrt(r) + cauda * np.sqrt(1 - r)
corpo *= 10 ** (-1 / 20) / max(1e-6, np.abs(corpo).max())
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(sr), "-i", "-", "-c:a", "libvorbis", "-q:a", "3", sai], input=corpo.astype(np.float32).tobytes(), check=True)
print(sai, round(len(corpo) / sr, 1), "s")
