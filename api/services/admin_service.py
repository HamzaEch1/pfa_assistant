# api/services/admin_service.py
import logging
import pandas as pd
import uuid
from fastapi import UploadFile, HTTPException, status
from qdrant_client import QdrantClient, models as qdrant_models
from sentence_transformers import SentenceTransformer
import time
import json

# Relative imports
from ..core.config import settings
from ..schemas.message import Message # If needed for any processing

logger = logging.getLogger(__name__)

# --- Helper function to create text chunks (Copied/Adapted from admin_logic.py) ---
# Note: This is duplicated from the Streamlit version. Consider putting shared logic
# in a common utility module if it grows more complex.
def _create_text_chunk(row_dict: dict, sheet_name: str) -> str:
    """Creates a formatted text string from a dictionary row based on the sheet name."""
    # Row is already a dict of strings here
    text_chunk = ""
    # Use .get(column, default_value) for robustness
    if sheet_name == 'Référentiel Sources':
        text_chunk = (
            f"Source: {row_dict.get('Nom source','N/A')} ({row_dict.get('Type Source','N/A')} sur {row_dict.get('Plateforme source','N/A')}). "
            f"Flux: {row_dict.get('Flux/Scénario SD','N/A')}. "
            f"Domaine: {row_dict.get('Domaine','N/A')} / {row_dict.get('Sous domaine','N/A')}. "
            f"Application source: {row_dict.get('Application Source','N/A')}. "
            f"Cible: {row_dict.get('Plateforme cible','N/A')} ({row_dict.get('Nom cible','N/A')}). "
            f"Chargement: {row_dict.get('Mode chargement','N/A')} ({row_dict.get('Fréquence MAJ','N/A')}) via {row_dict.get('Technologie de chargement(Outil)','N/A')} ({row_dict.get('Technologie','N/A')}). "
            f"Procédure: {row_dict.get('Nom Flux/Procedure','N/A')}. "
            f"Taille: {row_dict.get('Taille Objet','N/A')}. Format: {row_dict.get('Format','N/A')}. "
            f"Description: {row_dict.get('Description','N/A')}. "
            f"Filiale: {row_dict.get('Filiale','N/A')}."
        )
    elif sheet_name == 'Glossaire Métier':
        text_chunk = (
            f"Terme métier: {row_dict.get('Libellé Métier','N/A')}. Propriétaire: {row_dict.get('Propriétaire','N/A')}. "
            f"Description: {row_dict.get('Description','N/A')}. Confidentialité: {row_dict.get('Confidentialité','N/A')}. "
            f"Règle métier: {row_dict.get('Règle métier','N/A')}. "
            f"Criticité: {row_dict.get('Criticité','N/A')}. "
            f"Qualité adressée: {row_dict.get('Aspect de performance adressé (Qualité)','N/A')}. "
            f"Commentaire: {row_dict.get('Commentaire','N/A')}."
        )
    elif sheet_name == 'Réf technique':
        text_chunk = (
            f"Champ technique: {row_dict.get('Libellé champ','N/A')} dans la source {row_dict.get('Nom source','N/A')} (Plateforme: {row_dict.get('Plateforme','N/A')}). "
            f"Type: {row_dict.get('Type','N/A')}({row_dict.get('Taille','N/A')}). Obligatoire: {row_dict.get('Obligatoire','N/A')}. "
            f"Confidentialité: {row_dict.get('Confidentialité','N/A')}. Règle métier: {row_dict.get('Règle métier','N/A')}. "
            f"Libellé métier: {row_dict.get('Libellé Métier','N/A')}. "
            f"Commentaire: {row_dict.get('Commentaire','N/A')}."
        )
    elif sheet_name == 'Référentiel Flux':
        text_chunk = (
            f"Traitement dans Flux: {row_dict.get('Nom Flux','N/A')}. Champ source: {row_dict.get('Nom Champ SD Source','N/A')} (de {row_dict.get('Nom SD Source','N/A')} sur {row_dict.get('Plateforme source','N/A')}). "
            f"Règle: {row_dict.get('Règle de Gestion','N/A')}. Champ cible: {row_dict.get('Nom Champ Cible','N/A')} (vers {row_dict.get('Nom SD Cible','N/A')} sur {row_dict.get('Plateforme cible','N/A')}). "
            f"Confidentialité: {row_dict.get('Confidentialité','N/A')}. Description traitement: {row_dict.get('Description traitement','N/A')}. "
            f"Commentaire: {row_dict.get('Commentaire','N/A')}."
        )
    else:
        chunk_parts = [f"{col}: {val}" for col, val in row_dict.items() if str(val).strip()]
        text_chunk = ". ".join(chunk_parts)

    return text_chunk.replace('\n', ' ').strip()

# --- Main Processing Function for Background Task ---
# Note: Pass clients/models as arguments because this runs in a background thread/process
# and won't have access to the request-scoped dependencies directly.
# Also, avoid using Streamlit functions (st.info etc.) here. Use logging.
def process_and_upsert_excel_task(
    file_content: bytes,
    filename: str,
    qdrant_client: QdrantClient,
    embedding_model: SentenceTransformer
):
    """
    Background task to process Excel data and upsert to Qdrant.
    Uses logging instead of st functions.
    """
    start_time = time.time()
    logger.info(f"[Background Task] Starting processing for file: {filename}")

    # Dependency checks already happened in the main thread via Depends()
    # Add checks here just in case they become None somehow between threads/processes
    if not qdrant_client or not embedding_model:
         logger.error("[Background Task] Qdrant client or embedding model is None. Aborting.")
         return # Cannot proceed

    try:
        # Read Excel data from bytes
        excel_data = pd.ExcelFile(file_content)
        all_sheets_data = {sheet: excel_data.parse(sheet) for sheet in excel_data.sheet_names}
        logger.info(f"[Background Task] File read successfully. Sheets: {list(all_sheets_data.keys())}")
    except Exception as e:
        logger.error(f"[Background Task] Error reading Excel file {filename}: {e}", exc_info=True)
        return

    texts_to_embed = []
    metadata_list = []
    points_processed = 0
    total_rows = sum(len(df) for df in all_sheets_data.values())
    if total_rows == 0:
        logger.warning(f"[Background Task] Excel file {filename} contains no data.")
        return

    prep_start = time.time()
    logger.info(f"[Background Task] Preparing data ({total_rows} total rows)...")
    rows_processed = 0
    for sheet_name, df in all_sheets_data.items():
        df = df.fillna('').astype(str) # Ensure all data is string
        for index, row in df.iterrows():
            rows_processed += 1
            # Convert row to dict for helper function
            row_dict = row.to_dict()
            text_chunk = _create_text_chunk(row_dict, sheet_name)

            if text_chunk:
                texts_to_embed.append(text_chunk)
                metadata = {
                    "source_sheet": sheet_name,
                    "source_file": filename,
                    "original_row_index": index,
                    "text": text_chunk,
                    "original_data": row_dict # Store original row data
                }
                metadata_list.append(metadata)
                points_processed += 1
    prep_end = time.time()
    logger.info(f"[Background Task] Data preparation finished in {prep_end - prep_start:.2f}s. Found {points_processed} valid points.")

    if not texts_to_embed:
        logger.warning(f"[Background Task] No processable text found in {filename}.")
        return

    # Generate Embeddings
    embed_start = time.time()
    logger.info(f"[Background Task] Generating embeddings for {len(texts_to_embed)} points...")
    try:
        embeddings = embedding_model.encode(texts_to_embed, show_progress_bar=False) # No progress bar in background
        embed_end = time.time()
        logger.info(f"[Background Task] Embeddings generated ({len(embeddings)} vectors) in {embed_end - embed_start:.2f}s.")
    except Exception as e:
        logger.error(f"[Background Task] Error generating embeddings for {filename}: {e}", exc_info=True)
        return

    # Prepare points for Qdrant
    points_to_upsert = [
        qdrant_models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embeddings[i].tolist(),
            payload=metadata_list[i]
        ) for i in range(len(embeddings))
    ]

    # Upsert in batches
    upsert_start = time.time()
    logger.info(f"[Background Task] Upserting {len(points_to_upsert)} points to Qdrant collection '{settings.QDRANT_COLLECTION_NAME}'...")
    batch_size = 128
    total_batches = (len(points_to_upsert) - 1) // batch_size + 1
    errors_occurred = False
    batches_processed = 0

    for i in range(0, len(points_to_upsert), batch_size):
        batch = points_to_upsert[i:i + batch_size]
        batch_num = i // batch_size + 1
        try:
            qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points=batch,
                wait=True # Set wait=False for faster background upsert? Depends on consistency needs.
            )
            batches_processed += 1
            logger.debug(f"[Background Task] Upserted batch {batch_num}/{total_batches}")
        except Exception as e:
            logger.error(f"[Background Task] Error during Qdrant upsert (Batch {batch_num}) for {filename}: {e}", exc_info=True)
            errors_occurred = True
            break # Stop on first error

    upsert_end = time.time()
    total_duration = upsert_end - start_time
    if errors_occurred:
        logger.error(f"[Background Task] Upload for {filename} failed after {batches_processed}/{total_batches} batches. Total time: {total_duration:.2f}s.")
    else:
        logger.info(f"[Background Task] Successfully upserted {len(points_to_upsert)} points from {filename} to Qdrant. Total time: {total_duration:.2f}s.")

# Add other admin service logic here if needed (e.g., calling CRUD functions)