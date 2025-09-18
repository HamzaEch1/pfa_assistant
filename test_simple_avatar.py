#!/usr/bin/env python3
"""
Test simple de la fonctionnalité d'avatar automatique
"""

import requests
import json

def test_simple_chat():
    """Test simple du chat avec détection d'avatar"""
    
    # Test question qui devrait déclencher un avatar
    payload = {
        "message": "Qu'est-ce que la table CLIENT_QT?",
        "session_id": "test_session_1",
        "user_id": "test_user"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("📤 Test de la question: 'Qu'est-ce que la table CLIENT_QT?'")
        
        response = requests.post(
            "http://localhost:8000/api/v1/chat/message",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Réponse reçue!")
            
            # Vérifier la présence d'avatar
            if "avatar_video_url" in data and data["avatar_video_url"]:
                print(f"🎥 Avatar généré: {data['avatar_video_url']}")
                print("✅ Fonctionnalité d'avatar automatique FONCTIONNE!")
            else:
                print("ℹ️  Pas d'avatar généré")
                
            # Afficher la réponse
            if "content" in data:
                print(f"💬 Réponse: {data['content'][:200]}...")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"❌ Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_simple_chat()
