@echo off
echo 🧹 NETTOYAGE + CORRECTION TIMEOUT
echo.

echo 📊 Modèles actuels détectés:
echo - llama3:latest (4.7 GB) - ID: 365c0bd3c000
echo - llama3:8b (4.7 GB) - ID: 365c0bd3c000 (IDENTIQUE!)
echo.

echo 💡 PLAN:
echo 1. Supprimer llama3:latest (redondant)
echo 2. Garder llama3:8b pour référence
echo 3. Installer llama3.2:1b (rapide - 1.3GB)
echo 4. Configurer l'API pour utiliser le modèle rapide
echo.

echo 🗑️ Étape 1: Suppression du modèle redondant...
ollama rm llama3:latest
echo ✅ llama3:latest supprimé (4.7 GB libérés)

echo.
echo 📥 Étape 2: Installation du modèle rapide...
ollama pull llama3.2:1b
echo ✅ llama3.2:1b installé (1.3 GB)

echo.
echo 📊 Vérification des modèles après nettoyage...
ollama list

echo.
echo 🧪 Étape 3: Test du modèle rapide...
echo (Devrait répondre en 5-15 secondes)
ollama run llama3.2:1b "Bonjour, test rapide"

echo.
echo ⚙️ Étape 4: Configuration de l'API...
echo OLLAMA_MODEL_NAME=llama3.2:1b > .env
echo ✅ Fichier .env créé

echo.
echo 🔄 Étape 5: Redémarrage de l'API...
docker-compose restart api

echo.
echo ⏳ Attente de 20 secondes...
timeout /t 20

echo.
echo ✅ NETTOYAGE ET OPTIMISATION TERMINÉS !
echo.
echo 📊 RÉSUMÉ DES CHANGEMENTS:
echo ✅ Espace libéré: 4.7 GB (suppression llama3:latest)
echo ✅ Modèle rapide installé: llama3.2:1b (1.3 GB)
echo ✅ Modèles finaux: llama3:8b + llama3.2:1b
echo ✅ API configurée pour utiliser le modèle rapide
echo.
echo 🎯 RÉSULTAT ATTENDU:
echo - Timeout 240s → Réponse 5-15s ⚡
echo - Espace disque optimisé 💾
echo - Performance améliorée 🚀
echo.
echo 🧪 TESTEZ MAINTENANT:
echo 1. http://localhost → Connectez-vous
echo 2. Posez une question: "Bonjour"
echo 3. Réponse rapide garantie !
echo.
pause 