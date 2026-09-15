import sounddevice as sd
import numpy as np

print('Test enregistrement Bluetooth Poly V4320...')
print('Parlez pendant 3 secondes !')

audio = sd.rec(int(3 * 16000), samplerate=16000, channels=1, dtype='float32', device=2)
sd.wait()

volume = np.abs(audio).mean()
print(f'Volume detecte : {volume:.4f}')

if volume > 0.005:
    print('✅ Bluetooth micro fonctionne !')
else:
    print('❌ Signal trop faible, verifiez le casque')
