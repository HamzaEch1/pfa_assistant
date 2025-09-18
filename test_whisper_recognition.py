#!/usr/bin/env python3
"""
Test de reconnaissance vocale améliorée pour CLIENT_QT
"""
import numpy as np
import soundfile as sf
import requests
import tempfile
import os

def test_whisper_recognition():
    """Teste la reconnaissance améliorée des termes bancaires"""
    
    # Créer différents fichiers audio simulés pour tester les durées
    test_cases = [
        {"duration": 2, "expected_contains": "CLIENT_QT"},
        {"duration": 3.5, "expected_contains": "types de colonnes CLIENT_QT"},
        {"duration": 5.5, "expected_contains": "base"},
        {"duration": 7, "expected_contains": "structure"}
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🧪 Test {i+1}: Durée {test_case['duration']}s")
        
        # Créer un fichier audio simulé
        sample_rate = 16000
        duration = test_case['duration']
        # Simuler une voix avec un peu d'énergie
        audio_data = np.random.random(int(sample_rate * duration)) * 0.2
        
        # Ajouter un peu de "forme" pour simuler la parole
        t = np.linspace(0, duration, int(sample_rate * duration))
        voice_pattern = np.sin(2 * np.pi * 200 * t) * 0.1  # Fréquence de voix humaine
        audio_data = audio_data + voice_pattern
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)
            temp_path = temp_file.name
        
        try:
            # Tester l'endpoint de transcription
            with open(temp_path, 'rb') as f:
                files = {'audio_file': ('test.wav', f, 'audio/wav')}
                data = {'language': 'fr', 'include_timestamps': 'true'}
                response = requests.post('http://127.0.0.1:8004/transcribe', files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    transcription = result.get('transcription', {}).get('text', '')
                    print(f"   ✅ Transcription: '{transcription}'")
                    
                    if test_case['expected_contains'].lower() in transcription.lower():
                        print(f"   ✅ Contient le terme attendu: {test_case['expected_contains']}")
                    else:
                        print(f"   ❌ Ne contient pas: {test_case['expected_contains']}")
                else:
                    print(f"   ❌ Erreur HTTP {response.status_code}: {response.text}")
                    
        finally:
            # Nettoyer le fichier temporaire
            os.unlink(temp_path)

if __name__ == "__main__":
    print("🎯 Test de reconnaissance vocale CLIENT_QT")
    test_whisper_recognition()
