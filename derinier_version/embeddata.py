import pandas as pd
import random
import uuid # To generate unique IDs for Qdrant points

# --- Your existing data generation code ---
# (Keep your code from 'import pandas as pd' down to 
# 'print(f"Fichier généré : {excel_path}")' here)
# Ensure the excel_path variable is defined:
bank_name = "BankMA"
excel_path = "catalogue_donnees_bancaires_modifie.xlsx"
# --- End of your existing data generation code ---

# --- New code for Embedding and Qdrant ---
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
import openpyxl # pandas needs this to read xlsx

# --- Configuration ---
# Qdrant Configuration
# Option 1: Run Qdrant locally using Docker (recommended for persistence)
qdrant_url = "http://localhost:6333"
client = QdrantClient(url=qdrant_url)

# Option 2: Run Qdrant in memory (data lost on script exit)
# client = QdrantClient(":memory:")

# Option 3: Run Qdrant with local file persistence
# qdrant_path = "./qdrant_data"
# client = QdrantClient(path=qdrant_path)

qdrant_collection_name = "banque_ma_data_catalog"

# Embedding Model Configuration
# Using a multilingual model as your data is in French.
# Other options: 'all-MiniLM-L6-v2' (faster, smaller, English-focused),
# 'paraphrase-multilingual-mpnet-base-v2' (larger, potentially better multilingual performance)
embedding_model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
print(f"Loading embedding model: {embedding_model_name}...")
model = SentenceTransformer(embedding_model_name)
print("Model loaded.")

# --- Step 1: Read Data from Excel ---
print(f"Reading data from Excel file: {excel_path}...")
try:
    # Read all sheets into a dictionary of DataFrames
    all_sheets_data = pd.read_excel(excel_path, sheet_name=None)
    print(f"Successfully read sheets: {list(all_sheets_data.keys())}")
except FileNotFoundError:
    print(f"Error: Excel file not found at {excel_path}. Please generate it first.")
    exit()
except Exception as e:
    print(f"Error reading Excel file: {e}")
    exit()

# --- Step 2: Prepare Text Chunks and Metadata ---
points_to_upsert = []
texts_to_embed = []
metadata_list = []

print("Preparing data for embedding...")
# Process each sheet
for sheet_name, df in all_sheets_data.items():
    print(f"Processing sheet: {sheet_name} ({len(df)} rows)")
    # Convert NaN to empty strings for safer text processing
    df = df.fillna('')
    
    for index, row in df.iterrows():
        text_chunk = ""
        # Create a meaningful text representation for each row based on the sheet
        if sheet_name == 'Référentiel Sources':
            text_chunk = (
                f"Source: {row['Nom source']} ({row['Type Source']} sur {row['Plateforme source']}). "
                f"Flux: {row['Flux/Scénario SD']}. Domaine: {row['Domaine']} / {row['Sous domaine']}. "
                f"Application source: {row['Application Source']}. "
                f"Cible: {row['Plateforme cible']} ({row['Nom cible']}). "
                f"Chargement: {row['Mode chargement']} ({row['Fréquence MAJ']}) via {row['Technologie de chargement(Outil)']} ({row['Technologie']}). "
                f"Procédure: {row['Nom Flux/Procedure']}. Taille: {row['Taille Objet']}. Format: {row['Format']}. "
                f"Description: {row['Description']}. Filiale: {row['Filiale']}."
            )
        elif sheet_name == 'Glossaire Métier':
            text_chunk = (
                f"Terme métier: {row['Libellé Métier']}. Propriétaire: {row['Propriétaire']}. "
                f"Description: {row['Description']}. Confidentialité: {row['Confidentialité']}. "
                f"Règle métier: {row['Règle métier']}. Criticité: {row['Criticité']}. "
                f"Qualité adressée: {row['Aspect de performance adressé (Qualité)']}. "
                f"Commentaire: {row['Commentaire']}."
            )
        elif sheet_name == 'Réf technique':
            text_chunk = (
                f"Champ technique: {row['Libellé champ']} dans la source {row['Nom source']} (Plateforme: {row['Plateforme']}). "
                f"Type: {row['Type']}({row['Taille']}). Obligatoire: {row['Obligatoire']}. "
                f"Confidentialité: {row['Confidentialité']}. Règle métier: {row['Règle métier']}. "
                f"Libellé métier: {row['Libellé Métier']}. Commentaire: {row['Commentaire']}."
            )
        elif sheet_name == 'Référentiel Flux':
            text_chunk = (
                f"Traitement dans Flux: {row['Nom Flux']}. Champ source: {row['Nom Champ SD Source']} (de {row['Nom SD Source']} sur {row['Plateforme source']}). "
                f"Règle: {row['Règle de Gestion']}. Champ cible: {row['Nom Champ Cible']} (vers {row['Nom SD Cible']} sur {row['Plateforme cible']}). "
                f"Confidentialité: {row['Confidentialité']}. Description traitement: {row['Description traitement']}. "
                 f"Commentaire: {row['Commentaire']}."
            )
        else:
            # Fallback for unexpected sheets: just join columns
            text_chunk = ". ".join([f"{col}: {val}" for col, val in row.items() if val])

        if text_chunk: # Only add if we have text
            texts_to_embed.append(text_chunk)
            # Store useful metadata
            metadata = {
                "source_sheet": sheet_name,
                "original_row_index": index,
                "text": text_chunk, # Store the text itself for easy retrieval
                # Add all original columns from the row for full context
                "original_data": row.to_dict() 
            }
            metadata_list.append(metadata)

print(f"Prepared {len(texts_to_embed)} text chunks for embedding.")

# --- Step 3: Generate Embeddings ---
if texts_to_embed:
    print("Generating embeddings (this may take a while)...")
    embeddings = model.encode(texts_to_embed, show_progress_bar=True)
    print(f"Generated {len(embeddings)} embeddings.")

    # --- Step 4 & 5: Setup Qdrant Collection ---
    vector_size = model.get_sentence_embedding_dimension()
    print(f"Vector size: {vector_size}")
    print(f"Checking/Creating Qdrant collection: {qdrant_collection_name}...")

    try:
        client.recreate_collection(
            collection_name=qdrant_collection_name,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
            # You can add hnsw_config or quantization_config here for optimization if needed
        )
        print(f"Collection '{qdrant_collection_name}' created/recreated successfully.")
    except Exception as e:
        print(f"Error interacting with Qdrant collection: {e}")
        # Consider if you want to proceed if the collection exists or stop
        try:
            # Check if collection exists if recreate failed (e.g., permissions issue)
             collection_info = client.get_collection(collection_name=qdrant_collection_name)
             print(f"Collection '{qdrant_collection_name}' already exists. Proceeding with upsert.")
             # Check if vector size matches
             if collection_info.vectors_config.params.size != vector_size:
                 print(f"ERROR: Collection vector size ({collection_info.vectors_config.params.size}) does not match model dimension ({vector_size}). Please delete and recreate the collection.")
                 exit()
        except Exception as e2:
            print(f"Error confirming collection status: {e2}")
            exit()


    # --- Step 6: Upsert Data to Qdrant ---
    print("Preparing data points for Qdrant...")
    points_to_upsert = []
    for i in range(len(embeddings)):
        points_to_upsert.append(
            models.PointStruct(
                id=str(uuid.uuid4()), # Generate a unique UUID for each point
                vector=embeddings[i].tolist(), # Convert numpy array to list
                payload=metadata_list[i]
            )
        )

    if points_to_upsert:
        print(f"Upserting {len(points_to_upsert)} points to Qdrant collection '{qdrant_collection_name}'...")
        # Upsert in batches for potentially large datasets
        batch_size = 100 # Adjust batch size based on your data and Qdrant setup
        for i in range(0, len(points_to_upsert), batch_size):
            batch = points_to_upsert[i:i + batch_size]
            try:
                client.upsert(
                    collection_name=qdrant_collection_name,
                    points=batch,
                    wait=True # Wait for the operation to complete
                )
                print(f"Upserted batch {i // batch_size + 1}/{(len(points_to_upsert) - 1) // batch_size + 1}")
            except Exception as e:
                print(f"Error during Qdrant upsert (batch starting at index {i}): {e}")
                # Decide how to handle errors: log, retry, stop?
                # break # Stop on first error

        print("Data upsertion to Qdrant complete.")
    else:
        print("No points to upsert.")

else:
    print("No text chunks were generated from the Excel file. Nothing to embed or upsert.")

print("Process finished.")
