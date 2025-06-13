#!/bin/bash

# Script d'initialisation des dataviews pour les métriques de conteneurs
set -e

ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://elasticsearch:9200}"
KIBANA_URL="${KIBANA_URL:-http://kibana:5601}"

echo "🔄 Attente de la disponibilité d'Elasticsearch..."
until curl -s "$ELASTICSEARCH_URL/_cluster/health" > /dev/null; do
    echo "En attente d'Elasticsearch..."
    sleep 5
done

echo "🔄 Attente de la disponibilité de Kibana..."
until curl -s "$KIBANA_URL/api/status" > /dev/null; do
    echo "En attente de Kibana..."
    sleep 5
done

echo "✅ Elasticsearch et Kibana sont disponibles"

# Créer l'index pattern pour Metricbeat
echo "📊 Création de l'index pattern Metricbeat..."
curl -X POST "$KIBANA_URL/api/data_views/data_view" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    -d '{
        "data_view": {
            "title": "metricbeat-*",
            "name": "Metricbeat Metrics",
            "timeFieldName": "@timestamp"
        }
    }' || echo "Index pattern peut déjà exister"

# Créer l'index pattern spécifique pour les métriques Docker
echo "🐳 Création de l'index pattern pour les métriques Docker..."
curl -X POST "$KIBANA_URL/api/data_views/data_view" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    -d '{
        "data_view": {
            "title": "metricbeat-*",
            "name": "Docker Container Metrics",
            "timeFieldName": "@timestamp",
            "sourceFilters": [
                {
                    "value": "docker.*"
                }
            ]
        }
    }' || echo "Index pattern Docker peut déjà exister"

# Attendre quelques secondes pour que les index patterns soient créés
sleep 10

# Créer un dashboard basique pour les métriques de conteneurs
echo "📈 Création d'un dashboard basique pour les métriques de conteneurs..."
curl -X POST "$KIBANA_URL/api/saved_objects/dashboard" \
    -H "Content-Type: application/json" \
    -H "kbn-xsrf: true" \
    -d '{
        "attributes": {
            "title": "Container Metrics Dashboard",
            "description": "Dashboard pour visualiser les métriques des conteneurs Docker",
            "panelsJSON": "[]",
            "timeRestore": false,
            "timeTo": "now",
            "timeFrom": "now-15m",
            "refreshInterval": {
                "pause": false,
                "value": 10000
            },
            "version": 1
        }
    }' || echo "Dashboard peut déjà exister"

echo "✅ Initialisation des dataviews terminée!"
echo "🌐 Accédez à Kibana sur: $KIBANA_URL"
echo "📊 Vos dataviews sont maintenant disponibles dans Kibana > Analytics > Data Views" 