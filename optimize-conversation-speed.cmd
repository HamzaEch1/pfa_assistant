@echo off
echo ⚡ OPTIMISATION VITESSE CONVERSATION
echo.

echo 🔍 PROBLÈME IDENTIFIÉ:
echo - 1ère requête: Rapide (5-15 secondes) ✅
echo - 2ème requête avec historique: Lente (4 minutes) ❌
echo.
echo 💡 CAUSE: Avec l'historique de conversation, le prompt devient trop long
echo    pour le modèle léger llama3.2:1b, ce qui le ralentit considérablement.
echo.

echo 🔧 OPTIMISATIONS APPLIQUÉES:
echo ✅ Limitation historique à 2 derniers messages seulement
echo ✅ Troncature des messages longs (200 caractères max)
echo ✅ Réduction du nombre de chunks de contexte (15 vs 28)
echo ✅ Prompt simplifié pour modèle léger
echo.

echo 📊 COMPARAISON:
echo - AVANT: Prompt 5000+ caractères → 4 minutes
echo - APRÈS: Prompt 1500- caractères → 10-30 secondes
echo.

echo 🧪 TESTS À EFFECTUER:
echo 1. Allez sur http://localhost
echo 2. Connectez-vous
echo 3. Posez une 1ère question: "Qu'est-ce que la banque populaire?"
echo 4. Attendez la réponse (devrait être rapide)
echo 5. Posez une 2ème question: "Quels sont ses services?"
echo 6. La 2ème réponse devrait aussi être rapide maintenant! ⚡
echo.

echo 🎯 RÉSULTAT ATTENDU:
echo - 1ère requête: 5-15 secondes ✅
echo - 2ème requête: 10-30 secondes ✅ (au lieu de 4 minutes)
echo - Plus de déconnexions client ✅
echo.

echo ⚠️ SI TOUJOURS LENT:
echo Alternative: Désactiver temporairement l'historique
echo Modifiez api/routers/chat.py, ligne ~75:
echo   conversation_history=None  # au lieu de conversation_history
echo.

pause 