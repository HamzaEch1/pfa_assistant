#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "--- Starting Project Setup ---"

# Create the main application directory
echo "Creating directory: ./app"
mkdir -p app

# === Create Python Files within ./app ===

echo "Creating ./app/config.py..."
cat << 'EOF' > ./app/config.py
# config.py
import os

# --- Page Configuration ---
PAGE_TITLE = "Chat Banque Populaire"
PAGE_ICON = "🐴"

# --- External Services Configuration ---
# Use service names for hosts when running in Docker
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "banque_ma_data_catalog")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", 'paraphrase-multilingual-MiniLM-L12-v2')
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "llama3:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434") # Use service name 'ollama'
NUM_RESULTS_TO_RETRIEVE = int(os.getenv("NUM_RESULTS_TO_RETRIEVE", 10))

# --- PostgreSQL Configuration ---
# Use service name 'db' for the host when running in Docker
PG_HOST = os.getenv("PG_HOST", "db")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")
PG_DB = os.getenv("PG_DB", "mydb")


# --- JWT Configuration ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") # Load from environment variable
if not JWT_SECRET_KEY:
    print("ALERT: JWT_SECRET_KEY environment variable not set! Using a default, insecure key.")
    JWT_SECRET_KEY = "default-insecure-secret-key-for-dev-only" # Fallback for dev only

JWT_ALGORITHM = "HS256"
JWT_EXP_DELTA_SECONDS = 1800 # Token validity in seconds (e.g., 30 minutes)

EOF

echo "Creating ./app/database.py..."
cat << 'EOF' > ./app/database.py
# database.py
import psycopg2
from psycopg2.extras import Json, DictCursor
import hashlib
import streamlit as st
import config # Import the configuration

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=config.PG_HOST, # Read host from config
            port=config.PG_PORT,
            dbname=config.PG_DB,
            user=config.PG_USER,
            password=config.PG_PASSWORD
        )
        return conn
    except psycopg2.OperationalError as e:
        # Specific error for connection issues
        st.error(f"Erreur de connexion à PostgreSQL ({config.PG_HOST}): {e}")
        return None
    except Exception as e:
        st.error(f"Erreur inattendue lors de la connexion DB: {e}")
        return None

def init_db():
    """Initializes the database schema if tables don't exist."""
    conn = get_db_connection()
    if not conn:
        st.error("Initialisation DB échouée: Connexion impossible.")
        return False
    try:
        with conn.cursor() as cur:
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(100) NOT NULL,
                    full_name VARCHAR(100),
                    email VARCHAR(100) UNIQUE,
                    phone VARCHAR(20),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create conversations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    messages JSONB NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Insert default admin user if not present
            cur.execute("SELECT 1 FROM users WHERE username = %s LIMIT 1", ('admin',))
            if not cur.fetchone():
                # Use a more secure default password or recommend changing it
                default_admin_pass = 'admin123'
                password_hash = hashlib.sha256(default_admin_pass.encode()).hexdigest()
                cur.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, is_admin, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ('admin', password_hash, 'Administrateur', 'admin@example.com', True, True))
                print("Default admin user 'admin' created with password 'admin123'. Please change this password.")


            conn.commit()
        print("Base de données initialisée avec succès.")
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation de la base de données: {e}")
        conn.rollback() # Rollback changes on error
        return False
    finally:
        if conn:
            conn.close()

def authenticate_user(username, password):
    """Authenticates a user against the database."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cur.execute("""
                SELECT * FROM users
                WHERE username = %s AND password_hash = %s AND is_active = TRUE
            """, (username, password_hash))
            user = cur.fetchone()
            return user # Returns user dict or None
    except Exception as e:
        st.error(f"Erreur lors de l'authentification: {e}")
        return None
    finally:
        if conn:
            conn.close()

def create_user(username, password, full_name, email, phone=None):
    """Creates a new user in the database."""
    conn = get_db_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"

    # Basic validation before DB check
    if not username or not password or not full_name:
         return False, "Nom d'utilisateur, mot de passe et nom complet sont requis."
    if email:
        # Simple check, regex might be more robust
        if '@' not in email or '.' not in email.split('@')[-1]:
            return False, "Format d'email invalide."

    try:
        with conn.cursor() as cur:
            # Check username existence
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return False, "Ce nom d'utilisateur est déjà utilisé"
            # Check email existence if provided
            if email:
                cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    return False, "Cette adresse email est déjà utilisée"

            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cur.execute("""
                INSERT INTO users (username, password_hash, full_name, email, phone, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, password_hash, full_name, email, phone, True)) # Activate user by default
            conn.commit()
            return True, "Compte créé avec succès"
    except Exception as e:
        conn.rollback()
        print(f"DEBUG: Erreur lors de la création de l'utilisateur: {e}") # More detailed log
        return False, f"Erreur interne lors de la création du compte." # User-friendly message
    finally:
        if conn:
            conn.close()

def load_user_conversations(user_id):
    """Loads all conversations for a specific user."""
    conn = get_db_connection()
    if not conn:
        return {}
    conversations = {}
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM conversations WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
            for row in cur.fetchall():
                # Ensure messages are loaded correctly (psycopg2 might return string if not handled)
                messages_data = row['messages']
                if isinstance(messages_data, str):
                    try:
                        messages_data = json.loads(messages_data)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode messages JSON for conv_id {row['id']}")
                        messages_data = [] # Default to empty list on error

                conversations[row['id']] = {
                    "id": row['id'],
                    "title": row['title'],
                    "timestamp": row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    "messages": messages_data
                }
        return conversations
    except Exception as e:
        st.error(f"Erreur lors du chargement des conversations: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def save_conversation_to_db(conversation, user_id):
    """Saves or updates a conversation for a specific user."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            # Use INSERT ... ON CONFLICT ... UPDATE for atomicity (requires id to be primary key or unique constraint)
            cur.execute("""
                INSERT INTO conversations (id, user_id, title, timestamp, messages)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    timestamp = EXCLUDED.timestamp,
                    messages = EXCLUDED.messages
                WHERE conversations.user_id = %s;
            """, (
                conversation["id"],
                user_id,
                conversation["title"],
                conversation["timestamp"], # Pass datetime object directly
                Json(conversation["messages"]), # Use Json adapter
                user_id # Needed for the WHERE clause in DO UPDATE
            ))
            conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Erreur lors de la sauvegarde de la conversation: {e}")
        return False
    finally:
        if conn:
            conn.close()

def delete_conversation_from_db(conv_id, user_id):
    """Deletes a conversation ensuring it belongs to the user."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM conversations WHERE id = %s AND user_id = %s", (conv_id, user_id))
            conn.commit()
            # Check if deletion was successful (optional)
            return cur.rowcount > 0
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Erreur lors de la suppression de la conversation: {e}")
        return False
    finally:
        if conn:
            conn.close()
EOF

echo "Creating ./app/models.py..."
cat << 'EOF' > ./app/models.py
# models.py
import streamlit as st
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import ollama
import config # Import the configuration

# Flag to prevent multiple error messages per resource per run
_qdrant_error_shown = False
_embedding_error_shown = False
_ollama_error_shown = False

@st.cache_resource
def get_embedding_model():
    """Loads the Sentence Transformer model."""
    global _embedding_error_shown
    print(f"Attempting to load embedding model: {config.EMBEDDING_MODEL_NAME}")
    try:
        model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        print("Embedding model loaded successfully.")
        _embedding_error_shown = False # Reset error flag on success
        return model
    except Exception as e:
        if not _embedding_error_shown:
            st.error(f"Erreur chargement modèle embedding ({config.EMBEDDING_MODEL_NAME}): {e}")
            _embedding_error_shown = True
        print(f"ERROR loading embedding model: {e}")
        return None

@st.cache_resource
def get_qdrant_client():
    """Connects to the Qdrant vector database."""
    global _qdrant_error_shown
    print(f"Attempting connection to Qdrant at {config.QDRANT_URL}...")
    try:
        client = QdrantClient(url=config.QDRANT_URL, timeout=10) # Add timeout
        # Check connection by getting collection info (more reliable than just get_collection)
        client.get_collection(collection_name=config.QDRANT_COLLECTION_NAME)
        print("Connected to Qdrant and collection verified.")
        _qdrant_error_shown = False # Reset error flag on success
        return client
    except Exception as e:
        # Check if it's a connection error vs collection not found, etc.
        if not _qdrant_error_shown:
            st.error(f"Erreur connexion Qdrant ({config.QDRANT_URL}). Vérifiez service. Détails: {e}")
            _qdrant_error_shown = True
        print(f"ERROR connecting to Qdrant: {e}")
        return None

@st.cache_resource
def get_ollama_client():
    """Connects to the Ollama client."""
    global _ollama_error_shown
    print(f"Attempting connection to Ollama at {config.OLLAMA_HOST}...")
    try:
        client = ollama.Client(host=config.OLLAMA_HOST)
        # Test connection using list()
        client.list()
        print("Connecté à Ollama.")
        _ollama_error_shown = False # Reset error flag on success
        return client
    except ImportError:
         if not _ollama_error_shown:
            st.error("Bibliothèque Ollama non trouvée. Installez-la: pip install ollama")
            _ollama_error_shown = True
         print("ERROR: Ollama library not found.")
         return None
    except Exception as e:
        if not _ollama_error_shown:
            st.error(f"Erreur connexion Ollama ({config.OLLAMA_HOST}). Vérifiez service. Détails: {e}")
            _ollama_error_shown = True
        print(f"ERROR connecting to Ollama: {e}")
        return None

EOF

echo "Creating ./app/rag.py..."
cat << 'EOF' > ./app/rag.py
# rag.py
import streamlit as st
import config # Import the configuration
import models # To access clients/models

def get_rag_response(user_query, embedding_model, qdrant_client, ollama_client):
    """Generates a response using Retrieval-Augmented Generation."""
    if not all([embedding_model, qdrant_client, ollama_client]):
        st.error("Erreur RAG : Un ou plusieurs composants (modèle embedding, Qdrant, Ollama) ne sont pas initialisés.")
        return "Erreur : Composants RAG non prêts." # Return error message for UI

    try:
        # 1. Embed the user query
        print(f"Embedding query for RAG: '{user_query[:50]}...'")
        query_embedding = embedding_model.encode(user_query).tolist()
        print("Query embedding generated.")

        # 2. Search Qdrant for relevant documents
        print(f"Searching Qdrant collection '{config.QDRANT_COLLECTION_NAME}'...")
        search_result = qdrant_client.search(
            collection_name=config.QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=config.NUM_RESULTS_TO_RETRIEVE,
        )
        retrieved_texts = [hit.payload.get("text", "") for hit in search_result if hit.payload and hit.payload.get("text")]
        print(f"Retrieved {len(retrieved_texts)} chunks from Qdrant.")

        if not retrieved_texts:
            # Optionally try Ollama without context, or return specific message
            # response_content = get_ollama_direct_response(user_query, ollama_client)
            # return response_content if response_content else "..."
            return "Je n'ai pas trouvé d'information pertinente sur cette question dans ma base de connaissances."

        # 3. Construct the prompt with context
        context_string = "\n".join(f"- {chunk}" for chunk in retrieved_texts)
        system_prompt = f"""Vous êtes un assistant virtuel expert de la Banque Populaire.
Utilisez UNIQUEMENT le contexte suivant fourni pour répondre à la question de l'utilisateur.
Soyez concis et direct. Ne mentionnez pas que vous utilisez un contexte.
RÈGLES STRICTES :
1. Si la réponse n'est pas explicitement présente dans le contexte, dites EXACTEMENT : "Je ne dispose pas de cette information spécifique dans ma base de données."
2. Ne générez JAMAIS d'informations, d'hypothèses ou de conclusions non présentes dans le contexte.
3. Répondez en français.

Contexte:
{context_string}"""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_query},
        ]
        print("Prompt prepared for Ollama.")

        # 4. Call Ollama for response generation
        print(f"Sending request to Ollama model: {config.OLLAMA_MODEL_NAME}...")
        response = ollama_client.chat(
            model=config.OLLAMA_MODEL_NAME,
            messages=messages,
        )
        response_content = response.get('message', {}).get('content', '').strip()
        print("Received response from Ollama.")
        return response_content or "Désolé, une erreur s'est produite lors de la génération de la réponse."

    except Exception as e:
        print(f"Erreur pendant le processus RAG: {e}")
        st.error(f"Une erreur est survenue lors de la recherche d'informations : {e}")
        return f"Une erreur technique est survenue." # User-friendly error

# Optional: Function for direct Ollama call without RAG context
def get_ollama_direct_response(user_query, ollama_client):
     if not ollama_client:
        st.error("Client Ollama non initialisé.")
        return None
     try:
        print(f"Sending direct query to Ollama model: {config.OLLAMA_MODEL_NAME}...")
        response = ollama_client.chat(
            model=config.OLLAMA_MODEL_NAME,
            messages=[{'role': 'user', 'content': user_query}],
        )
        print("Received direct response from Ollama.")
        return response.get('message', {}).get('content', '').strip()
     except Exception as e:
        print(f"Erreur pendant l'appel direct à Ollama: {e}")
        st.error(f"Erreur de communication avec le modèle de langage : {e}")
        return None
EOF

echo "Creating ./app/auth.py..."
cat << 'EOF' > ./app/auth.py
# auth.py
import streamlit as st
import re
import jwt
import datetime
import time # Import time for potential rate limiting or delays
import database as db
import config # Import config for JWT settings

# --- JWT Token Functions ---

def generate_token(user_data):
    """Generates a JWT for the given user data."""
    if not config.JWT_SECRET_KEY:
         st.error("Erreur critique: Clé secrète JWT non configurée côté serveur.")
         return None

    payload = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'is_admin': user_data.get('is_admin', False), # Include admin status
        'full_name': user_data.get('full_name', ''), # Include full name if available
        'iat': datetime.datetime.utcnow(), # Issued at time
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=config.JWT_EXP_DELTA_SECONDS)
    }
    try:
        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return token
    except Exception as e:
        print(f"ERROR generating token: {e}")
        st.error(f"Erreur lors de la génération du token.")
        return None

def verify_token(token):
    """Verifies a JWT. Returns user payload if valid, None otherwise."""
    if not token:
        return None
    if not config.JWT_SECRET_KEY:
         print("ERROR: JWT_SECRET_KEY not configured for verification.")
         # Don't show internal error details to user here
         st.error("Erreur de configuration d'authentification.")
         return None
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM]
        )
        # Optional: Check if user still exists and is active in DB here for extra security
        # conn = db.get_db_connection()
        # if conn:
        #     try:
        #         with conn.cursor() as cur:
        #             cur.execute("SELECT 1 FROM users WHERE id = %s AND is_active = TRUE", (payload['user_id'],))
        #             if not cur.fetchone():
        #                 print(f"Token valid but user {payload['user_id']} not found or inactive.")
        #                 return None # Treat as invalid if user doesn't exist / inactive
        #     finally:
        #         conn.close()
        # else:
        #     print("Warning: Could not verify user existence against DB during token validation.")
        #     # Decide whether to allow access if DB connection fails - risky
        return payload
    except jwt.ExpiredSignatureError:
        st.warning("Session expirée. Veuillez vous reconnecter.")
        return None
    except jwt.InvalidTokenError as e:
        # Log the specific error for debugging but show generic message
        print(f"Invalid token error: {e}")
        st.error(f"Session invalide. Veuillez vous reconnecter.")
        return None
    except Exception as e:
        print(f"Unexpected token validation error: {e}")
        st.error(f"Erreur de validation de session.")
        return None

# --- Authentication Logic ---

def handle_login():
    """Handles the login attempt and generates JWT."""
    username = st.session_state.get("username", "")
    password = st.session_state.get("password", "")

    if not username or not password:
        st.error("Nom d'utilisateur et mot de passe requis.")
        return

    # Add slight delay to mitigate timing attacks / brute force
    time.sleep(0.5)

    user = db.authenticate_user(username, password)
    if user:
        token = generate_token(user)
        if token:
            st.session_state['jwt_token'] = token
            # Clear sensitive items used only for login
            if "password" in st.session_state: del st.session_state["password"]
            if "username" in st.session_state: del st.session_state["username"]
            # Reset view state on successful login
            st.session_state.view = 'Chat' # Default to Chat view after login
            # Trigger rerun to apply authentication check in app.py
            st.rerun()
        # Error handled in generate_token if it fails
    else:
        st.error("Identifiants incorrects ou utilisateur inactif.")


def handle_signup():
    """Handles the signup attempt."""
    username = st.session_state.get("new_username", "")
    password = st.session_state.get("new_password", "")
    confirm_password = st.session_state.get("confirm_password", "")
    full_name = st.session_state.get("full_name", "")
    email = st.session_state.get("email", "")
    phone = st.session_state.get("phone", "")

    # Simple validation
    errors = []
    if not username: errors.append("Nom d'utilisateur requis.")
    if not password: errors.append("Mot de passe requis.")
    if not confirm_password: errors.append("Confirmation du mot de passe requise.")
    if not full_name: errors.append("Nom complet requis.") # Make full name mandatory maybe?

    if password != confirm_password:
        errors.append("Les mots de passe ne correspondent pas.")
    elif password and len(password) < 6: # Check length only if passwords match or exist
        errors.append("Le mot de passe doit comporter au moins 6 caractères.")

    if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        errors.append("Format d'email invalide.")

    if errors:
        for error in errors:
            st.error(error)
        return

    # Proceed with creation if validation passes
    success, message = db.create_user(username, password, full_name, email, phone)
    if success:
        st.success(message + " Vous pouvez maintenant vous connecter.")
        # Reset form fields
        for key in ["new_username", "new_password", "confirm_password", "full_name", "email", "phone"]:
            if key in st.session_state: del st.session_state[key]
        # Switch to login view
        st.session_state.auth_view = "login"
        st.rerun()
    else:
        st.error(message) # Show error message from db.create_user


def logout():
    """Logs out the user by clearing the token and related state."""
    print("Logging out user...")
    keys_to_clear = ['jwt_token', 'user', 'authenticated', 'current_conversation_id', 'messages', 'conversation_history', 'view']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    # Explicitly set authenticated to False after clearing token
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun() # Rerun to show the login page


# --- Authentication UI ---
# This UI part now focuses only on displaying the forms
# The decision *whether* to show this UI is made in app.py

def show_auth_ui():
    """Displays the login or signup form based on st.session_state.auth_view."""
    st.session_state.setdefault('auth_view', 'login') # Ensure default view is set

    # Use columns to center the auth box
    col1, col_main, col3 = st.columns([1, 1.5, 1])

    with col_main:
        # st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}") # Title can be outside the box
        st.image(
            "https://upload.wikimedia.org/wikipedia/fr/thumb/8/8d/Banque_Populaire_logo.svg/1200px-Banque_Populaire_logo.svg.png",
            width=150, # Adjust width as needed
        )

        auth_view = st.session_state.auth_view

        # Login Form
        if auth_view == "login":
            with st.form("login_form"):
                st.subheader("Connexion")
                st.text_input("Nom d'utilisateur", key="username", autocomplete="username")
                st.text_input("Mot de passe", key="password", type="password", autocomplete="current-password")
                login_button = st.form_submit_button("Se connecter", use_container_width=True)
                if login_button:
                    # Call handle_login directly here instead of on_click
                    # This ensures state is available correctly within the form context
                    handle_login()

            st.markdown("---") # Separator
            if st.button("Pas encore de compte ? Créer un compte", use_container_width=True, type="secondary"):
                st.session_state.auth_view = "signup"
                # Reset potential login form error states if needed
                st.rerun()

        # Signup Form
        elif auth_view == "signup":
            with st.form("signup_form"):
                st.subheader("Création de compte")
                st.text_input("Nom d'utilisateur *", key="new_username")
                st.text_input("Mot de passe *", key="new_password", type="password", help="Minimum 6 caractères")
                st.text_input("Confirmer mot de passe *", key="confirm_password", type="password")
                st.text_input("Nom complet *", key="full_name")
                st.text_input("Email", key="email")
                st.text_input("Téléphone", key="phone")
                signup_button = st.form_submit_button("Créer un compte", use_container_width=True)
                if signup_button:
                    handle_signup() # Call directly on submit

            st.markdown("---") # Separator
            if st.button("Déjà un compte ? Se connecter", use_container_width=True, type="secondary"):
                st.session_state.auth_view = "login"
                # Reset potential signup form error states if needed
                st.rerun()
EOF

echo "Creating ./app/history.py..."
cat << 'EOF' > ./app/history.py
# history.py
import streamlit as st
import datetime
import uuid
import io
import json # Import json for robust message handling
import database as db # Use the database module

# --- Helper function to save conversation ---
def save_current_conversation():
    """Saves the active conversation to history and DB."""
    # Use .get() for safer access to session state items
    messages = st.session_state.get('messages', [])
    current_conv_id = st.session_state.get('current_conversation_id')
    user_info = st.session_state.get('user') # User info from verified JWT

    # Validate required information
    if not messages or not current_conv_id or not user_info or 'user_id' not in user_info:
        print(f"Warning: Skipping save_current_conversation. Missing data: messages={bool(messages)}, conv_id={bool(current_conv_id)}, user_info={bool(user_info and 'user_id' in user_info)}")
        # Optionally show a subtle warning if needed, but often saving is background
        # st.toast("Sauvegarde auto: Informations manquantes.")
        return

    user_id = user_info['user_id'] # Get user ID from verified token payload

    # Generate title from first user message safely
    user_messages_content = [msg["content"] for msg in messages if msg["role"] == "user" and "content" in msg]
    if user_messages_content:
        first_message = user_messages_content[0].replace("\n", " ").strip()
        title = (first_message[:47] + '...') if len(first_message) > 50 else first_message
    else:
        title = "Nouvelle conversation" # Default title

    conversation_data = {
        "id": current_conv_id,
        "title": title,
        "timestamp": datetime.datetime.now(), # Use server time for timestamp
        "messages": messages # Store the list of message dicts
    }

    # Update session state history (use string timestamp for display consistency if needed)
    st.session_state.conversation_history[current_conv_id] = {
        **conversation_data,
        "timestamp": conversation_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save to database
    print(f"Saving conversation {current_conv_id} for user {user_id} to DB...")
    success = db.save_conversation_to_db(conversation_data, user_id)
    if success:
        print(f"Conversation {current_conv_id} saved successfully.")
        # st.toast("Conversation sauvegardée.") # Optional feedback
    else:
        print(f"ERROR: Failed to save conversation {current_conv_id} to DB.")
        st.error(f"Échec de la sauvegarde de la conversation dans la base de données.") # More visible error


# --- Other history functions ---

def load_conversation(conv_id):
    """Loads a selected conversation into the main chat view."""
    user_info = st.session_state.get('user')
    conversation_history = st.session_state.get('conversation_history', {})

    if not user_info:
        st.warning("Utilisateur non authentifié.")
        return

    if conv_id in conversation_history:
        # Save current conversation if switching from another one that has messages
        if st.session_state.get('messages') and st.session_state.get('current_conversation_id') != conv_id:
             print(f"Switching conversation: Saving current one ({st.session_state.get('current_conversation_id')}) first.")
             save_current_conversation()

        # Load selected conversation
        print(f"Loading conversation {conv_id}...")
        st.session_state.current_conversation_id = conv_id
        # Ensure messages are in correct list format
        loaded_messages = conversation_history[conv_id].get("messages", [])
        if isinstance(loaded_messages, str): # Handle case where DB might return JSON string
             try:
                 loaded_messages = json.loads(loaded_messages)
             except json.JSONDecodeError:
                 print(f"Warning: Could not decode messages for loaded conv_id {conv_id}. Resetting.")
                 loaded_messages = []
        st.session_state.messages = loaded_messages if isinstance(loaded_messages, list) else []

        st.rerun() # Rerun to update the chat display
    else:
        st.warning("Conversation non trouvée ou inaccessible.")


def start_new_conversation():
    """Starts a new, empty conversation."""
    user_info = st.session_state.get('user')
    if not user_info or 'user_id' not in user_info:
        st.error("Action impossible: Utilisateur non authentifié.")
        return

    print("Starting new conversation...")
    # Save the current one if it exists and has messages
    if st.session_state.get('messages') and st.session_state.get('current_conversation_id'):
        print(f"Saving previous conversation ({st.session_state.get('current_conversation_id')}) before starting new.")
        save_current_conversation()

    # Create a new conversation ID
    new_id = str(uuid.uuid4())
    st.session_state.current_conversation_id = new_id
    st.session_state.messages = [] # Clear messages for the new chat
    # Add the new (empty) conversation to the history state immediately so it appears
    st.session_state.conversation_history[new_id] = {
        "id": new_id,
        "title": "Nouvelle conversation",
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": []
    }
    print(f"New conversation started with ID: {new_id}")
    st.rerun() # Rerun to clear the chat display and show the new convo in history


def delete_conversation(conv_id):
    """Deletes a conversation from session and DB."""
    user_info = st.session_state.get('user')
    conversation_history = st.session_state.get('conversation_history', {})

    # Check user authentication and existence of conversation ID
    if not user_info or 'user_id' not in user_info:
        st.warning("Impossible de supprimer: Utilisateur non authentifié.")
        return
    if conv_id not in conversation_history:
        st.warning("Conversation non trouvée dans l'historique de session.")
        return

    print(f"Attempting to delete conversation {conv_id} for user {user_info['user_id']}...")
    user_id = user_info['user_id']
    current_conv_id_before_delete = st.session_state.get('current_conversation_id')

    # Delete from session state first
    del st.session_state.conversation_history[conv_id]
    print(f"Removed conversation {conv_id} from session history.")

    # Delete from DB
    success = db.delete_conversation_from_db(conv_id, user_id)
    if success:
        print(f"Successfully deleted conversation {conv_id} from database.")
        st.toast(f"Conversation supprimée.") # User feedback
    else:
        print(f"ERROR: Failed to delete conversation {conv_id} from database.")
        st.error(f"Échec de la suppression de la conversation de la base de données.")
        # Consider reloading history from DB here if deletion fails to maintain consistency
        # st.session_state.conversation_history = db.load_user_conversations(user_id)


    # If the deleted conversation was the active one, load the latest or clear the view
    if conv_id == current_conv_id_before_delete:
        print(f"Deleted conversation {conv_id} was the active one. Selecting new active conversation.")
        if st.session_state.conversation_history:
             # Load the most recent conversation based on timestamp string
             latest_conv_id = max(st.session_state.conversation_history,
                                  key=lambda k: st.session_state.conversation_history[k].get('timestamp', '1970-01-01 00:00:00'))
             print(f"Loading latest conversation: {latest_conv_id}")
             # Update state directly to avoid issues with load_conversation causing nested reruns potentially
             st.session_state.current_conversation_id = latest_conv_id
             loaded_messages = st.session_state.conversation_history[latest_conv_id].get("messages", [])
             # Ensure messages format
             if isinstance(loaded_messages, str):
                 try: loaded_messages = json.loads(loaded_messages)
                 except: loaded_messages = []
             st.session_state.messages = loaded_messages if isinstance(loaded_messages, list) else []
        else:
             # No history left, clear the chat state
             print("No conversations left in history. Clearing active conversation.")
             st.session_state.current_conversation_id = None
             st.session_state.messages = []
        st.rerun() # Rerun required to update UI based on new state
    else:
        # Only the history list in sidebar needs update
        print(f"Deleted conversation {conv_id} was not the active one. Rerunning to update sidebar.")
        st.rerun()


def get_chat_history_text():
    """Formats the current chat history for download."""
    messages = st.session_state.get('messages', [])
    if not messages:
        return None

    buffer = io.StringIO()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conv_title = "Nouvelle Conversation"
    current_conv_id = st.session_state.get('current_conversation_id')
    conversation_history = st.session_state.get('conversation_history', {})

    if current_conv_id and current_conv_id in conversation_history:
        conv_title = conversation_history[current_conv_id].get('title', conv_title)

    # Sanitize title for filename
    safe_title = "".join(c if c.isalnum() or c in (' ', '-') else '_' for c in conv_title).rstrip()
    safe_title = safe_title.replace(' ', '_')[:30] # Limit length

    buffer.write(f"Historique Conversation: {conv_title} ({current_conv_id})\n")
    buffer.write(f"Exporté le: {now}\n")
    buffer.write("="*40 + "\n\n")

    for msg in messages:
        role = msg.get("role", "inconnu").capitalize()
        content = msg.get("content", "[Contenu manquant]")
        role_display = "Vous" if role.lower() == "user" else ("Assistant" if role.lower() == "assistant" else role)
        buffer.write(f"--- {role_display} ---\n{content}\n\n")

    return buffer.getvalue(), f"Historique_{safe_title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt"
EOF

echo "Creating ./app/ui.py..."
cat << 'EOF' > ./app/ui.py
# ui.py
import streamlit as st
import datetime
import config # Import configuration
import history # Import history functions
import auth # Import auth functions
# No need to import admin_ui here, app.py handles calling it

def show_sidebar():
    """Renders the sidebar content. Assumes user is authenticated."""
    if not st.session_state.get('user'):
        # This function should not be called if user is not authenticated
        # But add a check just in case
        st.sidebar.error("Erreur : Utilisateur non authentifié.")
        return

    with st.sidebar:
        st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}")
        user_display_name = st.session_state.user.get('full_name') or st.session_state.user.get('username', 'Utilisateur')
        st.write(f"Bienvenue, **{user_display_name}**")

        # --- View Selector for Admins ---
        if st.session_state.user.get('is_admin'):
            # Use st.session_state.view to store/retrieve the selection
            st.session_state.setdefault('view', 'Chat') # Ensure default view is set

            view_options = ("Chat", "Admin")
            # Get current index safely
            try:
                current_index = view_options.index(st.session_state.view)
            except ValueError:
                current_index = 0 # Default to Chat if state is invalid
                st.session_state.view = 'Chat'

            st.session_state.view = st.radio(
                "Navigation",
                view_options,
                key="view_selector",
                horizontal=True,
                index=current_index
             )
        else:
            # Ensure non-admins always have 'Chat' view state and hide radio
            st.session_state.view = "Chat"

        # Logout Button
        st.button("Déconnexion", key="logout_btn", on_click=auth.logout, use_container_width=True)
        st.divider()

        # --- Chat Specific Sidebar Elements ---
        if st.session_state.view == "Chat":
            st.button("Nouvelle conversation", type="primary", key="new_chat_btn", on_click=history.start_new_conversation, use_container_width=True)
            st.divider()
            st.subheader("Historique")

            conversation_history = st.session_state.get('conversation_history', {})
            # Sort by timestamp string (descending)
            sorted_conv_ids = sorted(
                conversation_history.keys(),
                key=lambda k: conversation_history[k].get("timestamp", "1970-01-01 00:00:00"),
                reverse=True
            )

            if not sorted_conv_ids:
                st.info("Aucune conversation.")
            else:
                current_conv_id = st.session_state.get("current_conversation_id")
                for conv_id in sorted_conv_ids:
                    # Check if conversation still exists (might be deleted in another session/tab)
                    if conv_id not in conversation_history: continue

                    conv = conversation_history[conv_id]
                    conv_title = conv.get('title', f"Conversation {conv_id[:8]}")
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        # Use type="primary" for selected, "secondary" otherwise
                        button_type = "primary" if current_conv_id == conv_id else "secondary"
                        st.button(f"{conv_title}",
                                    key=f"load_conv_{conv_id}", # Ensure unique key
                                    type=button_type,
                                    use_container_width=True,
                                    help=f"Charger : {conv_title}",
                                    on_click=history.load_conversation,
                                    args=(conv_id,) # Pass conv_id as argument
                                    )
                    with col2:
                        st.button("🗑️",
                                    key=f"del_conv_{conv_id}", # Ensure unique key
                                    help=f"Supprimer : {conv_title}",
                                    on_click=history.delete_conversation,
                                    args=(conv_id,) # Pass conv_id as argument
                                    )

            st.divider()
            # Download button for the current conversation
            if st.session_state.get("current_conversation_id") and st.session_state.get("messages"):
                 try:
                    history_text, file_name = history.get_chat_history_text()
                    if history_text:
                        st.download_button(
                            label="Télécharger la conversation",
                            data=history_text,
                            file_name=file_name,
                            mime="text/plain",
                            use_container_width=True
                        )
                 except Exception as e:
                      print(f"Error generating download button: {e}") # Log error
                      # Don't show error to user, button just won't appear

        # --- Admin Specific Sidebar ---
        elif st.session_state.view == "Admin":
             st.info("⚙️ Panneau Admin")
             # Add any admin-specific sidebar elements if needed later, like links to sub-sections
             # e.g., st.page_link("pages/user_management.py", label="Gérer Utilisateurs")


def show_chat_area():
    """Renders the main chat area and input."""
    st.header(f"{config.PAGE_ICON} Assistant {config.PAGE_TITLE}")
    st.caption(f"Modèle LLM : {config.OLLAMA_MODEL_NAME} | Modèle Embedding : {config.EMBEDDING_MODEL_NAME}")

    # Display existing messages for the current conversation
    current_conv_id = st.session_state.get("current_conversation_id")
    messages = st.session_state.get("messages", [])

    if current_conv_id:
        if not messages:
             st.info("Conversation vide. Posez votre première question ci-dessous.")
        else:
            for message in messages:
                role = message.get("role")
                content = message.get("content")
                if role and content: # Ensure message structure is valid
                    with st.chat_message(role):
                        st.markdown(content)
                else:
                    print(f"Warning: Skipping invalid message format in conv {current_conv_id}: {message}")
    else:
         st.info("Démarrez une nouvelle conversation ou sélectionnez-en une dans l'historique.")


def apply_styles():
    """Applies custom CSS styles."""
    # Using st.markdown for CSS injection
    st.markdown("""
    <style>
        /* General App Styling */
        .stApp {
            /* background-color: #f0f2f6; */ /* Optional: Light background for the whole app */
        }

        /* Sidebar styling */
        div[data-testid="stSidebarUserContent"] {
            padding-top: 1rem; /* Add some padding at the top */
        }
        div[data-testid="stSidebarUserContent"] button {
            margin-bottom: 8px; /* Consistent spacing */
            border-radius: 5px; /* Slightly rounded buttons */
        }
        div[data-testid="stSidebarUserContent"] button:hover {
            /* Define hover effect for secondary buttons if needed */
        }
        div[data-testid="stSidebarUserContent"] button[kind="primary"] {
             /* Style for primary buttons */
        }
        div[data-testid="stSidebarUserContent"] button:contains("🗑️") {
             background-color: transparent !important;
             color: #ff4b4b !important; /* More distinct delete color */
             border: none !important;
             padding: 0.2rem 0.4rem !important;
             line-height: 1 !important;
             opacity: 0.7;
             transition: opacity 0.2s ease-in-out;
        }
         div[data-testid="stSidebarUserContent"] button:contains("🗑️"):hover {
             opacity: 1.0;
         }

        /* Auth form styling */
        div[data-testid="stForm"] {
            background-color: #ffffff; /* White background for form */
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Softer shadow */
            border: 1px solid #e0e0e0; /* Subtle border */
        }
         div[data-testid="stForm"] h3 { /* Subheader inside form */
             margin-bottom: 20px;
             color: #333;
         }

        div[data-testid="stFormSubmitButton"] > button {
            background-color: #005A9E !important; /* BP Blue */
            color: white !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 10px 0 !important; /* Adjust padding */
            font-weight: bold;
        }
         div[data-testid="stFormSubmitButton"] > button:hover {
             background-color: #004C80 !important; /* Darker BP Blue on hover */
         }

        /* Auth switch button styling (below the form) */
        /* Target more specifically if possible */
        div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="element-container"] > div.stButton button {
            background-color: transparent !important;
            color: #005A9E !important; /* BP Blue */
            border: 1px solid #005A9E !important;
            width: 100%;
            margin-top: 15px; /* More space above */
            border-radius: 5px !important;
            padding: 8px 0 !important;
            font-weight: bold;
        }
         div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="element-container"] > div.stButton button:hover {
              background-color: #e7f3ff !important; /* Light blue background on hover */
              color: #004C80 !important;
              border-color: #004C80 !important;
         }


         /* Chat message styling */
        [data-testid="stChatMessage"] {
            border-radius: 10px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.6rem; /* Slightly more space */
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); /* Subtle shadow for messages */
            border: 1px solid transparent; /* Base border */
        }
        [data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-user"]) {
            background-color: #e9f5ff; /* Lighter blue for user */
            border-color: #cde5ff;
        }
        [data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) {
            background-color: #f8f9fa; /* Lighter grey for assistant */
            border-color: #dee2e6;
        }

        /* Sidebar Radio Button Styling */
        div[data-testid="stRadio"] {
            margin-bottom: 1rem; /* Space below radio buttons */
        }
        div[data-testid="stRadio"] > label {
            padding: 6px 12px !important; /* Adjust padding */
            margin: 0 4px 5px 0 !important; /* Adjust spacing */
            border: 1px solid #ccc !important;
            border-radius: 15px !important; /* More rounded */
            cursor: pointer !important;
            display: inline-block !important;
            transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
            font-size: 0.9em; /* Slightly smaller font */
        }
        div[data-testid="stRadio"] input[type="radio"] {
             display: none; /* Hide the actual radio button */
        }
        div[data-testid="stRadio"] input[type="radio"]:checked + label {
            background-color: #005A9E !important; /* BP Blue */
            color: white !important;
            border-color: #004C80 !important; /* Darker blue border */
            font-weight: bold;
        }

        /* Center alignment for Auth UI Image/Forms (if needed, depends on column setup) */
        /* Might need adjustment based on exact Streamlit version and structure */
        /* div[data-testid="stVerticalBlock"] {
            align-items: center;
        } */

    </style>
    """, unsafe_allow_html=True)

EOF

echo "Creating ./app/admin_logic.py..."
cat << 'EOF' > ./app/admin_logic.py
# admin_logic.py
import streamlit as st
import pandas as pd
import uuid
from qdrant_client import models as qdrant_models # Use alias to avoid conflict with local 'models' module
import config
import models as model_loader # Reuse model loading functions
import time # For timing operations

# --- Helper function to create text chunks (adapted from embeddata.txt) ---
def create_text_chunk(row, sheet_name):
    """Creates a formatted text string from a DataFrame row based on the sheet name."""
    text_chunk = ""
    # Use .get(column, default_value) for robustness against missing columns
    if sheet_name == 'Référentiel Sources':
        text_chunk = (
            f"Source: {row.get('Nom source','N/A')} ({row.get('Type Source','N/A')} sur {row.get('Plateforme source','N/A')}). "
            f"Flux: {row.get('Flux/Scénario SD','N/A')}. "
            f"Domaine: {row.get('Domaine','N/A')} / {row.get('Sous domaine','N/A')}. "
            f"Application source: {row.get('Application Source','N/A')}. "
            f"Cible: {row.get('Plateforme cible','N/A')} ({row.get('Nom cible','N/A')}). "
            f"Chargement: {row.get('Mode chargement','N/A')} ({row.get('Fréquence MAJ','N/A')}) via {row.get('Technologie de chargement(Outil)','N/A')} ({row.get('Technologie','N/A')}). "
            f"Procédure: {row.get('Nom Flux/Procedure','N/A')}. "
            f"Taille: {row.get('Taille Objet','N/A')}. Format: {row.get('Format','N/A')}. "
            f"Description: {row.get('Description','N/A')}. "
            f"Filiale: {row.get('Filiale','N/A')}."
        )
    elif sheet_name == 'Glossaire Métier':
        text_chunk = (
            f"Terme métier: {row.get('Libellé Métier','N/A')}. Propriétaire: {row.get('Propriétaire','N/A')}. "
            f"Description: {row.get('Description','N/A')}. Confidentialité: {row.get('Confidentialité','N/A')}. "
            f"Règle métier: {row.get('Règle métier','N/A')}. "
            f"Criticité: {row.get('Criticité','N/A')}. "
            f"Qualité adressée: {row.get('Aspect de performance adressé (Qualité)','N/A')}. "
            f"Commentaire: {row.get('Commentaire','N/A')}."
        )
    elif sheet_name == 'Réf technique':
        text_chunk = (
            f"Champ technique: {row.get('Libellé champ','N/A')} dans la source {row.get('Nom source','N/A')} (Plateforme: {row.get('Plateforme','N/A')}). "
            f"Type: {row.get('Type','N/A')}({row.get('Taille','N/A')}). Obligatoire: {row.get('Obligatoire','N/A')}. "
            f"Confidentialité: {row.get('Confidentialité','N/A')}. Règle métier: {row.get('Règle métier','N/A')}. "
            f"Libellé métier: {row.get('Libellé Métier','N/A')}. "
            f"Commentaire: {row.get('Commentaire','N/A')}."
        )
    elif sheet_name == 'Référentiel Flux':
        text_chunk = (
            f"Traitement dans Flux: {row.get('Nom Flux','N/A')}. Champ source: {row.get('Nom Champ SD Source','N/A')} (de {row.get('Nom SD Source','N/A')} sur {row.get('Plateforme source','N/A')}). "
            f"Règle: {row.get('Règle de Gestion','N/A')}. Champ cible: {row.get('Nom Champ Cible','N/A')} (vers {row.get('Nom SD Cible','N/A')} sur {row.get('Plateforme cible','N/A')}). "
            f"Confidentialité: {row.get('Confidentialité','N/A')}. Description traitement: {row.get('Description traitement','N/A')}. "
            f"Commentaire: {row.get('Commentaire','N/A')}."
        )
    else:
        # Fallback: join non-empty column values, using .get() for safety
        chunk_parts = []
        for col, val in row.items():
            if pd.notna(val) and str(val).strip():
                chunk_parts.append(f"{col}: {val}")
        text_chunk = ". ".join(chunk_parts)

    return text_chunk.replace('\n', ' ').strip() # Remove newlines and trim whitespace

# --- Main processing function ---
def process_excel_and_upsert(uploaded_file):
    """Reads an Excel file, processes its sheets, generates embeddings, and upserts to Qdrant."""
    start_time = time.time()
    st.info(f"Début du traitement du fichier : {uploaded_file.name}...")

    # Get necessary clients/models
    qdrant_client = model_loader.get_qdrant_client()
    embedding_model = model_loader.get_embedding_model()

    if not qdrant_client or not embedding_model:
        st.error("Erreur: Client Qdrant ou modèle d'embedding non initialisé. Impossible de continuer.")
        return

    try:
        read_start = time.time()
        # Read all sheets into a dictionary of DataFrames
        # Use io.BytesIO to read the uploaded file in memory
        excel_data = pd.ExcelFile(uploaded_file)
        all_sheets_data = {sheet: excel_data.parse(sheet) for sheet in excel_data.sheet_names}
        read_end = time.time()
        st.success(f"Fichier lu ({len(all_sheets_data)} feuilles) en {read_end - read_start:.2f} secondes.")
        print(f"Sheets found: {list(all_sheets_data.keys())}")
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier Excel : {e}")
        print(f"ERROR reading Excel: {e}")
        return

    texts_to_embed = []
    metadata_list = []
    points_processed = 0
    total_rows = sum(len(df) for df in all_sheets_data.values())
    if total_rows == 0:
        st.warning("Le fichier Excel ne contient aucune donnée.")
        return

    prep_start = time.time()
    # Use st.container() to group progress elements
    progress_container = st.container()
    progress_bar = progress_container.progress(0)
    status_text = progress_container.empty()
    status_text.text(f"Préparation des données (0/{total_rows})...")

    # Process each sheet
    rows_processed = 0
    for sheet_name, df in all_sheets_data.items():
        print(f"Processing sheet: {sheet_name} ({len(df)} rows)")
        # Fill NA and convert all to string before processing row by row
        df = df.fillna('').astype(str)

        for index, row in df.iterrows():
            rows_processed += 1
            text_chunk = create_text_chunk(row, sheet_name)

            if text_chunk: # Only add if we have meaningful text
                texts_to_embed.append(text_chunk)
                # Store useful metadata
                metadata = {
                    "source_sheet": sheet_name,
                    "source_file": uploaded_file.name,
                    "original_row_index": index,
                    "text": text_chunk, # Keep the generated text chunk
                    # Add original data as string dict for JSON compatibility
                    "original_data": row.to_dict() # Already strings due to df.astype(str)
                }
                metadata_list.append(metadata)
                points_processed += 1

            # Update progress bar periodically to avoid slowing down too much
            if rows_processed % 100 == 0 or rows_processed == total_rows:
                 progress_value = rows_processed / total_rows
                 status_text.text(f"Préparation des données ({rows_processed}/{total_rows})...")
                 progress_bar.progress(progress_value)

    prep_end = time.time()
    status_text.text(f"Préparation terminée ({points_processed} points valides) en {prep_end - prep_start:.2f}s.")
    print(f"Data preparation finished. Found {points_processed} valid points.")

    if not texts_to_embed:
        st.warning("Aucun texte traitable n'a été trouvé dans le fichier Excel après préparation.")
        return

    # --- Generate Embeddings ---
    embed_start = time.time()
    status_text.text(f"Génération des embeddings pour {len(texts_to_embed)} points (cela peut prendre du temps)...")
    progress_bar.progress(0) # Reset progress bar for embedding stage

    try:
        # Note: SentenceTransformer progress bar doesn't integrate with st.progress easily
        # We'll just show a spinner or static text during this phase
        with st.spinner("Génération des embeddings en cours..."):
             embeddings = embedding_model.encode(texts_to_embed, show_progress_bar=False) # Disable built-in bar
        embed_end = time.time()
        status_text.text(f"Embeddings générés ({len(embeddings)} vecteurs) en {embed_end - embed_start:.2f}s.")
        print("Embeddings generated.")
        progress_bar.progress(1.0) # Show completion for this stage
    except Exception as e:
        st.error(f"Erreur lors de la génération des embeddings : {e}")
        print(f"ERROR generating embeddings: {e}")
        progress_bar.empty() # Clear progress on error
        status_text.empty()
        return

    # --- Prepare and Upsert to Qdrant ---
    upsert_start = time.time()
    points_to_upsert = [
        qdrant_models.PointStruct( # Use aliased import
            id=str(uuid.uuid4()), # Generate a unique UUID
            vector=embeddings[i].tolist(),
            payload=metadata_list[i]
        ) for i in range(len(embeddings))
    ]

    status_text.text(f"Ajout de {len(points_to_upsert)} points à la collection Qdrant '{config.QDRANT_COLLECTION_NAME}'...")
    progress_bar.progress(0) # Reset progress bar for upsert stage

    # Upsert in batches
    batch_size = 128 # Adjust batch size based on typical data size and Qdrant/network performance
    total_batches = (len(points_to_upsert) - 1) // batch_size + 1
    errors_occurred = False
    batches_processed = 0

    for i in range(0, len(points_to_upsert), batch_size):
        batch = points_to_upsert[i:i + batch_size]
        batch_num = i // batch_size + 1
        try:
            # Show progress for the batch being processed
            status_text.text(f"Ajout à Qdrant (Batch {batch_num}/{total_batches})...")
            progress_bar.progress(batch_num / total_batches)

            qdrant_client.upsert(
                collection_name=config.QDRANT_COLLECTION_NAME,
                points=batch,
                wait=True # Wait for confirmation can slow down, consider wait=False for large imports
            )
            batches_processed += 1
            print(f"Upserted batch {batch_num}/{total_batches}")
        except Exception as e:
            st.error(f"Erreur lors de l'ajout à Qdrant (Batch {batch_num}): {e}")
            print(f"ERROR during Qdrant upsert (Batch {batch_num}): {e}")
            errors_occurred = True
            # Decide how to handle errors: log, retry batch, stop?
            break # Stop on first error for simplicity

    upsert_end = time.time()

    # Final status update
    progress_bar.empty()
    status_text.empty()

    total_duration = upsert_end - start_time
    if errors_occurred:
        st.error(f"Des erreurs se sont produites après {batches_processed}/{total_batches} batches. Traitement interrompu. Durée totale: {total_duration:.2f}s.")
    else:
        st.success(f"Données ajoutées avec succès à la collection '{config.QDRANT_COLLECTION_NAME}'. Durée totale: {total_duration:.2f}s.")
EOF

echo "Creating ./app/admin_ui.py..."
cat << 'EOF' > ./app/admin_ui.py
# admin_ui.py
import streamlit as st
import admin_logic # Import the logic functions
import database as db # To potentially add user management later
import models # Use model loading functions
import config # Use config for collection name etc.
from qdrant_client.http import models as rest # For Qdrant REST models if needed elsewhere

def show_admin_dashboard():
    """Displays the admin dashboard. Assumes user is authenticated and admin."""

    st.title("🐴 Tableau de Bord Administrateur")
    st.divider()

    # --- Section 1: Data Catalog Management ---
    st.header("Gestion du Catalogue de Données (Qdrant)")
    st.markdown(f"Gestion de la collection : `{config.QDRANT_COLLECTION_NAME}`")

    # File Uploader
    uploaded_file = st.file_uploader(
        "Télécharger un fichier Excel (.xlsx) pour ajouter au catalogue",
        type=['xlsx'],
        accept_multiple_files=False,
        key="excel_uploader",
        help="Le fichier sera lu, transformé en vecteurs et ajouté à la base de données Qdrant."
    )

    process_button_placeholder = st.empty()

    if uploaded_file is not None:
        st.info(f"Fichier prêt : `{uploaded_file.name}` ({uploaded_file.size / 1024 / 1024:.2f} Mo)")
        # Place button inside the placeholder
        if process_button_placeholder.button("Lancer le Traitement et l'Ajout", key="process_excel", type="primary"):
            process_button_placeholder.empty() # Hide button after click
            # Check if models are loaded before processing
            embedding_model_check = models.get_embedding_model()
            qdrant_client_check = models.get_qdrant_client()
            if embedding_model_check and qdrant_client_check:
                admin_logic.process_excel_and_upsert(uploaded_file)
            else:
                st.error("Les modèles d'embedding ou le client Qdrant ne sont pas prêts. Impossible de traiter le fichier.")
    st.divider()


    # --- Section 2: User Management (Example Idea) ---
    with st.expander("Gestion des Utilisateurs (Exemple)"):
        st.info("Fonctionnalité de gestion des utilisateurs (activation/désactivation, etc.) peut être ajoutée ici.")
        if st.button("Afficher les utilisateurs", key="show_users_btn"):
            try:
                conn = db.get_db_connection()
                if conn:
                    with conn.cursor(cursor_factory=db.DictCursor) as cur:
                        cur.execute("SELECT id, username, full_name, email, is_admin, is_active, created_at FROM users ORDER BY id")
                        users = cur.fetchall()
                        if users:
                            # Prepare data for display (e.g., convert boolean to readable status)
                            display_users = [{
                                'ID': u['id'],
                                'Utilisateur': u['username'],
                                'Nom Complet': u['full_name'],
                                'Email': u['email'],
                                'Admin': 'Oui' if u['is_admin'] else 'Non',
                                'Actif': 'Oui' if u['is_active'] else 'Non',
                                'Créé le': u['created_at'].strftime('%Y-%m-%d %H:%M') if u['created_at'] else 'N/A'
                            } for u in users]
                            st.dataframe(display_users, use_container_width=True)
                        else:
                            st.write("Aucun utilisateur trouvé.")
                    conn.close()
                else:
                    st.error("Impossible de se connecter à la base de données pour afficher les utilisateurs.")
            except Exception as e:
                st.error(f"Erreur lors de la récupération des utilisateurs: {e}")
                print(f"Error fetching users: {e}")


    # --- Section 3: Qdrant Collection Info (Example Idea) ---
    with st.expander("Informations sur la Collection Qdrant (Exemple)"):
        st.info("Affichage des informations de base sur la collection vectorielle.")
        if st.button("Afficher les infos de la collection", key="show_qdrant_info_btn"):
            qdrant_client = models.get_qdrant_client() # Get client instance
            if qdrant_client:
                try:
                    st.write(f"Interrogation de la collection : `{config.QDRANT_COLLECTION_NAME}` sur `{config.QDRANT_URL}`")
                    with st.spinner("Récupération des informations..."):
                        collection_info = qdrant_client.get_collection(collection_name=config.QDRANT_COLLECTION_NAME)

                    st.metric(label="Nombre de Points (Vecteurs)", value=f"{collection_info.points_count or 0}")
                    st.metric(label="Dimension des Vecteurs", value=f"{collection_info.vectors_config.params.size if collection_info.vectors_config else 'N/A'}")
                    # st.json(collection_info.dict(), expanded=False) # Optionally display full info
                    st.success("Informations récupérées.")

                except Exception as e:
                    st.error(f"Impossible de récupérer les informations de la collection '{config.QDRANT_COLLECTION_NAME}': {e}")
                    print(f"Error fetching Qdrant collection info: {e}")
            else:
                st.error("Client Qdrant non disponible. Vérifiez la connexion dans `models.py` et le service Qdrant.")


    # Add more admin features here as needed using st.expander or columns
EOF

echo "Creating ./app/app.py..."
cat << 'EOF' > ./app/app.py
# app.py
import streamlit as st
import config
import database as db
import models
import rag
import auth # Import updated auth module
import history
import ui
import admin_ui # Import the admin UI module

# --- Page Configuration ---
# Set page config must be the first Streamlit command
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide" # Use wide layout for more space
)

# --- Initialize Database ---
# Done only once at the start of the session if not already done
if 'db_initialized' not in st.session_state:
    print("Attempting DB Initialization...")
    st.session_state.db_initialized = db.init_db()
    if not st.session_state.db_initialized:
        # Show error prominently if DB init fails
        st.error("Erreur critique : Impossible d'initialiser la base de données. L'application risque de ne pas fonctionner correctement.")
        # Optionally st.stop() here if DB is absolutely essential for any view
        # st.stop()
elif not st.session_state.db_initialized:
    # If already failed in a previous run, show persistent error
    st.error("Erreur critique : L'initialisation de la base de données a échoué précédemment.")
    # st.stop()

# --- Initialize Session State Defaults (Safe Initialization) ---
# Use setdefault to initialize only if keys are missing
st.session_state.setdefault('jwt_token', None)
st.session_state.setdefault('user', None) # Will hold verified user data for the current run
st.session_state.setdefault('authenticated', False) # Reflects status for the current run
st.session_state.setdefault('messages', [])
st.session_state.setdefault('current_conversation_id', None)
st.session_state.setdefault('conversation_history', {})
st.session_state.setdefault('view', 'Chat') # Default view is Chat
st.session_state.setdefault('auth_view', 'login') # For login/signup toggle

# --- Apply Styling ---
# Apply styles early so they affect the auth page too
ui.apply_styles()

# --- Authentication Check ---
# Perform this check on every script run to ensure session validity
if not st.session_state.authenticated: # Only verify token if not already authenticated in this run
    if st.session_state.jwt_token:
        print("Verifying existing JWT token...")
        user_payload = auth.verify_token(st.session_state.jwt_token)
        if user_payload:
            # Token is valid, set user info and authenticated status for this run
            print(f"Token verified successfully for user: {user_payload.get('username')}")
            st.session_state.user = user_payload
            st.session_state.authenticated = True

            # Load conversation history if authenticated and history is empty
            # This might happen on first load after refresh with a valid token
            if not st.session_state.conversation_history and 'user_id' in st.session_state.user:
                print(f"Loading conversation history for user {st.session_state.user['user_id']}...")
                st.session_state.conversation_history = db.load_user_conversations(st.session_state.user['user_id'])
                # Select latest conversation if history was just loaded and no conversation is active
                if st.session_state.conversation_history and not st.session_state.current_conversation_id:
                    try:
                        latest_conv_id = max(
                            st.session_state.conversation_history,
                            key=lambda k: st.session_state.conversation_history[k].get('timestamp', '1970-01-01 00:00:00')
                        )
                        print(f"Setting latest conversation {latest_conv_id} as active.")
                        st.session_state.current_conversation_id = latest_conv_id
                        st.session_state.messages = st.session_state.conversation_history[latest_conv_id].get('messages', [])
                    except Exception as e:
                        print(f"Error selecting latest conversation: {e}")


        else:
            # Token is invalid (expired or tempered) or verify_token failed
            print("Token verification failed or token expired.")
            # Clear potentially stale/invalid token and user info
            if 'jwt_token' in st.session_state: del st.session_state['jwt_token']
            if 'user' in st.session_state: del st.session_state['user']
            st.session_state.authenticated = False
            # No need to call logout() here as we need to show the login UI anyway
            # and logout() causes a rerun which might interfere.
    else:
        # No token exists, ensure authenticated is False
        st.session_state.authenticated = False
        st.session_state.user = None


# --- Main App Logic ---
if not st.session_state.authenticated:
    # --- Unauthenticated View ---
    # User is not authenticated (or token failed verification), show login/signup UI
    print("User not authenticated, showing auth UI.")
    auth.show_auth_ui()

else:
    # --- Authenticated View ---
    # User is authenticated for this run (valid token verified)
    print(f"User authenticated: {st.session_state.user.get('username')}. Showing main interface.")

    # Show Sidebar (contains view selector for admin)
    ui.show_sidebar() # This function reads st.session_state.user and sets st.session_state.view

    # --- Determine View (Chat or Admin) ---
    current_view = st.session_state.get('view', 'Chat')
    is_admin = st.session_state.user.get('is_admin', False)

    # Main area container
    main_container = st.container()

    with main_container:
        if current_view == "Admin" and is_admin:
            # --- Admin View ---
            print("Displaying Admin View.")
            # Ensure models needed for admin tasks are loaded/cached
            # Calling them here ensures they are ready if admin needs them
            models.get_embedding_model()
            models.get_qdrant_client()
            admin_ui.show_admin_dashboard()

        elif current_view == "Chat":
            # --- Chat View ---
            print("Displaying Chat View.")
            # Load models needed for chat (cached by Streamlit)
            embedding_model = models.get_embedding_model()
            qdrant_client = models.get_qdrant_client()
            ollama_client = models.get_ollama_client()

            # Show Main Chat Area UI components
            ui.show_chat_area()

            # Chat Input Logic (at the bottom of the page)
            if prompt := st.chat_input("Posez votre question ici..."):
                print(f"Received chat input: '{prompt[:50]}...'")
                current_conversation_id = st.session_state.get('current_conversation_id')
                user_id = st.session_state.user.get('user_id') # Get user ID from verified payload

                if not user_id:
                     st.error("Erreur: Impossible d'identifier l'utilisateur connecté.")
                     st.stop() # Stop if user context is lost somehow

                if not current_conversation_id:
                     print("No active conversation, starting a new one...")
                     # This function should handle the rerun if needed to update state
                     history.start_new_conversation()
                     # After rerun, the state 'current_conversation_id' should be set
                     # Re-read state just in case, though rerun should handle it
                     current_conversation_id = st.session_state.get('current_conversation_id')


                # Check if all components are ready AFTER potentially starting a new convo
                if all([ollama_client, qdrant_client, embedding_model, current_conversation_id]):
                    print(f"Processing prompt for conversation {current_conversation_id}...")
                    # Add user message to state immediately for responsiveness
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    # Rerun to display the user message instantly
                    st.rerun()

                elif not current_conversation_id:
                    st.error("Impossible de démarrer ou de trouver une conversation active. Veuillez réessayer.")
                else: # Models not ready
                    st.error("Les composants IA ne sont pas prêts. Veuillez patienter ou vérifier les services externes.")

            # --- Handle RAG response generation ---
            # This needs to happen *after* the user message is potentially added and displayed by rerun
            # Check if the last message is from the user (to avoid re-generating on simple rerun)
            last_message_is_user = st.session_state.messages and st.session_state.messages[-1].get("role") == "user"

            if last_message_is_user and all([ollama_client, qdrant_client, embedding_model, st.session_state.current_conversation_id]):
                 user_prompt_for_rag = st.session_state.messages[-1]['content']
                 print(f"Generating RAG response for prompt: '{user_prompt_for_rag[:50]}...'")

                 with st.chat_message("assistant"): # Display thinking indicator within assistant message block
                     message_placeholder = st.empty()
                     with st.spinner("Réflexion..."):
                         assistant_response = rag.get_rag_response(
                             user_prompt_for_rag, embedding_model, qdrant_client, ollama_client
                         )
                         assistant_response = assistant_response or "Désolé, je n'ai pas pu générer de réponse."
                         message_placeholder.markdown(assistant_response) # Display final response

                 # Add assistant response to state
                 st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                 print("Assistant response generated and added to state.")

                 # Save the updated conversation (includes user + new assistant message)
                 history.save_current_conversation()
                 # *** Avoid rerun after adding assistant message unless absolutely necessary ***
                 # st.rerun()

        else: # User is not admin trying to access Admin view, or invalid view state
             st.warning("Vue non autorisée ou invalide. Retour au Chat.")
             st.session_state.view = 'Chat'
             st.rerun()

EOF

# === Create Docker Configuration Files ===

echo "Creating Dockerfile..."
cat << 'EOF' > Dockerfile
# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables to prevent buffering stdout/stderr
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by some Python packages (if any)
# Example: RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
# Copy the entire 'app' directory from the build context into '/app/app' in the container
COPY ./app ./app

# Expose the port Streamlit runs on
EXPOSE 8501

# Define the command to run the application
# Run the app.py located inside the copied 'app' directory
CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF

echo "Creating requirements.txt..."
cat << 'EOF' > requirements.txt
# requirements.txt

streamlit
psycopg2-binary # For PostgreSQL connection
qdrant-client>=1.7.0,<2.0.0 # Use a specific version range if needed
sentence-transformers
pandas
openpyxl # Required by pandas for reading .xlsx files
ollama
PyJWT # For JWT authentication
cryptography # Often a dependency for PyJWT or other crypto operations
# Add any other specific dependencies your app might have
EOF

echo "Creating docker-compose.yml..."
cat << 'EOF' > docker-compose.yml
# docker-compose.yml
version: '3.8'

services:
  # Streamlit Application Service
  app:
    build: . # Build the image using the Dockerfile in the current directory (.)
    container_name: streamlit_app
    ports:
      - "8501:8501" # Map host port 8501 to container port 8501
    environment:
      # --- Pass necessary environment variables to the Streamlit app ---
      # Database connection (using service name 'db')
      PG_HOST: db
      PG_PORT: 5432
      PG_USER: ${PG_USER:-user} # Use host env var or default
      PG_PASSWORD: ${PG_PASSWORD:-password} # Use host env var or default
      PG_DB: ${PG_DB:-mydb} # Use host env var or default

      # Qdrant connection (using service name 'qdrant')
      QDRANT_URL: http://qdrant:6333
      QDRANT_COLLECTION_NAME: ${QDRANT_COLLECTION_NAME:-banque_ma_data_catalog}

      # Ollama connection (using service name 'ollama')
      OLLAMA_HOST: http://ollama:11434
      OLLAMA_MODEL_NAME: ${OLLAMA_MODEL_NAME:-llama3:8b}

      # Embedding model
      EMBEDDING_MODEL_NAME: ${EMBEDDING_MODEL_NAME:-paraphrase-multilingual-MiniLM-L12-v2}

      # JWT Secret (CRITICAL: Load from host environment, DO NOT hardcode here)
      JWT_SECRET_KEY: ${JWT_SECRET_KEY?err} # Fails if JWT_SECRET_KEY is not set on host

      # Other config if needed
      NUM_RESULTS_TO_RETRIEVE: ${NUM_RESULTS_TO_RETRIEVE:-10}

      # Streamlit specific environment variables (optional)
      STREAMLIT_SERVER_MAX_UPLOAD_SIZE: 1028 # Increase max upload size if needed (e.g., 1028 MB)

    volumes:
      # Optional: Mount local code for development (comment out for production builds)
      # This allows code changes without rebuilding the image
      - ./app:/app/app
      # Mount ollama models volume if needed by app directly (e.g. embedding model loaded from Ollama?)
      # Usually not needed by the app container itself if Ollama service handles models.
      # Keep if embedding models are stored/loaded via Ollama paths from app.
      #- ollama_data:/root/.ollama

    depends_on:
      db:
        condition: service_healthy # Wait for db to be healthy
      qdrant:
        condition: service_healthy # Wait for qdrant to be healthy
      ollama: # Wait for ollama to start (add condition if healthcheck is available)
        condition: service_started
    restart: unless-stopped
    networks: # Define a network for services to communicate
      - rag_network

  # Qdrant Service (from your existing file)
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant_db
    ports:
      - "6333:6333" # Expose HTTP port to host
      # - "6334:6334" # Expose gRPC port (optional)
    volumes:
      - qdrant_data:/qdrant/storage # Persist Qdrant data
    environment:
      # Qdrant specific config if needed
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY:-} # Example: Allow setting API key via env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - rag_network

  # PostgreSQL Service (from your existing file)
  db:
    image: postgres:14 # Or your preferred postgres version
    container_name: postgres_db
    environment:
      POSTGRES_USER: ${PG_USER:-user}
      POSTGRES_PASSWORD: ${PG_PASSWORD:-password}
      POSTGRES_DB: ${PG_DB:-mydb}
    ports:
      - "5432:5432" # Expose PostgreSQL port to host
    volumes:
      - postgres_data:/var/lib/postgresql/data # Persist PostgreSQL data
      # Optional: Mount init scripts
      # - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${PG_USER:-user} -d ${PG_DB:-mydb}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - rag_network

  # Ollama Service (Added)
  ollama:
    image: ollama/ollama:latest # Use official Ollama image
    container_name: ollama_service
    ports:
      - "11434:11434" # Expose Ollama API port to host
    volumes:
      - ollama_data:/root/.ollama # Persist Ollama models
    # Add GPU support if available and desired (requires nvidia-container-toolkit)
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all # Use 'all' available GPUs
              capabilities: [gpu]
    tty: true # Allocate a TTY for Ollama
    restart: unless-stopped
    networks:
      - rag_network
    # Note: Ollama official images might not have a standard healthcheck yet.
    # 'depends_on' condition 'service_started' might be sufficient.

# Define named volumes for data persistence
volumes:
  qdrant_data:
  postgres_data:
  ollama_data:

# Define the network
networks:
  rag_network:
    driver: bridge
EOF

echo "--- Project Setup Complete ---"
echo ""
echo "Directory 'app' created with Python files."
echo "Dockerfile, requirements.txt, and docker-compose.yml created."
echo ""
echo "Next steps:"
echo "1. Ensure Docker and Docker Compose are installed."
echo "2. Set the JWT_SECRET_KEY environment variable:"
echo "   export JWT_SECRET_KEY='your-very-secure-and-random-secret-key'"
echo "   (Replace with your actual secret key!)"
echo "3. (Optional) Set other environment variables like PG_USER, PG_PASSWORD, etc., if needed."
echo "4. Run 'docker-compose up --build' to build and start the containers."
echo "5. Access the app at http://localhost:8501"
echo "6. (First time only or if model missing) Pull the Ollama model:"
echo "   docker-compose exec ollama ollama pull ${OLLAMA_MODEL_NAME:-llama3:8b}"
echo ""
