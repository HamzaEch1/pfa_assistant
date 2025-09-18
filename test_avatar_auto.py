#!/usr/bin/env python3
"""
Script de test pour vérifier la génération automatique d'avatar
pour les questions bancaires spécifiques
"""

import requests
import json
import time
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
AVATAR_SERVICE_URL = "http://localhost:8003"

def test_avatar_health():
    """Test de santé du service avatar"""
    print("🔍 Vérification du service avatar...")
    try:
        response = requests.get(f"{AVATAR_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ Service avatar opérationnel")
            return True
        else:
            print(f"❌ Service avatar non disponible: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur connexion service avatar: {e}")
        return False

def test_api_health():
    """Test de santé de l'API principale"""
    print("🔍 Vérification de l'API principale...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API principale opérationnelle")
            return True
        else:
            print(f"❌ API principale non disponible: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur connexion API: {e}")
        return False

def test_avatar_detection_questions():
    """Test des questions qui devraient déclencher la génération d'avatar"""
    
    test_questions = [
        "Qu'est-ce que la table CLIENT_QT?",
        "Qui est propriétaire de la base de données?",
        "Explique-moi les colonnes de la table COMPTE",
        "Quels sont les champs de la table TRANSACTION?",
        "Comment fonctionne le système bancaire?",
        "Donne-moi des informations sur les données bancaires",
        "Analyse des données CLIENT_QT",
        "Propriétaire des données bancaires"
    ]
    
    print("\n🎬 Test de détection automatique d'avatar...")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Test {i}/8: {question} ---")
        
        payload = {
            "message": question,
            "session_id": f"test_session_{i}",
            "user_id": "test_user"
        }
        
        try:
            print("📤 Envoi de la question...")
            response = requests.post(
                f"{API_BASE_URL}/api/chat/",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Réponse reçue")
                
                # Vérification de la présence d'avatar
                if "avatar_video_url" in data and data["avatar_video_url"]:
                    print(f"🎥 Avatar généré: {data['avatar_video_url']}")
                    
                    # Test d'accès au fichier vidéo
                    try:
                        video_response = requests.get(f"{API_BASE_URL}{data['avatar_video_url']}")
                        if video_response.status_code == 200:
                            print(f"✅ Vidéo accessible ({len(video_response.content)} bytes)")
                        else:
                            print(f"❌ Vidéo non accessible: {video_response.status_code}")
                    except Exception as e:
                        print(f"❌ Erreur accès vidéo: {e}")
                        
                else:
                    print("ℹ️  Pas d'avatar généré pour cette question")
                
                # Affichage de la réponse (tronquée)
                if "content" in data:
                    content = data["content"][:200] + "..." if len(data["content"]) > 200 else data["content"]
                    print(f"💬 Réponse: {content}")
                    
            else:
                print(f"❌ Erreur API: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Détails: {error_data}")
                except:
                    print(f"   Réponse brute: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print("⏰ Timeout - La génération prend plus de 60 secondes")
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur réseau: {e}")
        
        # Pause entre les tests
        if i < len(test_questions):
            print("⏳ Pause de 2 secondes...")
            time.sleep(2)

def test_manual_avatar_generation():
    """Test de génération manuelle d'avatar"""
    print("\n🎨 Test de génération manuelle d'avatar...")
    
    payload = {
        "text": "Bonjour, je suis votre assistant bancaire. La table CLIENT_QT contient les informations des clients.",
        "avatar_type": "professional"
    }
    
    try:
        response = requests.post(
            f"{AVATAR_SERVICE_URL}/generate_avatar_from_text",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Avatar généré manuellement")
            print(f"🎥 Chemin: {data.get('video_path', 'Non spécifié')}")
        else:
            print(f"❌ Erreur génération manuelle: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS D'AVATAR AUTOMATIQUE")
    print("=" * 50)
    
    # Tests de santé
    avatar_healthy = test_avatar_health()
    api_healthy = test_api_health()
    
    if not avatar_healthy or not api_healthy:
        print("\n❌ Services non disponibles - Arrêt des tests")
        return
    
    # Test de génération manuelle
    test_manual_avatar_generation()
    
    # Tests de détection automatique
    test_avatar_detection_questions()
    
    print("\n" + "=" * 50)
    print("🏁 TESTS TERMINÉS")
    print("\nInstructions pour tester manuellement:")
    print("1. Ouvrir http://localhost:3000")
    print("2. Poser ces questions:")
    print("   - 'Qu'est-ce que la table CLIENT_QT?'")
    print("   - 'Qui est propriétaire des données?'")
    print("   - 'Explique-moi les données bancaires'")
    print("3. Vérifier que l'avatar apparaît automatiquement")

if __name__ == "__main__":
    main()
