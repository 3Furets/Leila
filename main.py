import whisper
import ollama
import sounddevice as sd
import soundfile as sf
import numpy as np
import asyncio
import edge_tts
import os
import re
import io
import pygame
from config import *
from coach_prompt import COACH_PROMPT

pygame.mixer.init()

def detecter_emotion(texte):
    texte_lower = texte.lower()
    if any(mot in texte_lower for mot in ['bravo', 'excellent', 'génial', 'super', 'félicitations']) or '!' in texte:
        return 'enthousiaste'
    elif any(mot in texte_lower for mot in ['attention', 'erreur', 'problème', 'difficile']):
        return 'serieux'
    elif any(mot in texte_lower for mot in ['doucement', 'calme', 'respire', 'détend']):
        return 'calme'
    elif '?' in texte:
        return 'curieux'
    else:
        return 'neutre'

PARAMETRES_EMOTION = {
    'enthousiaste': {'rate': '+15%', 'pitch': '+10Hz'},
    'serieux':      {'rate': '-5%',  'pitch': '-5Hz'},
    'calme':        {'rate': '-15%', 'pitch': '-8Hz'},
    'curieux':      {'rate': '+5%',  'pitch': '+5Hz'},
    'neutre':       {'rate': '+0%',  'pitch': '+0Hz'},
}

historique = [{'role': 'system', 'content': COACH_PROMPT}]

print('⏳ Chargement de Whisper...')
whisper_model = whisper.load_model(MODEL_STT)
print('✅ Whisper chargé !')

def enregistrer_audio():
    print(f'🎤 Je vous écoute... (max {DUREE_ECOUTE} secondes)')
    print('   Parlez maintenant !')

    sample_rate = 16000
    audio = sd.rec(
        int(DUREE_ECOUTE * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()

    volume = np.abs(audio).mean()
    print(f'   Volume détecté : {volume:.4f}')

    if volume < SEUIL_SILENCE:
        print('⚠️  Signal audio trop faible')
        return None

    sf.write('audio/input.wav', audio, sample_rate)
    return 'audio/input.wav'

def transcrire_audio(fichier_audio):
    print('🔄 Transcription en cours...')

    result = whisper_model.transcribe(
        fichier_audio,
        language=LANGUE,
        fp16=False,
        temperature=0.0,
        best_of=3,
        beam_size=5,
        condition_on_previous_text=True,
        initial_prompt='Bonjour, je parle en français.'
    )

    texte = result['text'].strip()
    print(f'📝 Vous avez dit : "{texte}"')
    return texte

async def synthetiser_voix_async(texte, emotion='neutre'):
    params = PARAMETRES_EMOTION[emotion]
    communicate = edge_tts.Communicate(
        texte,
        VOIX_TTS,
        rate=params['rate'],
        pitch=params['pitch']
    )
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            buffer.write(chunk['data'])
    buffer.seek(0)
    return buffer

def synthetiser_voix(texte):
    emotion = detecter_emotion(texte)
    print(f'🎭 Émotion détectée : {emotion}')
    buffer = asyncio.run(synthetiser_voix_async(texte, emotion))

    tmp_path = 'audio/tmp_tts.mp3'
    with open(tmp_path, 'wb') as f:
        f.write(buffer.read())

    pygame.mixer.music.load(tmp_path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def obtenir_et_parler_reponse(texte):
    print('🧠 Le coach réfléchit...')

    historique.append({'role': 'user', 'content': texte})

    stream = ollama.chat(
        model=MODEL_LLM,
        messages=historique,
        stream=True,
        options={'num_predict': 150, 'temperature': 0.7}
    )

    buffer = ''
    reponse_complete = ''

    for part in stream:
        morceau = part['message']['content']
        buffer += morceau
        reponse_complete += morceau

        while True:
            match = re.search(r'([.!?])(\s|$)', buffer)
            if not match:
                break
            fin = match.end()
            phrase = buffer[:fin].strip()
            buffer = buffer[fin:]
            if phrase:
                print(f'🤖 Coach : {phrase}')
                synthetiser_voix(phrase)

    if buffer.strip():
        print(f'🤖 Coach : {buffer.strip()}')
        synthetiser_voix(buffer.strip())

    historique.append({'role': 'assistant', 'content': reponse_complete})
    return reponse_complete

def main():
    os.makedirs('audio', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

    print('\n' + '=' * 45)
    print('   🎯 COACH VOCAL - Prêt !')
    print('=' * 45)
    print('💡 Conseils pour une bonne reconnaissance :')
    print('   - Parlez clairement et distinctement')
    print('   - Attendez le signal 🎤 avant de parler')
    print('   - Restez à 30-50cm du micro')
    print('   - Évitez les bruits de fond')
    print('   CTRL+C pour quitter\n')

    bienvenue = 'Bonjour ! Je suis votre coach vocal personnel. Comment puis-je vous aider aujourd\'hui ?'
    print(f'🤖 Coach : {bienvenue}')
    synthetiser_voix(bienvenue)

    while True:
        try:
            audio = enregistrer_audio()

            if audio is None:
                print('🔄 Réessayez en parlant plus fort')
                continue

            texte = transcrire_audio(audio)

            if not texte or len(texte) < 3:
                print('⚠️  Texte trop court ou vide, réessayez')
                continue

            mots_parasites = ['merci', 'sous-titres', 'transcription', '...', 'sous-titrage']
            if any(mot in texte.lower() for mot in mots_parasites) and len(texte) < 20:
                print('⚠️  Transcription incorrecte détectée, réessayez')
                continue

            obtenir_et_parler_reponse(texte)

        except KeyboardInterrupt:
            print('\n👋 Au revoir !')
            pygame.mixer.quit()
            break
        except Exception as e:
            print(f'❌ Erreur : {e}')
            print('🔄 Continuons...')

if __name__ == '__main__':
    main()
