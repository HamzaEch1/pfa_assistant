@echo off
echo ===== CORRECTION DU FICHIER HOSTS POUR LOCALHOST =====
echo.
echo Le fichier hosts se trouve dans : C:\Windows\System32\drivers\etc\hosts
echo.
echo INSTRUCTIONS :
echo 1. Ouvrez le Bloc-notes en tant qu'ADMINISTRATEUR
echo 2. Ouvrez le fichier : C:\Windows\System32\drivers\etc\hosts
echo 3. Trouvez ces lignes commentées (avec #) :
echo    #       127.0.0.1       localhost
echo    #       ::1             localhost
echo.
echo 4. Supprimez le # au début de ces lignes pour obtenir :
echo    127.0.0.1       localhost
echo    ::1             localhost
echo.
echo 5. Sauvegardez le fichier
echo 6. Redémarrez votre navigateur
echo.
echo Ou bien, copiez-collez directement ces lignes à la fin du fichier :
echo 127.0.0.1       localhost
echo ::1             localhost
echo.
pause
