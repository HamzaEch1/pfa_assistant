# api/schemas/admin.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime

from .user import User # Import base User schema for response

# --- User Management Schemas ---

# Schema for viewing users in the admin panel (extends base User)
class UserAdminView(User):
    created_at: Optional[datetime.datetime] = None

# --- Feedback Schemas ---

class FeedbackEntry(BaseModel):
    # Replicate structure from admin_logic.py get_all_feedback
    utilisateur: str = Field(..., alias='Utilisateur')
    id_conversation: str = Field(..., alias='ID Conversation')
    date_conversation: datetime.datetime = Field(..., alias='Date Conversation')
    index_message: int = Field(..., alias='Index Message')
    message_assistant: str = Field(..., alias='Message Assistant')
    question_utilisateur: Optional[str] = Field(None, alias='Question Utilisateur')
    feedback_note: Optional[str] = Field(None, alias='Feedback Note') # 'up' or 'down'
    categorie_probleme: Optional[str] = Field(None, alias='Catégorie Problème')
    details_feedback: Optional[str] = Field(None, alias='Détails Feedback')
    id_utilisateur: int = Field(..., alias='ID Utilisateur')

    class Config:
        from_attributes = True
        populate_by_name = True # Allow using aliases for field names

# --- Catalog Schemas ---

class CatalogInfoResponse(BaseModel):
    collection_name: str
    points_count: Optional[int] = None
    vectors_dimension: Optional[int] = None
    # Add other relevant info if needed

class CatalogUploadResponse(BaseModel):
    filename: str
    message: str = "File received and background processing started."

# --- Config Schemas ---
class AdminConfigResponse(BaseModel):
    admin_email: Optional[str] = None
    # authorized_emails: List[str] = [] # Add if implementing authorized emails

class UpdateAdminEmailRequest(BaseModel):
    new_email: str

# Ce tableau doit être cohérent avec celui dans frontend/src/pages/ChatPage.jsx
PREDEFINED_FEEDBACK_PROBLEMS = [
    "Information incorrecte",
    "Réponse pas claire",
    "Ne répond pas à la question",
    "Contenu offensant",
    "Autre"
]

def parse_feedback_comment_for_admin(raw_comment: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Analyse le commentaire brut du feedback (tel que sauvegardé dans FeedbackData.comment)
    pour le décomposer en catégorie de problème et commentaire détaillé pour l'affichage admin.

    Retourne:
        tuple[Optional[str], Optional[str]]: (categorie_probleme, details_feedback)
    """
    if not raw_comment:
        return None, None

    # 1. Vérifier si le commentaire correspond exactement à un problème prédéfini (sans détails supplémentaires)
    for problem in PREDEFINED_FEEDBACK_PROBLEMS:
        if problem == "Autre":  # "Autre" sera géré spécifiquement
            continue
        if raw_comment == problem:
            return problem, None  # La catégorie est le problème, pas de détails

    # 2. Vérifier si le commentaire commence par "Problème: Détails"
    for problem in PREDEFINED_FEEDBACK_PROBLEMS:
        if problem == "Autre":
            continue
        prefix = problem + ":"
        if raw_comment.startswith(prefix):
            details = raw_comment[len(prefix):].strip()
            return problem, details if details else None # La catégorie est le problème, le reste sont les détails

    # 3. Si "Autre" était le problème sélectionné sur le frontend,
    #    raw_comment est directement le commentaire détaillé.
    if "Autre" in PREDEFINED_FEEDBACK_PROBLEMS:
        # Note : si le commentaire détaillé commence lui-même par un autre nom de problème+':' (ex: "Information incorrecte: ..."),
        # il aurait été attrapé par la boucle précédente. Donc ici, c'est bien le commentaire libre pour "Autre".
        return "Autre", raw_comment

    # 4. Fallback: si le commentaire ne correspond à aucun des cas ci-dessus
    #    (par exemple, un ancien format ou une structure inattendue)
    return None, raw_comment

def votre_fonction_pour_obtenir_les_feedbacks_admin() -> List[FeedbackEntry]:
    liste_des_feedbacks_pour_admin = []
    
    # ... votre code existant pour récupérer les conversations, utilisateurs, messages ...

    # Dans votre boucle qui traite chaque message avec feedback:
    # for ... :
        # if message_assistant_a_un_feedback_down:
        #     raw_comment = feedback_details_du_message.comment
        #
        #     categorie_parsee, details_parses = None, None
        #     if raw_comment:
        #          # ICI EST L'APPEL CRUCIAL :
        #          categorie_parsee, details_parses = parse_feedback_comment_for_admin(raw_comment)
        #
        #     nouvelle_entree_feedback = FeedbackEntry(
        #         # ... autres champs ...
        #         categorie_probleme=categorie_parsee,  # <--- Utilisation du résultat
        #         details_feedback=details_parses,    # <--- Utilisation du résultat
        #         # ... autres champs ...
        #     )
        #     liste_des_feedbacks_pour_admin.append(nouvelle_entree_feedback)

    return liste_des_feedbacks_pour_admin