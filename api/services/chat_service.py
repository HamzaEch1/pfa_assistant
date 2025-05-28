import logging
import pandas as pd
import uuid
import os
import time
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient, models as qdrant_models
from sentence_transformers import SentenceTransformer

from ..core.config import settings

logger = logging.getLogger(__name__)

class FileProcessingError(Exception):
    """Exception raised for errors during file processing."""
    pass

class FileContextRetrievalError(Exception):
    """Exception raised for errors during retrieval of file context."""
    pass

async def process_excel_for_conversation(
    file_path: str,
    file_id: str,
    conversation_id: str,
    user_id: int,
    embedding_model: SentenceTransformer,
    qdrant_client: QdrantClient
) -> bool:
    """
    Process an Excel file for a conversation, creating embeddings for each row
    and storing them in a custom collection for user-uploaded files.
    """
    start_time = time.time()
    logger.info(f"Processing file {file_path} for conversation {conversation_id}")
    
    collection_name = f"user_files_{settings.QDRANT_COLLECTION_NAME}"
    
    try:
        # Ensure the collection exists
        try:
            collection_info = qdrant_client.get_collection(collection_name=collection_name)
            logger.info(f"Collection {collection_name} exists")
        except Exception:
            # Create collection if it doesn't exist
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=embedding_model.get_sentence_embedding_dimension(),
                    distance=qdrant_models.Distance.COSINE
                )
            )
            logger.info(f"Created new collection {collection_name}")
        
        # Read Excel file
        excel_data = pd.ExcelFile(file_path)
        all_sheets_data = {sheet: excel_data.parse(sheet) for sheet in excel_data.sheet_names}
        
        texts_to_embed = []
        metadata_list = []
        
        for sheet_name, df in all_sheets_data.items():
            df = df.fillna('').astype(str)  # Ensure all data is string
            
            # Process each row
            for index, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Create text from row data
                text_chunk = _create_text_chunk(row_dict, sheet_name)
                
                if text_chunk:
                    texts_to_embed.append(text_chunk)
                    metadata = {
                        "source_sheet": sheet_name,
                        "source_file": os.path.basename(file_path),
                        "file_id": file_id,
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "original_row_index": index,
                        "text": text_chunk,
                        "original_data": row_dict
                    }
                    metadata_list.append(metadata)
        
        if not texts_to_embed:
            logger.warning(f"No processable text found in file {file_path}")
            return False
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts_to_embed)} points from file {file_path}")
        embeddings = embedding_model.encode(texts_to_embed, show_progress_bar=False)
        
        # Prepare points for Qdrant
        points_to_upsert = [
            qdrant_models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i].tolist(),
                payload=metadata_list[i]
            ) for i in range(len(embeddings))
        ]
        
        # Upsert to Qdrant
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points_to_upsert,
            wait=True
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully processed {len(points_to_upsert)} points from file {file_path} in {elapsed_time:.2f}s")
        return True
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
        raise FileProcessingError(f"Failed to process file: {str(e)}")


def get_file_context(
    file_id: str,
    query: str,
    embedding_model: SentenceTransformer,
    qdrant_client: QdrantClient,
    limit: int = 5
) -> Optional[str]:
    """
    Retrieve relevant context from a file based on the query.
    """
    collection_name = f"user_files_{settings.QDRANT_COLLECTION_NAME}"
    
    try:
        # Create embedding for query
        query_embedding = embedding_model.encode(query).tolist()
        
        # Search for relevant context
        search_results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="file_id",
                        match=qdrant_models.MatchValue(value=file_id)
                    )
                ]
            ),
            limit=limit
        )
        
        if not search_results:
            logger.warning(f"No results found for query on file {file_id}")
            return None
        
        # Format context from search results
        context_parts = []
        
        for hit in search_results:
            payload = hit.payload
            sheet_name = payload.get("source_sheet", "Unknown")
            row_data = payload.get("original_data", {})
            
            # Format as a table-like structure
            context_part = f"From sheet '{sheet_name}':\n"
            for key, value in row_data.items():
                context_part += f"{key}: {value}\n"
            
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        return context
    
    except Exception as e:
        logger.error(f"Error retrieving context from file {file_id}: {e}", exc_info=True)
        raise FileContextRetrievalError(f"Failed to get context from file: {str(e)}")


def _create_text_chunk(row_dict: dict, sheet_name: str) -> str:
    """
    Create a text representation of a row from an Excel sheet.
    """
    text_chunk = f"Sheet: {sheet_name}\n"
    
    for key, value in row_dict.items():
        if value and str(value).strip():
            text_chunk += f"{key}: {value}\n"
    
    return text_chunk.strip() 