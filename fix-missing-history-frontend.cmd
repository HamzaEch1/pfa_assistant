@echo off
echo 🔍 DIAGNOSTIC HISTORIQUE MANQUANT - UTILISATEUR KHADIJA
echo.

echo 📊 VÉRIFICATION BASE DE DONNÉES:
echo ✅ Utilisateur khadija existe (ID: 2)
echo ✅ 10+ conversations trouvées en base de données
echo ✅ Dernière conversation: 27 mai 2025
echo.

echo 🔍 PROBLÈME IDENTIFIÉ:
echo - Base de données: ✅ Historique présent
echo - API: ⚠️ Authentification requise
echo - Frontend: ❌ Historique non affiché
echo.

echo 💡 CAUSES POSSIBLES:
echo 1. Cache navigateur (localStorage/sessionStorage)
echo 2. Session expirée côté frontend
echo 3. Token JWT expiré ou invalide
echo 4. Problème de connexion frontend ↔ API
echo.

echo 🔧 SOLUTIONS À TESTER:
echo.
echo SOLUTION 1: Nettoyage cache navigateur
echo 1. Appuyez sur F12 (Outils développeur)
echo 2. Onglet Application → Storage
echo 3. Supprimez localStorage et sessionStorage
echo 4. Rechargez la page (F5)
echo.
echo SOLUTION 2: Reconnexion complète
echo 1. Déconnectez-vous complètement
echo 2. Fermez tous les onglets
echo 3. Reconnectez-vous avec: khadija / [mot de passe]
echo.
echo SOLUTION 3: Navigation privée (test)
echo 1. Ouvrez un onglet privé
echo 2. Allez sur: http://localhost
echo 3. Connectez-vous avec khadija
echo 4. Vérifiez si l'historique apparaît
echo.

echo 📝 SI AUCUNE SOLUTION NE FONCTIONNE:
echo Problème probable: Frontend ne charge pas les conversations
echo.
echo SOLUTION AVANCÉE: Redémarrage frontend
docker-compose restart frontend

echo.
echo ⏳ Attente redémarrage frontend...
timeout /t 15

echo.
echo ✅ Frontend redémarré !
echo.
echo 🧪 TESTEZ MAINTENANT:
echo 1. Allez sur: http://localhost
echo 2. Connectez-vous avec: khadija
echo 3. L'historique devrait apparaître dans la sidebar
echo.

echo 🎯 SI LE PROBLÈME PERSISTE:
echo 1. Vérifiez la console navigateur (F12)
echo 2. Regardez s'il y a des erreurs JavaScript
echo 3. Vérifiez les requêtes API dans l'onglet Network
echo.

pause 