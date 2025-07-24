# Apache Atlas Data Catalog Setup

This directory contains a complete Apache Atlas setup using the Sburn version with Docker, plus scripts to populate Atlas with data from Excel catalogs and synchronize it to Qdrant for vector search.

## 📁 Directory Structure

```
apache-atlas/
├── docker-compose.yml              # Atlas stack with dependencies
├── Dockerfile.scripts              # Python environment for scripts
├── requirements.txt                 # Python dependencies
├── data/
│   └── catalogue_donnees_bancaires_modifie.xlsx  # Excel catalog data
├── scripts/
│   ├── populate_atlas_from_excel.py # Script 1: Excel → Atlas
│   └── sync_atlas_to_qdrant.py     # Script 2: Atlas → Qdrant
├── run_populate_atlas.sh           # Convenience script for Excel → Atlas
├── run_sync_to_qdrant.sh           # Convenience script for Atlas → Qdrant
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Start Apache Atlas

```bash
# Start the complete Atlas stack
docker-compose up -d

# Wait for services to be ready (this takes 3-5 minutes)
docker-compose logs -f atlas

# Check when Atlas is ready
curl http://localhost:21000/api/atlas/admin/version
```

### 2. Populate Atlas from Excel Catalog

```bash
# Run the population script
./run_populate_atlas.sh

# Or manually:
docker build -f Dockerfile.scripts -t atlas-scripts .
docker run --rm --network apache-atlas_atlas-network \
  -e ATLAS_URL=http://atlas:21000 \
  atlas-scripts python scripts/populate_atlas_from_excel.py
```

### 3. Synchronize Atlas Data to Qdrant

```bash
# Make sure your main project's Qdrant is running on port 6333
# Then run the sync script
./run_sync_to_qdrant.sh

# Or manually:
docker run --rm --network host \
  -e ATLAS_URL=http://localhost:21000 \
  -e QDRANT_URL=http://localhost:6333 \
  -e QDRANT_COLLECTION_NAME=atlas_catalog \
  atlas-scripts python scripts/sync_atlas_to_qdrant.py
```

## 🔧 Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| **Apache Atlas** | 21000 | Main Atlas UI and API |
| **Kafka** | 9092 | Message broker for Atlas |
| **Zookeeper** | 2181 | Coordination service |
| **Elasticsearch** | 9200/9300 | Search backend for Atlas |

## 📊 Script Details

### Script 1: `populate_atlas_from_excel.py`

**Purpose**: Reads the Excel catalog file and creates Atlas entities for data governance.

**What it does**:
- Reads all sheets from `catalogue_donnees_bancaires_modifie.xlsx`
- Creates Atlas entities:
  - **DataSet** entities from "Référentiel Sources" sheet
  - **AtlasGlossaryTerm** entities from "Glossaire Métier" sheet  
  - **Column** entities from "Réf technique" sheet
  - **Process** entities from "Référentiel Flux" sheet
- Uses Atlas REST API to bulk-create entities
- Handles relationships and custom attributes

**Excel Sheet Mapping**:
```
Référentiel Sources → DataSet entities (data sources)
Glossaire Métier    → AtlasGlossaryTerm entities (business terms)
Réf technique       → Column entities (technical fields)
Référentiel Flux    → Process entities (data flows)
```

### Script 2: `sync_atlas_to_qdrant.py`

**Purpose**: Extracts data from Atlas and creates vector embeddings in Qdrant for semantic search.

**What it does**:
- Fetches all entities from Atlas using REST API
- Converts each entity to searchable text representation
- Generates embeddings using SentenceTransformers
- Creates Qdrant collection `atlas_catalog`
- Stores vectors with full metadata for search

**Entity Text Conversion**:
- Combines entity attributes into meaningful text
- Includes custom attributes as searchable fields
- Preserves metadata for result display
- Uses multilingual embedding model for French content

## 🔐 Access Information

### Apache Atlas
- **URL**: http://localhost:21000
- **Username**: `admin`
- **Password**: `admin`

### Default Configuration
- **Qdrant Collection**: `atlas_catalog`
- **Embedding Model**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Vector Dimension**: 384

## 🛠️ Manual Operations

### Check Atlas Status
```bash
curl http://localhost:21000/api/atlas/admin/version
```

### List Atlas Entities
```bash
curl -u admin:admin http://localhost:21000/api/atlas/v2/search/basic?typeName=DataSet
```

### Check Qdrant Collection
```bash
curl http://localhost:6333/collections/atlas_catalog
```

### Query Qdrant
```bash
curl -X POST http://localhost:6333/collections/atlas_catalog/points/search \
  -H "Content-Type: application/json" \
  -d '{"vector": [...], "limit": 5}'
```

## 🐛 Troubleshooting

### Atlas Not Starting
- Increase Docker memory allocation (recommend 4GB+)
- Wait longer - Atlas takes 3-5 minutes to fully start
- Check logs: `docker-compose logs atlas`

### Script Dependencies
```bash
# Install Python dependencies locally
pip install -r requirements.txt

# Run scripts locally
python scripts/populate_atlas_from_excel.py
python scripts/sync_atlas_to_qdrant.py
```

### Qdrant Connection Issues
- Ensure your main project's Qdrant is running on port 6333
- Or start standalone Qdrant: `docker run -p 6333:6333 qdrant/qdrant`

### Network Issues
- Atlas container uses network `apache-atlas_atlas-network`
- Sync script uses `--network host` to access external Qdrant

## 📈 Monitoring

### Atlas Health Check
```bash
curl http://localhost:21000/api/atlas/admin/status
```

### View Created Entities
Navigate to Atlas UI → Search → Advanced Search

### Qdrant Dashboard
Visit: http://localhost:6333/dashboard

## 🔄 Data Flow

```
Excel Catalog → Atlas Entities → Qdrant Vectors → Semantic Search
     ↓              ↓                ↓               ↓
1. Excel sheets  2. DataSets     3. Embeddings   4. Query results
   Business terms   Glossary        Metadata        Rich context
   Technical refs   Columns         Relationships   Data lineage
   Data flows       Processes       Custom attrs    Business meaning
```

## 🎯 Integration with Main Project

The Qdrant collection `atlas_catalog` created by these scripts can be integrated into your main RAG application by:

1. **Updating your search service** to query the `atlas_catalog` collection
2. **Modifying your chat interface** to include Atlas entity results
3. **Adding data lineage visualization** from Atlas relationships
4. **Implementing governance workflows** using Atlas APIs

## 📝 Notes

- This Atlas instance is **separate** from your main project
- Data flows: Excel → Atlas → Qdrant (one-way sync)
- Atlas provides **data governance** features (lineage, classification, etc.)
- Qdrant provides **semantic search** capabilities for the chat interface
- Both systems can coexist and complement each other 