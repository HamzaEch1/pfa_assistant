#!/usr/bin/env python3
"""
Script to extract data from Apache Atlas and populate it into Qdrant database.
This script fetches all entities from Atlas and creates vector embeddings for semantic search.
"""

import json
import requests
import uuid
from typing import Dict, List, Any, Optional
import logging
import time
from requests.auth import HTTPBasicAuth
import sys
import os

# Import required libraries for Qdrant and embeddings
try:
    from qdrant_client import QdrantClient, models as qdrant_models
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logging.error(f"Required libraries not installed: {e}")
    logging.error("Please install: pip install qdrant-client sentence-transformers")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtlasToQdrantSyncer:
    def __init__(
        self, 
        atlas_url: str = "http://localhost:21000",
        qdrant_url: str = "http://localhost:6333",
        atlas_username: str = "admin",
        atlas_password: str = "admin",
        collection_name: str = "atlas_catalog",
        embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        # Atlas configuration
        self.atlas_url = atlas_url
        self.atlas_auth = HTTPBasicAuth(atlas_username, atlas_password)
        self.atlas_session = requests.Session()
        self.atlas_session.auth = self.atlas_auth
        self.atlas_session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Qdrant configuration
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        
        # Embedding model
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        logger.info("Embedding model loaded successfully")

    def wait_for_atlas(self, max_retries: int = 30) -> bool:
        """Wait for Atlas to be ready"""
        logger.info("Waiting for Atlas to be ready...")
        for i in range(max_retries):
            try:
                response = self.atlas_session.get(f"{self.atlas_url}/api/atlas/admin/version")
                if response.status_code == 200:
                    logger.info("Atlas is ready!")
                    return True
            except Exception as e:
                logger.info(f"Atlas not ready yet (attempt {i+1}/{max_retries}): {e}")
                time.sleep(10)
        logger.error("Atlas failed to become ready")
        return False

    def setup_qdrant_collection(self) -> bool:
        """Setup Qdrant collection for Atlas data"""
        try:
            # Check if collection exists
            try:
                collection_info = self.qdrant_client.get_collection(collection_name=self.collection_name)
                logger.info(f"Collection {self.collection_name} already exists")
                return True
            except Exception:
                # Collection doesn't exist, create it
                vector_size = self.embedding_model.get_sentence_embedding_dimension()
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=vector_size,
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name} with vector size: {vector_size}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting up Qdrant collection: {e}")
            return False

    def get_all_atlas_entities(self) -> List[Dict[str, Any]]:
        """Fetch all entities from Atlas"""
        entities = []
        
        # Get all entity types first
        entity_types = ["DataSet", "AtlasGlossaryTerm", "Column", "Process"]
        
        for entity_type in entity_types:
            try:
                logger.info(f"Fetching {entity_type} entities from Atlas...")
                
                # Use search API to get entities by type
                search_params = {
                    "typeName": entity_type,
                    "excludeDeletedEntities": True,
                    "limit": 1000,
                    "offset": 0
                }
                
                response = self.atlas_session.get(
                    f"{self.atlas_url}/api/atlas/v2/search/basic",
                    params=search_params
                )
                
                if response.status_code == 200:
                    result = response.json()
                    entity_headers = result.get("entities", [])
                    
                    # For each entity header, get the full entity details
                    for entity_header in entity_headers:
                        guid = entity_header.get("guid")
                        if guid:
                            entity_detail = self.get_entity_by_guid(guid)
                            if entity_detail:
                                entities.append(entity_detail)
                    
                    logger.info(f"Found {len(entity_headers)} {entity_type} entities")
                else:
                    logger.warning(f"Failed to fetch {entity_type} entities: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error fetching {entity_type} entities: {e}")
        
        logger.info(f"Total entities fetched from Atlas: {len(entities)}")
        return entities

    def get_entity_by_guid(self, guid: str) -> Optional[Dict[str, Any]]:
        """Get full entity details by GUID"""
        try:
            response = self.atlas_session.get(f"{self.atlas_url}/api/atlas/v2/entity/guid/{guid}")
            if response.status_code == 200:
                return response.json().get("entity", {})
            else:
                logger.warning(f"Failed to get entity {guid}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting entity {guid}: {e}")
            return None

    def entity_to_text(self, entity: Dict[str, Any]) -> str:
        """Convert Atlas entity to searchable text"""
        attributes = entity.get("attributes", {})
        custom_attributes = entity.get("customAttributes", {})
        type_name = entity.get("typeName", "")
        
        # Build text representation based on entity type
        text_parts = []
        
        # Basic information
        name = attributes.get("name", "")
        description = attributes.get("description", "")
        qualified_name = attributes.get("qualifiedName", "")
        
        text_parts.append(f"Type: {type_name}")
        if name:
            text_parts.append(f"Name: {name}")
        if description:
            text_parts.append(f"Description: {description}")
        if qualified_name:
            text_parts.append(f"Qualified Name: {qualified_name}")
        
        # Type-specific attributes
        if type_name == "DataSet":
            owner = attributes.get("owner", "")
            if owner:
                text_parts.append(f"Owner: {owner}")
                
        elif type_name == "AtlasGlossaryTerm":
            short_desc = attributes.get("shortDescription", "")
            long_desc = attributes.get("longDescription", "")
            usage = attributes.get("usage", "")
            if short_desc:
                text_parts.append(f"Short Description: {short_desc}")
            if long_desc:
                text_parts.append(f"Long Description: {long_desc}")
            if usage:
                text_parts.append(f"Usage: {usage}")
                
        elif type_name == "Column":
            col_type = attributes.get("type", "")
            length = attributes.get("length", "")
            is_nullable = attributes.get("isNullable", "")
            comment = attributes.get("comment", "")
            if col_type:
                text_parts.append(f"Type: {col_type}")
            if length:
                text_parts.append(f"Length: {length}")
            if comment:
                text_parts.append(f"Comment: {comment}")
                
        elif type_name == "Process":
            owner = attributes.get("owner", "")
            if owner:
                text_parts.append(f"Owner: {owner}")
        
        # Add custom attributes
        for key, value in custom_attributes.items():
            if value and str(value).strip():
                text_parts.append(f"{key}: {value}")
        
        return ". ".join(text_parts)

    def create_qdrant_point(self, entity: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Create a Qdrant point from Atlas entity"""
        guid = entity.get("guid", str(uuid.uuid4()))
        attributes = entity.get("attributes", {})
        custom_attributes = entity.get("customAttributes", {})
        
        # Create metadata payload
        metadata = {
            "guid": guid,
            "typeName": entity.get("typeName", ""),
            "name": attributes.get("name", ""),
            "qualifiedName": attributes.get("qualifiedName", ""),
            "description": attributes.get("description", ""),
            "text": text,
            "source": "apache_atlas",
            "createTime": attributes.get("createTime", int(time.time() * 1000)),
            "updateTime": attributes.get("updateTime", int(time.time() * 1000))
        }
        
        # Add all custom attributes to metadata
        for key, value in custom_attributes.items():
            metadata[f"custom_{key}"] = str(value) if value else ""
        
        return {
            "id": guid,
            "text": text,
            "metadata": metadata
        }

    def sync_to_qdrant(self, entities: List[Dict[str, Any]]) -> bool:
        """Sync Atlas entities to Qdrant"""
        try:
            points_to_create = []
            texts_to_embed = []
            
            logger.info("Converting Atlas entities to Qdrant points...")
            
            for entity in entities:
                # Convert entity to searchable text
                text = self.entity_to_text(entity)
                if text.strip():
                    point_data = self.create_qdrant_point(entity, text)
                    points_to_create.append(point_data)
                    texts_to_embed.append(text)
            
            if not points_to_create:
                logger.warning("No valid entities to sync")
                return True
            
            logger.info(f"Generating embeddings for {len(texts_to_embed)} entities...")
            embeddings = self.embedding_model.encode(texts_to_embed, show_progress_bar=True)
            
            # Create Qdrant points
            logger.info("Creating Qdrant points...")
            qdrant_points = []
            
            for i, point_data in enumerate(points_to_create):
                qdrant_point = qdrant_models.PointStruct(
                    id=point_data["id"],
                    vector=embeddings[i].tolist(),
                    payload=point_data["metadata"]
                )
                qdrant_points.append(qdrant_point)
            
            # Upsert points in batches
            batch_size = 100
            total_points = len(qdrant_points)
            
            for i in range(0, total_points, batch_size):
                batch = qdrant_points[i:i + batch_size]
                logger.info(f"Upserting batch {i//batch_size + 1}/{(total_points + batch_size - 1)//batch_size}")
                
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True
                )
            
            logger.info(f"Successfully synced {total_points} entities to Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing to Qdrant: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection"""
        try:
            collection_info = self.qdrant_client.get_collection(collection_name=self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_config": collection_info.config.params.vectors,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    def run_sync(self) -> bool:
        """Main sync process"""
        logger.info("Starting Atlas to Qdrant synchronization...")
        
        # Wait for Atlas
        if not self.wait_for_atlas():
            return False
        
        # Setup Qdrant collection
        if not self.setup_qdrant_collection():
            return False
        
        # Fetch entities from Atlas
        entities = self.get_all_atlas_entities()
        if not entities:
            logger.warning("No entities found in Atlas")
            return True
        
        # Sync to Qdrant
        success = self.sync_to_qdrant(entities)
        
        if success:
            # Show collection info
            info = self.get_collection_info()
            logger.info(f"Sync completed successfully!")
            logger.info(f"Collection info: {json.dumps(info, indent=2)}")
        
        return success

def main():
    # Configuration
    atlas_url = os.getenv("ATLAS_URL", "http://localhost:21000")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "atlas_catalog")
    
    # Create syncer instance
    syncer = AtlasToQdrantSyncer(
        atlas_url=atlas_url,
        qdrant_url=qdrant_url,
        collection_name=collection_name
    )
    
    # Run synchronization
    success = syncer.run_sync()
    
    if success:
        logger.info("Atlas to Qdrant synchronization completed successfully!")
        logger.info(f"Data is now available in Qdrant collection: {collection_name}")
        logger.info(f"You can query the collection at: {qdrant_url}")
    else:
        logger.error("Synchronization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 