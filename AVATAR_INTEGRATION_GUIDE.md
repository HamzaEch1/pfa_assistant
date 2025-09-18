# Guide d'intégration Avatar Wav2Lip - Assistant Banque Populaire

## 🎯 Vue d'ensemble

Cette intégration ajoute un avatar virtuel avec synchronisation labiale (Wav2Lip) à votre assistant bancaire. L'avatar peut parler en synchronisant ses lèvres avec l'audio généré par la synthèse vocale.

## 🏗️ Architecture

```
Frontend (React) ↔ Nginx ↔ Avatar Service (FastAPI + Wav2Lip) ↔ TTS
```

## 📦 Services déployés

### 1. Service Avatar (Port 8003)
- **Container**: `avatar_service`
- **API**: `/api/avatar/`
- **Technologie**: FastAPI + OpenCV + Mediapipe

### 2. Composant Frontend
- **Composant**: `AvatarDisplay.jsx`
- **Intégré dans**: `ChatPage.jsx`

## 🚀 Déploiement

### 1. Construire et démarrer les services

```bash
# Construire tous les services
docker compose build

# Démarrer avec l'avatar
docker compose up -d

# Vérifier le statut
docker compose ps
```

### 2. Vérifier les services

```bash
# API Avatar
curl http://localhost/api/avatar/health

# Types d'avatars disponibles
curl http://localhost/api/avatar/types
```

## 🎭 Utilisation

### 1. Interface utilisateur

- **Avatar visible par défaut** : L'avatar s'affiche en haut de la zone de chat
- **Contrôles** : 
  - Bouton ✕ pour masquer
  - Sélecteur de type d'avatar
  - Bouton "Afficher l'Avatar" pour réafficher

### 2. Types d'avatars

1. **Professional** : Costume professionnel, idéal pour conseils bancaires
2. **Friendly** : Apparence amicale pour interactions décontractées  
3. **Executive** : Style exécutif pour consultations importantes

### 3. Fonctionnement

1. **Utilisateur** tape ou dicte un message
2. **Assistant** génère une réponse
3. **TTS** convertit la réponse en audio
4. **Avatar Service** génère la vidéo avec synchronisation labiale
5. **Frontend** affiche l'avatar parlant

## 🔧 Configuration avancée

### 1. Modèle Wav2Lip

Pour utiliser le vrai modèle Wav2Lip :

```bash
# Télécharger le modèle pré-entraîné
cd avatar/models
wget https://github.com/Rudrabha/Wav2Lip/releases/download/v1.0/wav2lip_gan.pth
```

### 2. Variables d'environnement

Dans `docker-compose.yml` :

```yaml
avatar:
  environment:
    - AVATAR_MODEL_PATH=/app/models/wav2lip_gan.pth
    - AVATAR_DEVICE=cpu  # ou 'cuda' pour GPU
    - AVATAR_QUALITY=high
```

### 3. Performance

- **CPU seulement** : ~10-15 secondes par phrase
- **Avec GPU** : ~2-3 secondes par phrase
- **Mémoire** : 2-3GB recommandés

## 🎨 Personnalisation

### 1. Avatars personnalisés

Ajoutez vos propres images d'avatar dans :
```
avatar/avatar_images/
├── professional_avatar.jpg
├── friendly_avatar.jpg
└── executive_avatar.jpg
```

### 2. Styles CSS

Modifiez `AvatarDisplay.jsx` pour personnaliser :
- Taille de l'avatar
- Animations
- Couleurs
- Effets visuels

### 3. API endpoints

Ajoutez des endpoints dans `avatar/main.py` :
- `/avatar/custom-generate`
- `/avatar/presets`
- `/avatar/backgrounds`

## 🔍 Dépannage

### 1. Erreurs communes

**Avatar ne s'affiche pas** :
```bash
# Vérifier les logs
docker compose logs avatar

# Vérifier la connectivité
curl http://localhost:8003/health
```

**Génération lente** :
- Vérifiez la mémoire disponible
- Réduisez la qualité vidéo
- Utilisez des textes plus courts

**Erreurs de synchronisation** :
- Vérifiez la qualité de l'audio TTS
- Ajustez les paramètres de détection faciale

### 2. Logs utiles

```bash
# Logs Avatar Service
docker compose logs avatar -f

# Logs Nginx (proxying)
docker compose logs nginx -f

# Logs Frontend
docker compose logs frontend -f
```

### 3. Tests de performance

```bash
# Test génération simple
curl -X POST http://localhost/api/avatar/generate-from-text \
  -F "text=Bonjour, je suis votre assistant bancaire" \
  -F "avatar_type=professional"

# Benchmark
time curl -X POST http://localhost/api/avatar/generate-from-text \
  -F "text=Test de performance" \
  -F "avatar_type=professional" \
  -o test_avatar.mp4
```

## 📊 Monitoring

### 1. Métriques importantes

- **Temps de génération** : < 15s recommandé
- **Utilisation mémoire** : < 3GB
- **Taille des vidéos** : 1-5MB par phrase
- **Taux d'erreur** : < 5%

### 2. Santé des services

```bash
# Healthcheck automatique dans docker-compose
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
  interval: 30s
  timeout: 5s
  retries: 3
```

## 🚀 Améliorations futures

### 1. Prochaines fonctionnalités

- [ ] Support GPU pour accélération
- [ ] Avatars 3D avec Three.js
- [ ] Expressions faciales émotionnelles
- [ ] Synchronisation gestuelle
- [ ] Avatars personnalisés par utilisateur

### 2. Intégrations possibles

- **Caméra utilisateur** : Avatar miroir
- **Reconnaissance émotions** : Adapter expressions
- **Multilingue** : Avatars par langue
- **Réalité augmentée** : Avatar AR mobile

## 📞 Support

Pour toute question ou problème :

1. **Logs** : Toujours vérifier les logs Docker
2. **Documentation** : Consulter la doc Wav2Lip officielle
3. **Performance** : Monitorer CPU/mémoire
4. **Tests** : Utiliser les endpoints de test

---

**Développé pour la Banque Populaire** 🏦
*Assistant virtuel nouvelle génération avec avatar interactif*
