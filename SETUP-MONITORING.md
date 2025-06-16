# 📊 Configuration Monitoring Docker avec Elasticsearch, Kibana et Metricbeat

## 🎯 Objectif
Stack de monitoring complet pour visualiser les métriques des conteneurs Docker et du système avec Kibana.

## 📁 Structure des fichiers nécessaires

```
derinier_version/
├── docker-compose.yml              # Configuration principale
├── Dockerfile.metricbeat           # Image Metricbeat personnalisée
├── metricbeat/
│   └── metricbeat.yml              # Configuration Metricbeat (index classiques)
├── elasticsearch/
│   └── init-dataviews.sh           # Script d'initialisation Kibana
├── restart-metricbeat.cmd          # Script de redémarrage Windows
├── diagnose-metricbeat.ps1         # Script de diagnostic
├── fix-docker-module.ps1           # Script de correction
└── SETUP-MONITORING.md             # Ce guide

```

## 🚀 Installation rapide

### 1. Cloner/Copier les fichiers de configuration

Tous les fichiers de configuration sont déjà dans le projet. Assurez-vous d'avoir :
- `docker-compose.yml` avec les services Elasticsearch, Kibana, Metricbeat
- `Dockerfile.metricbeat` pour la construction personnalisée
- `metricbeat/metricbeat.yml` avec configuration index classiques
- `elasticsearch/init-dataviews.sh` pour l'initialisation Kibana

### 2. Lancer le stack complet

```bash
docker-compose up -d
```

### 3. Vérifier que tout fonctionne

Après 2-3 minutes :
- **Elasticsearch** : http://localhost:9200/_cluster/health
- **Kibana** : http://localhost:5601
- **Données Metricbeat** : http://localhost:9200/metricbeat-*/_count

### 4. Créer le dataview dans Kibana

1. Aller dans **Kibana** : http://localhost:5601
2. **Menu ☰ > Management > Stack Management > Data Views**
3. **Create data view** :
   - **Name** : `Container Monitoring`
   - **Index pattern** : `metricbeat-*`
   - **Time field** : `@timestamp`
4. **Cliquer sur "Create data view"**

## 🔧 Résolution des problèmes

### Problème : Pas de métriques Docker

Si vous ne voyez que les métriques système mais pas `docker.container.name` :

**Windows :**
```cmd
restart-metricbeat.cmd
```

**Linux/Mac :**
```bash
docker-compose restart metricbeat
```

### Diagnostic complet

**Windows :**
```powershell
.\diagnose-metricbeat.ps1
```

**Vérification manuelle :**
```bash
# Vérifier les logs
docker logs metricbeat --tail 20

# Compter les documents Docker
curl -X POST "http://localhost:9200/metricbeat-*/_count" \
  -H "Content-Type: application/json" \
  -d '{"query":{"exists":{"field":"docker"}}}'
```

## 📊 Champs disponibles pour visualisations

### Métriques Système
- `system.cpu.total.pct` - CPU système (%)
- `system.memory.used.pct` - Mémoire utilisée (%)
- `system.load.1` - Charge système (1min)
- `system.network.in.bytes` - Trafic réseau entrant
- `system.network.out.bytes` - Trafic réseau sortant

### Métriques Docker
- `docker.container.name` - Nom du conteneur
- `docker.container.id` - ID du conteneur
- `docker.cpu.total.pct` - CPU conteneur (%)
- `docker.memory.usage.pct` - Mémoire conteneur (%)
- `docker.network.in.bytes` - Réseau conteneur entrant
- `docker.network.out.bytes` - Réseau conteneur sortant

### Champs communs
- `@timestamp` - Timestamp des métriques
- `host.name` - Nom de l'hôte
- `agent.name` - Agent de collecte

## 🎨 Exemples de visualisations

### 1. CPU par conteneur (Lens)
- **Type** : Bar chart
- **X-axis** : `docker.container.name` (Top values)
- **Y-axis** : `docker.cpu.total.pct` (Average)

### 2. Mémoire au fil du temps (Lens)
- **Type** : Line chart
- **X-axis** : `@timestamp` (Date histogram)
- **Y-axis** : `docker.memory.usage.pct` (Average)
- **Split series** : `docker.container.name`

### 3. Trafic réseau (Lens)
- **Type** : Area chart
- **X-axis** : `@timestamp` (Date histogram)
- **Y-axis** : `docker.network.in.bytes` + `docker.network.out.bytes` (Sum)
- **Split series** : `docker.container.name`

## ⚙️ Configuration technique détaillée

### Points clés de la configuration

1. **Index classiques au lieu de data streams** pour éviter les conflits
2. **Permissions Docker socket** correctement configurées
3. **Template Elasticsearch** désactivé pour éviter les conflits
4. **Modules Docker et System** activés automatiquement
5. **Logging détaillé** pour diagnostic

### Variables d'environnement importantes

```yaml
ELASTICSEARCH_HOSTS: http://elasticsearch:9200
KIBANA_HOSTS: http://kibana:5601
XPACK_MONITORING_ENABLED: true
```

### Volumes Docker critiques

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro  # Accès Docker
  - /sys/fs/cgroup:/hostfs/sys/fs/cgroup:ro        # Métriques système
  - /proc:/hostfs/proc:ro                          # Métriques processus
  - /:/hostfs:ro                                   # Métriques filesystem
```

## 🔍 Troubleshooting avancé

### Cas 1: Elasticsearch refuse les connections
```bash
# Vérifier le status
curl http://localhost:9200/_cluster/health

# Redémarrer si nécessaire
docker-compose restart elasticsearch
```

### Cas 2: Metricbeat ne démarre pas
```bash
# Vérifier les logs
docker logs metricbeat

# Reconstruire l'image
docker-compose build --no-cache metricbeat
docker-compose up -d metricbeat
```

### Cas 3: Pas de données dans Kibana
1. Vérifier que l'index existe : `http://localhost:9200/_cat/indices`
2. Rafraîchir le dataview dans Kibana (bouton 🔄)
3. Ajuster la période de temps (dernières 24h)

## 📝 Notes importantes

- **Temps d'initialisation** : Comptez 2-3 minutes après `docker-compose up`
- **Période de rétention** : Les index sont créés par jour (`metricbeat-YYYY.MM.DD`)
- **Performance** : Metricbeat collecte toutes les 10 secondes
- **Stockage** : Environ 100MB/jour pour 5-10 conteneurs

## ✅ Checklist de déploiement

- [ ] Tous les fichiers de configuration présents
- [ ] Docker et docker-compose installés
- [ ] Ports libres : 9200 (Elasticsearch), 5601 (Kibana)
- [ ] `docker-compose up -d` exécuté
- [ ] Attendre 2-3 minutes
- [ ] Vérifier Elasticsearch : http://localhost:9200
- [ ] Vérifier Kibana : http://localhost:5601
- [ ] Créer dataview `metricbeat-*`
- [ ] Vérifier présence de `docker.container.name`

---

**🎯 Avec cette configuration, vous devriez avoir un monitoring complet opérationnel en moins de 5 minutes !** 