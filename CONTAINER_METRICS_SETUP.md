# Guide de Configuration des Métriques de Conteneurs

## 🔧 Problèmes identifiés et résolus

### Problèmes précédents :
1. **Configuration incohérente de Metricbeat** - Les fichiers de configuration avaient des index patterns différents
2. **Variables d'environnement manquantes** - Elasticsearch et Kibana hosts non configurés
3. **Setup automatique désactivé** - Les dashboards et dataviews ne se créaient pas automatiquement
4. **Dépendances incorrectes** - Metricbeat ne dépendait pas de Kibana

### Solutions appliquées :
✅ Configuration unifiée de Metricbeat  
✅ Variables d'environnement ajoutées  
✅ Setup automatique des dashboards activé  
✅ Script d'initialisation des dataviews créé  
✅ Dépendances corrigées dans docker-compose  

## 🚀 Démarrage du système

### 1. Arrêter les services existants
```bash
docker-compose down -v
```

### 2. Nettoyer les volumes (optionnel)
```bash
docker volume prune -f
```

### 3. Démarrer les services
```bash
docker-compose up -d
```

### 4. Vérifier le statut des services
```bash
docker-compose ps
```

## 📊 Accès aux services

- **Kibana Dashboard** : http://localhost:5601
- **Elasticsearch** : http://localhost:9200
- **Application Frontend** : http://localhost:3000
- **API Backend** : http://localhost:8000

## 🔍 Vérification des métriques

### 1. Vérifier que Metricbeat collecte les données
```bash
curl "http://localhost:9200/metricbeat-8.12.1-*/_search?size=5&sort=@timestamp:desc"
```

### 2. Vérifier les index dans Elasticsearch
```bash
curl "http://localhost:9200/_cat/indices/metricbeat*?v"
```

### 3. Accéder aux dataviews dans Kibana
1. Ouvrir Kibana : http://localhost:5601
2. Aller dans **Analytics > Data Views**
3. Vous devriez voir :
   - `Metricbeat Metrics`
   - `Docker Container Metrics`

## 📈 Création de visualisations

### 1. Métriques de CPU des conteneurs
- Aller dans **Analytics > Visualizations**
- Créer une nouvelle visualisation
- Sélectionner le dataview `Docker Container Metrics`
- Filtrer sur `docker.container.cpu.total.pct`

### 2. Métriques de mémoire des conteneurs
- Utiliser le champ `docker.container.memory.usage.pct`
- Grouper par `container.name`

### 3. Métriques réseau des conteneurs
- Utiliser les champs `docker.container.network.in.bytes` et `docker.container.network.out.bytes`

## 🔧 Résolution de problèmes

### Si les dataviews ne se créent pas automatiquement :

1. **Exécuter manuellement le script d'initialisation**
```bash
docker run --rm --network derinier_version_rag_network \
  -v $(pwd)/elasticsearch/init-dataviews.sh:/init-dataviews.sh:ro \
  -e ELASTICSEARCH_URL=http://elasticsearch:9200 \
  -e KIBANA_URL=http://kibana:5601 \
  curlimages/curl:latest /bin/sh /init-dataviews.sh
```

2. **Vérifier les logs de Metricbeat**
```bash
docker logs metricbeat
```

3. **Vérifier les logs de Kibana**
```bash
docker logs kibana
```

### Si Metricbeat ne collecte pas les métriques Docker :

1. **Vérifier les permissions Docker socket**
```bash
docker exec metricbeat ls -la /var/run/docker.sock
```

2. **Redémarrer Metricbeat**
```bash
docker-compose restart metricbeat
```

## 📋 Checklist de vérification

- [ ] Elasticsearch est accessible sur port 9200
- [ ] Kibana est accessible sur port 5601
- [ ] Metricbeat collecte les métriques (vérifier les logs)
- [ ] Les index `metricbeat-8.12.1-*` existent dans Elasticsearch
- [ ] Les dataviews sont créés dans Kibana
- [ ] Les métriques Docker sont visibles dans Kibana

## 🔗 Champs de métriques Docker disponibles

### Métriques de conteneur :
- `docker.container.cpu.total.pct` - Pourcentage CPU
- `docker.container.memory.usage.pct` - Pourcentage mémoire
- `docker.container.memory.usage.total` - Utilisation mémoire totale
- `docker.container.network.in.bytes` - Trafic réseau entrant
- `docker.container.network.out.bytes` - Trafic réseau sortant
- `docker.container.diskio.read.bytes` - Lecture disque
- `docker.container.diskio.write.bytes` - Écriture disque

### Métadonnées :
- `container.name` - Nom du conteneur
- `container.image.name` - Nom de l'image
- `docker.container.status` - Statut du conteneur

## 🎯 Suggestions d'amélioration

1. **Alertes** : Configurer des alertes pour l'utilisation excessive des ressources
2. **Retention** : Configurer ILM pour la gestion du cycle de vie des index
3. **Sécurité** : Activer l'authentification pour Elasticsearch et Kibana
4. **Monitoring** : Ajouter des métriques sur l'état de santé des services 