import sounddevice as sd
import numpy as np

# Tous les devices d'entree Poly V4320
devices_a_tester = {
    2:  'Casque Poly MME',
    10: 'Casque Poly DirectSound',
    21: 'Casque Poly WASAPI',
    22: 'Casque Poly WDM-KS Hands-Free',
    25: 'Casque Poly WDM-KS Input',
    28: 'Casque Poly WDM-KS Input 2',
}

print('🎧 Test de tous les devices Bluetooth Poly V4320...')
print('Parlez fort pendant chaque test !\n')

resultats = {}

for device_id, nom in devices_a_tester.items():
    try:
        print(f'Test device [{device_id}] {nom}...')
        print('  → Parlez maintenant pendant 2 secondes !')
        audio = sd.rec(
            int(2 * 16000),
            samplerate=16000,
            channels=1,
            dtype='float32',
            device=device_id
        )
        sd.wait()
        volume = np.abs(audio).mean()
        resultats[device_id] = volume
        status = '✅ OK !' if volume > 0.005 else '❌ Faible'
        print(f'  Volume : {volume:.4f} {status}\n')
    except Exception as e:
        print(f'  ⚠️  Erreur : {e}\n')
        resultats[device_id] = 0

print('=' * 40)
print('📊 RÉSULTATS :')
meilleur = max(resultats, key=resultats.get)
for device_id, volume in resultats.items():
    marker = '👉 MEILLEUR' if device_id == meilleur and volume > 0.005 else ''
    print(f'  [{device_id}] Volume: {volume:.4f} {marker}')

if resultats[meilleur] > 0.005:
    print(f'\n✅ Utilisez DEVICE_ENTREE = {meilleur} dans config.py')
else:
    print('\n❌ Aucun device ne capte le son')
    print('   Vérifiez que le casque est bien connecté en Bluetooth')
    print('   et défini comme périphérique par défaut dans Windows')
