# 🗄️ Système de Sauvegarde PostgreSQL - Projet RAG-Almost

## 📋 Vue d'ensemble

Ce système complet de sauvegarde PostgreSQL vous permet de protéger vos données contre la perte accidentelle de conteneurs Docker. Il propose plusieurs méthodes de sauvegarde et de restauration adaptées à différents scénarios.

## 🎯 Objectif

Éviter la perte de données si les conteneurs PostgreSQL sont supprimés en gardant toujours une copie sécurisée de vos bases de données.

## 📦 Scripts Disponibles

### 🔧 Script Principal
- **`postgres-backup-manager.cmd`** - Interface centralisée pour tous les outils

### 💾 Scripts de Sauvegarde
- **`backup-postgres-volume.cmd`** - Création de sauvegardes manuelles
- **`setup-postgres-backup-schedule.cmd`** - Configuration de sauvegardes automatiques

### 🔄 Scripts de Restauration
- **`restore-postgres-volume.cmd`** - Restauration depuis différents types de sauvegarde

### ✅ Scripts de Maintenance
- **`verify-postgres-backups.cmd`** - Vérification de l'intégrité des sauvegardes
- **`cleanup-old-backups.cmd`** - Nettoyage automatique des anciennes sauvegardes

## 🚀 Démarrage Rapide

### 1. Première Sauvegarde
```cmd
# Exécuter une sauvegarde immédiate
postgres-backup-manager.cmd
# Choisir option 1 - Créer une sauvegarde manuelle
```

### 2. Configuration Automatique
```cmd
# Configurer une sauvegarde quotidienne
setup-postgres-backup-schedule.cmd
# Choisir l'heure souhaitée (recommandé: 02:00)
```

### 3. Vérification
```cmd
# Vérifier que tout fonctionne
verify-postgres-backups.cmd
```

## 📊 Types de Sauvegarde

### 🔄 1. Volumes Clonés
- **Format**: `ragalmost-main_postgres_data_backup_YYYYMMDD_HHMMSS`
- **Avantages**: Restauration ultra-rapide, copie exacte
- **Inconvénients**: Utilise plus d'espace disque
- **Usage**: Idéal pour restaurations fréquentes

### 📦 2. Archives TAR.GZ
- **Format**: `postgres_backup_YYYYMMDD_HHMMSS.tar.gz`
- **Avantages**: Compression efficace, portable
- **Inconvénients**: Restauration plus lente
- **Usage**: Archivage long terme

### 📄 3. Dumps SQL
- **Format**: `postgres_dump_YYYYMMDD_HHMMSS.sql`
- **Avantages**: Compatible entre versions, lisible
- **Inconvénients**: Plus lent pour grandes bases
- **Usage**: Migration et compatibilité

## 📁 Structure des Fichiers

```
derinier_version/
├── postgres-backup-manager.cmd           # 🎮 Interface principale
├── backup-postgres-volume.cmd            # 💾 Sauvegarde manuelle
├── restore-postgres-volume.cmd           # 🔄 Restauration
├── verify-postgres-backups.cmd           # ✅ Vérification
├── setup-postgres-backup-schedule.cmd    # ⏰ Planification
├── cleanup-old-backups.cmd               # 🧹 Nettoyage
├── README-PostgreSQL-Backup.md           # 📖 Cette documentation
└── backups/
    └── postgres/
        ├── postgres_backup_*.tar.gz      # Archives
        ├── postgres_dump_*.sql           # Dumps SQL
        └── scheduled_backup.log          # Logs automatiques
```

## 🛠️ Utilisation Détaillée

### Sauvegarde Manuelle
```cmd
# Méthode 1: Via le gestionnaire
postgres-backup-manager.cmd

# Méthode 2: Directe
backup-postgres-volume.cmd
```

### Restauration d'Urgence
```cmd
# Si les conteneurs sont supprimés
restore-postgres-volume.cmd
# Choisir le type de sauvegarde à restaurer
```

### Planification Automatique
```cmd
# Configuration d'une tâche Windows
setup-postgres-backup-schedule.cmd
# Choisir: Quotidienne (recommandé) ou Hebdomadaire
```

## 🔍 Commandes de Vérification

### Vérifier les Sauvegardes
```cmd
# Vérification rapide (existence des fichiers)
verify-postgres-backups.cmd (option 1)

# Vérification complète (test de restauration)
verify-postgres-backups.cmd (option 2)
```

### Vérifier l'État Actuel
```cmd
# Voir tous les volumes PostgreSQL
docker volume ls | findstr postgres

# Voir les conteneurs
docker-compose ps db

# Voir les tâches planifiées
schtasks /Query /TN "*PostgreSQL*"
```

## 🧹 Maintenance

### Nettoyage Automatique
```cmd
# Supprimer les sauvegardes anciennes
cleanup-old-backups.cmd
# Configurer: garder X jours de fichiers et Y volumes
```

### Nettoyage Manuel
```cmd
# Supprimer un volume de sauvegarde spécifique
docker volume rm ragalmost-main_postgres_data_backup_20241201_140000

# Supprimer tous les volumes de sauvegarde
docker volume ls | findstr backup | awk '{print $2}' | xargs docker volume rm
```

## ⚡ Scénarios d'Usage

### 🚨 Restauration d'Urgence
Si vos conteneurs PostgreSQL sont perdus :

1. **Arrêter les services**
   ```cmd
   docker-compose down
   ```

2. **Restaurer depuis la sauvegarde la plus récente**
   ```cmd
   restore-postgres-volume.cmd
   ```

3. **Redémarrer les services**
   ```cmd
   docker-compose up -d
   ```

### 🔄 Migration ou Mise à Jour
Avant une mise à jour majeure :

1. **Créer une sauvegarde de sécurité**
   ```cmd
   backup-postgres-volume.cmd
   ```

2. **Effectuer la mise à jour**

3. **En cas de problème, restaurer**
   ```cmd
   restore-postgres-volume.cmd
   ```

### 📊 Tests et Développement
Pour tester avec des données de production :

1. **Cloner le volume de production**
   ```cmd
   # Le script crée automatiquement un volume cloné
   backup-postgres-volume.cmd
   ```

2. **Utiliser le clone pour les tests**

## ⚙️ Configuration Avancée

### Variables d'Environnement
Les scripts utilisent ces variables depuis `docker-compose.yml` :
- `PG_USER` (défaut: user)
- `PG_PASSWORD` (défaut: password)
- `PG_DB` (défaut: mydb)

### Personnalisation des Sauvegardes
Modifiez ces variables dans les scripts :
```cmd
set ORIGINAL_VOLUME=ragalmost-main_postgres_data
set BACKUP_DIR=./backups/postgres
set DEFAULT_KEEP_DAYS=7
set DEFAULT_KEEP_VOLUMES=5
```

## 🔒 Sécurité

### Bonnes Pratiques
1. **Chiffrement**: Les sauvegardes ne sont pas chiffrées par défaut
2. **Stockage**: Considérez un stockage hors site pour les sauvegardes critiques
3. **Accès**: Limitez l'accès aux scripts de sauvegarde
4. **Tests**: Testez régulièrement vos restaurations

### Amélioration de la Sécurité
```cmd
# Chiffrer une archive (optionnel)
7z a -p postgres_backup_encrypted.7z postgres_backup_*.tar.gz

# Copier vers un stockage externe
robocopy ./backups/postgres E:\BackupsExternes\PostgreSQL /E
```

## 🐛 Résolution de Problèmes

### Problèmes Courants

#### Volume non trouvé
```
ERREUR: Le volume ragalmost-main_postgres_data n'existe pas!
```
**Solution**: Démarrez d'abord PostgreSQL avec `docker-compose up -d db`

#### Espace disque insuffisant
```
ERREUR: No space left on device
```
**Solution**: Exécutez `cleanup-old-backups.cmd` ou libérez de l'espace

#### Tâche planifiée échoue
```
✗ Erreur lors de la création de la tâche planifiée
```
**Solution**: Exécutez le script en tant qu'administrateur

### Commandes de Diagnostic
```cmd
# Vérifier l'espace Docker
docker system df

# Vérifier les logs de sauvegarde planifiée
type .\backups\postgres\scheduled_backup.log

# Tester la connectivité PostgreSQL
docker-compose exec db pg_isready -U user -d mydb
```

## 📈 Monitoring

### Logs de Sauvegarde
Les sauvegardes automatiques créent des logs dans :
```
./backups/postgres/scheduled_backup.log
```

### Alertes (Optionnel)
Créez un script de vérification pour surveiller :
- Échec des sauvegardes automatiques
- Espace disque faible
- Sauvegardes trop anciennes

## 🚀 Évolutions Futures

### Fonctionnalités Prévues
- [ ] Chiffrement automatique des sauvegardes
- [ ] Envoi vers stockage cloud (AWS S3, Google Drive)
- [ ] Interface web pour la gestion
- [ ] Notifications par email en cas d'échec
- [ ] Sauvegarde incrémentielle

### Contributions
Pour améliorer ce système :
1. Forkez le projet
2. Créez une branche feature
3. Testez vos modifications
4. Soumettez une pull request

## 📞 Support

### En cas de problème
1. Consultez cette documentation
2. Vérifiez les logs d'erreur
3. Testez les commandes Docker manuellement
4. Contactez l'équipe de développement

### Ressources Utiles
- [Documentation Docker Volumes](https://docs.docker.com/storage/volumes/)
- [PostgreSQL Backup & Restore](https://www.postgresql.org/docs/current/backup.html)
- [Planificateur de tâches Windows](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)

---

📝 **Note**: Ce système est conçu spécifiquement pour le projet RAG-Almost et ses configurations Docker. Adaptez les scripts selon vos besoins spécifiques.

🔄 **Dernière mise à jour**: Décembre 2024 