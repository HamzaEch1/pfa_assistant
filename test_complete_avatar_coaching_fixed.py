#!/usr/bin/env python3
"""
Script de test complet pour la stack Avatar + Coaching + Whisper
Teste toutes les fonctionnalités en temps réel
"""

import requests
import json
import time
import asyncio
import logging
from pathlib import Path
import tempfile
import wave
import numpy as np

# Configuration
API_BASE = "http://localhost:8000"
AVATAR_SERVICE = "http://localhost:8003"
WHISPER_SERVICE = "http://localhost:8004"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AvatarCoachingTester:
    def __init__(self):
        self.token = None
        self.session_id = f"test_session_{int(time.time())}"
        
    async def run_complete_test(self):
        """Execute le test complet de la stack"""
        
        print("🚀 DÉMARRAGE DES TESTS COMPLETS AVATAR + COACHING + WHISPER")
        print("=" * 70)
        
        # 1. Test des services de base
        if not await self.test_services_health():
            print("❌ Services non disponibles - Arrêt des tests")
            return
            
        # 2. Authentification
        if not await self.authenticate():
            print("❌ Authentification échouée - Arrêt des tests")
            return
            
        # 3. Test Whisper (reconnaissance vocale)
        await self.test_whisper_service()
        
        # 4. Test Avatar simple
        await self.test_avatar_generation()
        
        # 5. Test Coaching KPI
        await self.test_kpi_coaching()
        
        # 6. Test Pipeline complet (Voix → Avatar + Coaching)
        await self.test_complete_pipeline()
        
        # 7. Test des questions spécifiques données bancaires
        await self.test_banking_data_questions()
        
        print("\n" + "=" * 70)
        print("🏁 TESTS TERMINÉS")
        
    async def test_services_health(self):
        """Test de santé de tous les services"""
        print("\n🔍 TEST DE SANTÉ DES SERVICES")
        print("-" * 40)
        
        services = [
            ("API Principal", f"{API_BASE}/health"),
            ("Avatar Service", f"{AVATAR_SERVICE}/health"),
            ("Whisper Service", f"{WHISPER_SERVICE}/health")
        ]
        
        all_healthy = True
        
        for name, url in services:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {name}: Opérationnel")
                else:
                    print(f"❌ {name}: Erreur {response.status_code}")
                    all_healthy = False
            except Exception as e:
                print(f"❌ {name}: Non accessible ({e})")
                all_healthy = False
                
        return all_healthy
    
    async def authenticate(self):
        """Authentification sur l'API"""
        print("\n🔐 AUTHENTIFICATION")
        print("-" * 40)
        
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = requests.post(
                f"{API_BASE}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                if "access_token" in token_data and token_data["access_token"]:
                    self.token = token_data["access_token"]
                    print("✅ Authentification réussie")
                    return True
                    
            print(f"❌ Échec authentification: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Erreur authentification: {e}")
            return False
    
    async def test_whisper_service(self):
        """Test du service de reconnaissance vocale"""
        print("\n🎤 TEST WHISPER (RECONNAISSANCE VOCALE)")
        print("-" * 40)
        
        try:
            # Créer un fichier audio factice
            audio_data = await self.create_fake_audio()
            
            # Test transcription
            files = {"audio_file": ("test_audio.wav", audio_data, "audio/wav")}
            data = {"language": "fr", "include_timestamps": "true"}
            
            response = requests.post(
                f"{WHISPER_SERVICE}/transcribe",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Transcription réussie")
                print(f"   Texte: {result.get('text', 'N/A')[:100]}...")
                print(f"   Langue: {result.get('language', 'N/A')}")
                
                # Test analyse de contenu
                await self.test_speech_analysis(result.get('text', 'Test'))
                
            else:
                print(f"❌ Échec transcription: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur Whisper: {e}")
    
    async def test_speech_analysis(self, text):
        """Test de l'analyse sémantique du contenu vocal"""
        try:
            data = {
                "text": text,
                "detect_intent": "true",
                "extract_keywords": "true"
            }
            
            response = requests.post(
                f"{WHISPER_SERVICE}/analyze-speech",
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Analyse vocale réussie")
                print(f"   Intention: {result.get('intent', 'N/A')}")
                print(f"   Mots-clés: {result.get('keywords', [])}")
                print(f"   Coaching nécessaire: {result.get('coaching_needed', False)}")
            else:
                print(f"❌ Échec analyse vocale: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur analyse: {e}")
    
    async def test_avatar_generation(self):
        """Test de génération d'avatar simple"""
        print("\n🎭 TEST GÉNÉRATION AVATAR")
        print("-" * 40)
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            data = {
                "question": "Qu'est-ce que la table CLIENT_QT?",
                "user_level": "beginner",
                "include_coaching": "true"
            }
            
            response = requests.post(
                f"{API_BASE}/avatar/generate-real-time-response",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Avatar généré avec succès")
                print(f"   URL Vidéo: {result.get('video_url', 'N/A')}")
                print(f"   URL Audio: {result.get('audio_url', 'N/A')}")
                print(f"   Coaching inclus: {result.get('coaching_module') is not None}")
                
                if result.get('coaching_module'):
                    module = result['coaching_module']
                    print(f"   Module: {module.get('title', 'N/A')}")
                    print(f"   Durée: {module.get('duration_minutes', 'N/A')} min")
                    print(f"   Leçons: {len(module.get('lessons', []))}")
                    print(f"   Quiz: {len(module.get('quiz', []))} questions")
                    
            else:
                print(f"❌ Échec génération avatar: {response.status_code}")
                print(f"   Réponse: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Erreur avatar: {e}")
    
    async def test_kpi_coaching(self):
        """Test spécifique du coaching KPI"""
        print("\n🎯 TEST COACHING KPI")
        print("-" * 40)
        
        questions_kpi = [
            "Comment mettre à jour un KPI efficacement?",
            "Quelles sont les bonnes pratiques pour les indicateurs?",
            "Je veux optimiser mes métriques de performance"
        ]
        
        for question in questions_kpi:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    "question": question,
                    "user_level": "intermediate",
                    "include_coaching": "true"
                }
                
                response = requests.post(
                    f"{API_BASE}/avatar/generate-real-time-response",
                    headers=headers,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    coaching = result.get('coaching_module')
                    
                    if coaching:
                        print(f"✅ Coaching généré pour: '{question[:50]}...'")
                        print(f"   Titre: {coaching.get('title', 'N/A')}")
                        print(f"   Leçons: {len(coaching.get('lessons', []))}")
                        
                        # Test soumission de quiz
                        if coaching.get('quiz'):
                            await self.test_quiz_submission(coaching['quiz'][0])
                    else:
                        print(f"⚠️  Pas de coaching pour: '{question[:50]}...'")
                        
                await asyncio.sleep(1)  # Pause entre les tests
                
            except Exception as e:
                print(f"❌ Erreur coaching: {e}")
    
    async def test_quiz_submission(self, quiz_question):
        """Test de soumission d'une réponse de quiz"""
        try:
            data = {
                "question_id": 0,
                "answer": 1,  # Réponse arbitraire
                "coaching_session_id": self.session_id
            }
            
            response = requests.post(
                f"{API_BASE}/avatar/quiz/submit",
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   📝 Quiz soumis - Correct: {result.get('correct', False)}")
            else:
                print(f"   ❌ Échec soumission quiz: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur quiz: {e}")
    
    async def test_complete_pipeline(self):
        """Test du pipeline complet: Voix → Analyse → Avatar + Coaching"""
        print("\n🔄 TEST PIPELINE COMPLET")
        print("-" * 40)
        
        # Simuler un input vocal
        fake_speech = "Je veux apprendre les bonnes pratiques pour mettre à jour mes KPI"
        
        try:
            # 1. Analyse de l'intention vocale
            analysis_data = {
                "text": fake_speech,
                "detect_intent": "true",
                "extract_keywords": "true"
            }
            
            analysis_response = requests.post(
                f"{WHISPER_SERVICE}/analyze-speech",
                data=analysis_data
            )
            
            if analysis_response.status_code != 200:
                print("❌ Échec analyse intention")
                return
                
            analysis = analysis_response.json()
            print(f"✅ Intention détectée: {analysis.get('intent', 'N/A')}")
            
            # 2. Génération avatar basée sur l'intention
            headers = {"Authorization": f"Bearer {self.token}"}
            avatar_data = {
                "question": fake_speech,
                "user_level": "beginner",
                "include_coaching": str(analysis.get('coaching_needed', False)).lower()
            }
            
            avatar_response = requests.post(
                f"{API_BASE}/avatar/generate-real-time-response",
                headers=headers,
                data=avatar_data
            )
            
            if avatar_response.status_code == 200:
                result = avatar_response.json()
                print("✅ Pipeline complet réussi")
                print(f"   Avatar: {result.get('video_url') is not None}")
                print(f"   Coaching: {result.get('coaching_module') is not None}")
                
                # 3. Test streaming en temps réel
                await self.test_streaming_response(fake_speech)
                
            else:
                print(f"❌ Échec pipeline: {avatar_response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur pipeline: {e}")
    
    async def test_streaming_response(self, question):
        """Test du streaming de réponse en temps réel"""
        try:
            data = {
                "question": question,
                "include_coaching": "true"
            }
            
            response = requests.post(
                f"{API_BASE}/avatar/stream-response",
                data=data,
                stream=True
            )
            
            if response.status_code == 200:
                print("✅ Streaming démarré")
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data = json.loads(line_str[6:])
                            print(f"   📡 {data.get('type', 'unknown')}: {data.get('content', '')[:50]}...")
                            
                            if data.get('type') == 'complete':
                                break
            else:
                print(f"❌ Échec streaming: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur streaming: {e}")
    
    async def test_banking_data_questions(self):
        """Test des questions spécifiques sur les données bancaires"""
        print("\n💼 TEST QUESTIONS DONNÉES BANCAIRES")
        print("-" * 40)
        
        banking_questions = [
            "Qu'est-ce que la table CLIENT_QT?",
            "Qui est propriétaire des données bancaires?",
            "Comment sont structurées les données clients?",
            "Quels sont les flux de données dans le système?",
            "Comment assurer la sécurité des données?"
        ]
        
        for question in banking_questions:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    "question": question,
                    "dataset_context": "Banque Populaire - Système Core Banking",
                    "avatar_type": "professional"
                }
                
                response = requests.post(
                    f"{API_BASE}/avatar/generate-data-explanation",
                    headers=headers,
                    data=data
                )
                
                if response.status_code == 200:
                    print(f"✅ Explication générée: '{question[:40]}...'")
                    # Le response est un FileResponse (vidéo)
                    video_size = len(response.content)
                    print(f"   Taille vidéo: {video_size} bytes")
                else:
                    print(f"❌ Échec pour: '{question[:40]}...' ({response.status_code})")
                    
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Erreur question bancaire: {e}")
    
    async def create_fake_audio(self):
        """Crée un fichier audio factice pour les tests"""
        # Générer un signal audio simple (silence + bip)
        sample_rate = 16000
        duration = 2  # 2 secondes
        samples = np.zeros(sample_rate * duration, dtype=np.int16)
        
        # Ajouter un bip au milieu
        bip_freq = 440  # Hz
        bip_duration = 0.1  # secondes
        bip_samples = int(sample_rate * bip_duration)
        bip_start = sample_rate  # 1 seconde
        
        t = np.linspace(0, bip_duration, bip_samples)
        bip = (np.sin(2 * np.pi * bip_freq * t) * 16000).astype(np.int16)
        samples[bip_start:bip_start + bip_samples] = bip
        
        # Créer le fichier WAV en mémoire
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            with wave.open(f.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(samples.tobytes())
            
            # Lire le contenu
            with open(f.name, 'rb') as audio_file:
                return audio_file.read()

async def main():
    """Fonction principale"""
    tester = AvatarCoachingTester()
    await tester.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())
