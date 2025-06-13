from sentence_transformers import SentenceTransformer
import os
import time

model_name = 'paraphrase-multilingual-MiniLM-L12-v2'

# --- OPTIONNEL: Spécifier un dossier cache local au projet ---
# cache_dir = os.path.join(os.getcwd(), ".model_cache")
# print(f"Le dossier cache sera : {cache_dir}")
# os.makedirs(cache_dir, exist_ok=True)
# ---------------------------------------------------------

print(f"Tentative de téléchargement/vérification du modèle : {model_name}")
print("Cela peut prendre plusieurs minutes et nécessiter plusieurs centaines de Mo...")
start_time = time.time()
try:
    # Utilisez 'cache_folder=cache_dir' si vous avez décommenté la section optionnelle
    # model = SentenceTransformer(model_name, cache_folder=cache_dir)
    model = SentenceTransformer(model_name) # Utilise le cache par défaut de Hugging Face
    end_time = time.time()
    # Trouve le chemin réel où le modèle a été mis en cache par la bibliothèque
    model_cache_path = model.tokenizer.name_or_path
    print("-" * 50)
    print(f"SUCCÈS ! Modèle téléchargé/vérifié en {end_time - start_time:.2f} secondes.")
    print(f"Le modèle est probablement dans un sous-dossier de : {os.path.expanduser('~/.cache/huggingface/hub')} OU un autre chemin système.")
    print(f"Chemin spécifique trouvé par la bibliothèque : {model_cache_path}")
    print("-" * 50)
    print("Vous pouvez maintenant configurer Docker pour monter ce cache.")

except Exception as e:
    end_time = time.time()
    print("-" * 50)
    print(f"ERREUR après {end_time - start_time:.2f} secondes.")
    print(f"Impossible de télécharger le modèle : {e}")
    print("Vérifiez votre connexion internet et l'absence de pare-feu/VPN bloquant.")
    print("-" * 50)