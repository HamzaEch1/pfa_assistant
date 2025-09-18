#!/usr/bin/env python3
"""
Test avec authentification pour la fonctionnalité d'avatar automatique
"""

import requests
import json

API_BASE = "http://localhost:8000"

def login():
    """Connexion et récupération du token"""
    login_data = {
        "username": "admin",  # Utilisateur par défaut
        "password": "admin123"  # Mot de passe par défaut
    }
    
    try:
        print("🔐 Tentative de connexion...")
        response = requests.post(
            f"{API_BASE}/api/v1/auth/login",
            data=login_data,  # form data for OAuth2
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            if "access_token" in token_data and token_data["access_token"]:
                print("✅ Connexion réussie")
                return token_data["access_token"]
            else:
                print("⚠️  2FA requis ou problème de token")
                print(f"Réponse: {token_data}")
                return None
        else:
            print(f"❌ Échec de connexion: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def test_chat_with_avatar(token):
    """Test du chat avec détection d'avatar"""
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": "Qu'est-ce que la table CLIENT_QT?",
        "conversation_id": "test_conv_1"
    }
    
    try:
        print("📤 Test avec authentification...")
        response = requests.post(
            f"{API_BASE}/api/v1/chat/message",
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
            elif "message" in data:
                print(f"💬 Message: {data['message'][:200]}...")
            else:
                print(f"📋 Données: {data}")
                
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"❌ Réponse: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_without_auth():
    """Test simple sans authentification d'abord"""
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": "Hello",
        "conversation_id": "test"
    }
    
    try:
        print("📤 Test sans authentification...")
        response = requests.post(
            f"{API_BASE}/api/v1/chat/message",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Status: {response.status_code}")
        print(f"📋 Réponse: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("🔒 Authentification requise (normal)")
            return True
        else:
            print("⚠️  Réponse inattendue")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    print("🚀 TEST D'AVATAR AVEC AUTHENTIFICATION")
    print("=" * 45)
    
    # Test sans auth d'abord
    print("\n1. Test sans authentification:")
    auth_required = test_without_auth()
    
    if not auth_required:
        print("⚠️  L'authentification ne semble pas requise, test direct...")
        test_chat_with_avatar("")
        return
    
    # Test avec auth
    print("\n2. Test avec authentification:")
    token = login()
    
    if token:
        test_chat_with_avatar(token)
    else:
        print("❌ Impossible de se connecter")
        print("\nℹ️  Vérifiez que l'utilisateur 'admin' existe")
        print("ℹ️  Ou essayez de créer un compte via l'interface web")

if __name__ == "__main__":
    main()
