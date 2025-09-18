@echo off
echo ===================================================
echo      CORRECTION DE LOCALHOST POUR VOTRE PROJET
echo ===================================================
echo.
echo Ce script va corriger localhost pour qu'il fonctionne 
echo comme dans votre projet original.
echo.
echo ATTENTION: Vous devez accepter l'elevation administrateur
echo.
pause

echo Lancement de PowerShell en tant qu'administrateur...
powershell -Command "Start-Process PowerShell -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0fix-localhost-admin.ps1\"' -Verb RunAs"

echo.
echo Une fois termine, votre application sera accessible sur :
echo http://localhost (comme dans le projet original)
echo.
pause
