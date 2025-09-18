#!/usr/bin/env python3
"""
Test spécifique pour les erreurs de reconnaissance CLIENT_QT
"""
import numpy as np
import soundfile as sf
import requests
import tempfile
import os

def test_client_qt_corrections():
    """Teste spécifiquement les corrections pour CLIENT_QT"""
    
    print("🎯 Test des corrections CLIENT_QT")
    
    # Test avec audio de durée moyenne (3.5s) qui génère l'erreur "colande client culant"
    sample_rate = 16000
    duration = 3.5
    
    # Simuler une voix avec énergie faible pour déclencher l'erreur
    audio_data = np.random.random(int(sample_rate * duration)) * 0.08  # Énergie faible
    
    # Ajouter un pattern vocal réaliste
    t = np.linspace(0, duration, int(sample_rate * duration))
    voice_pattern = np.sin(2 * np.pi * 150 * t) * 0.05  # Voix plus douce
    audio_data = audio_data + voice_pattern
    
    # Créer un fichier temporaire
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        sf.write(temp_file.name, audio_data, sample_rate)
        temp_path = temp_file.name
    
    try:
        print(f"📤 Test avec audio de {duration}s (énergie faible)")
        
        with open(temp_path, 'rb') as f:
            files = {'audio_file': ('test.wav', f, 'audio/wav')}
            data = {'language': 'fr', 'include_timestamps': 'true'}
            response = requests.post('http://127.0.0.1:8004/transcribe', files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                transcription = result.get('transcription', {}).get('text', '')
                print(f"   📝 Transcription brute: '{transcription}'")
                
                # Vérifier que la correction a fonctionné
                if "CLIENT_QT" in transcription.upper():
                    print("   ✅ CLIENT_QT correctement reconnu !")
                elif any(word in transcription.lower() for word in ["colande", "culant", "cléons", "culon"]):
                    print("   ⚠️  Termes d'erreur détectés mais pas encore corrigés")
                else:
                    print("   ❓ Transcription inattendue")
                    
                print(f"   🎯 Résultat final: {transcription}")
            else:
                print(f"   ❌ Erreur HTTP {response.status_code}: {response.text}")
                
    finally:
        os.unlink(temp_path)

def test_various_durations():
    """Teste différentes durées pour voir les patterns de reconnaissance"""
    durations = [1.5, 2.8, 3.2, 3.8, 5.0]
    
    for duration in durations:
        print(f"\n⏱️  Test durée {duration}s")
        
        sample_rate = 16000
        audio_data = np.random.random(int(sample_rate * duration)) * 0.1
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)
            temp_path = temp_file.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'audio_file': ('test.wav', f, 'audio/wav')}
                data = {'language': 'fr'}
                response = requests.post('http://127.0.0.1:8004/transcribe', files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get('transcription', {}).get('text', '')
                    print(f"   📝 '{transcription}'")
                    
                    if "CLIENT_QT" in transcription.upper():
                        print("   ✅ CLIENT_QT reconnu")
                    else:
                        print("   ❌ CLIENT_QT non reconnu")
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    test_client_qt_corrections()
    test_various_durations()
