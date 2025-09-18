# api/routers/avatar.py
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import httpx
import asyncio
import os
import json
from ..schemas.message import Message
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
import logging
import tempfile
import os
import base64

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/avatar", tags=["avatar"])
security = HTTPBearer()

# === MODÈLES DE DONNÉES POUR LE COACHING ===

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str

class CoachingModule(BaseModel):
    title: str
    description: str
    lessons: List[str]
    quiz: List[QuizQuestion]
    duration_minutes: int

class AvatarResponse(BaseModel):
    video_url: str
    audio_url: str
    transcript: str
    coaching_module: Optional[CoachingModule] = None
    interactive_elements: Optional[Dict[str, Any]] = None

@router.post("/generate-real-time-response", response_model=AvatarResponse)
async def generate_real_time_avatar_response(
    question: str = Form(...),
    context: str = Form(default=""),
    user_level: str = Form(default="beginner"),  # beginner, intermediate, expert
    include_coaching: bool = Form(default=True)
):
    """
    Génère une réponse avatar en temps réel avec voix + visage
    Inclut du coaching automatique selon le type de question
    
    Args:
        question: Question de l'utilisateur
        context: Contexte additionnel 
        user_level: Niveau de l'utilisateur pour adapter le coaching
        include_coaching: Inclure ou non le module de coaching
        
    Returns:
        Réponse complète avec vidéo, audio et éventuellement coaching
    """
    try:
        logger.info(f"Generating real-time avatar response for: {question}")
        
        # 1. Analyser le type de question
        question_type = await _analyze_question_type(question)
        
        # 2. Générer le contenu de base
        base_response = await _generate_base_response(question, context, question_type)
        
        # 3. Ajouter coaching si nécessaire
        coaching_module = None
        if include_coaching and _needs_coaching(question, question_type):
            coaching_module = await _generate_coaching_module(question, question_type, user_level)
        
        # 4. Générer l'audio avec TTS (simulation)
        audio_content = await _generate_tts_audio(base_response, coaching_module)
        
        # 5. Générer la vidéo avec Wav2Lip
        video_path = await _generate_wav2lip_video(audio_content, question_type)
        
        # 6. Préparer les éléments interactifs
        interactive_elements = await _generate_interactive_elements(question_type, coaching_module)
        
        return AvatarResponse(
            video_url=f"/avatar/videos/{os.path.basename(video_path)}",
            audio_url=f"/avatar/audio/{os.path.basename(audio_content)}",
            transcript=base_response,
            coaching_module=coaching_module,
            interactive_elements=interactive_elements
        )
        
    except Exception as e:
        logger.error(f"Error generating real-time avatar response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-data-explanation")
async def generate_data_explanation_avatar(
    question: str = Form(...),
    dataset_context: str = Form(default=""),
    avatar_type: str = Form(default="professional")
):
    """
    Générer une explication avatar pour les questions sur les jeux de données bancaires
    
    Args:
        question: Question sur les données (ex: "Qu'est-ce que la table CLIENT_QT?")
        dataset_context: Contexte additionnel sur le dataset
        avatar_type: Type d'avatar
        
    Returns:
        Fichier vidéo MP4 avec explication avatar
    """
    try:
        logger.info(f"Generating data explanation avatar for: {question}")
        
        # Détecter le type de question et préparer la réponse
        response_text = await _prepare_data_explanation(question, dataset_context)
        
        # Simuler la génération d'avatar
        import tempfile
        temp_dir = tempfile.gettempdir()
        video_path = os.path.join(temp_dir, f"data_explanation_{hash(question) % 10000}.mp4")
        
        with open(video_path, "wb") as f:
            f.write(b"FAKE_DATA_EXPLANATION_VIDEO")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"data_explanation_{hash(question) % 10000}.mp4"
        )
        
    except Exception as e:
        logger.error(f"Error generating data explanation avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _prepare_data_explanation(question: str, context: str = "") -> str:
    """
    Préparer une réponse structurée pour les questions sur les données bancaires
    """
    question_lower = question.lower()
    
    # Réponses prédéfinies pour les questions courantes sur les données bancaires
    if "client_qt" in question_lower or "table client" in question_lower:
        return """La table CLIENT_QT contient les informations quantitatives des clients de la Banque Populaire. 
        Elle inclut les données comme le nombre de comptes, les volumes de transactions, 
        les soldes moyens et les indicateurs de rentabilité par client. 
        Cette table est essentielle pour l'analyse de la performance commerciale et la segmentation clientèle."""
    
    elif "propriétaire" in question_lower or "qui possède" in question_lower:
        return """Les données de la Banque Populaire appartiennent à l'institution financière. 
        La gouvernance des données est assurée par le département Data Management, 
        sous la supervision du Chief Data Officer. 
        Chaque table a un propriétaire métier désigné responsable de la qualité et de l'utilisation des données."""
    
    elif "flux" in question_lower or "dataflow" in question_lower:
        return """Les flux de données suivent une architecture ETL moderne. 
        Les données sources proviennent des systèmes core banking, 
        sont transformées dans notre data lake, 
        puis chargées dans les entrepôts de données pour l'analyse et le reporting."""
    
    elif "format" in question_lower or "structure" in question_lower:
        return """Les données sont structurées selon les standards bancaires. 
        Les formats incluent des tables relationnelles, des fichiers Excel pour les données de référence, 
        et des flux JSON pour les API temps réel. 
        Tous les formats respectent les normes de conformité réglementaire."""
    
    elif "sécurité" in question_lower or "protection" in question_lower:
        return """La sécurité des données est notre priorité absolue. 
        Nous utilisons un chiffrement AES 256 bits, 
        des contrôles d'accès basés sur les rôles, 
        et un monitoring continu des accès. 
        Toutes les données sont anonymisées pour les environnements de test."""
    
    else:
        # Réponse générique pour autres questions
        return f"""Concernant votre question sur {question}, 
        je vous recommande de consulter notre catalogue de données 
        ou de contacter l'équipe Data Management pour plus de détails spécifiques. 
        Nos données bancaires suivent les standards industriels 
        et les réglementations en vigueur."""

@router.get("/types")
async def get_avatar_types():
    """Obtenir la liste des types d'avatar disponibles"""
    return {
        "avatar_types": [
            {
                "id": "professional",
                "name": "Banquier Professionnel",
                "description": "Avatar professionnel pour les explications techniques"
            },
            {
                "id": "friendly", 
                "name": "Assistant Amical",
                "description": "Avatar amical pour les interactions quotidiennes"
            },
            {
                "id": "executive",
                "name": "Dirigeant",
                "description": "Avatar exécutif pour les présentations importantes"
            }
        ]
    }

@router.get("/health")
async def health_check():
    """Health check pour le service avatar"""
    return {"status": "healthy", "service": "avatar_api"}

# === FONCTIONS AUXILIAIRES POUR LE COACHING ET L'AVATAR ===

async def _analyze_question_type(question: str) -> str:
    """Analyse le type de question pour déterminer la stratégie de réponse"""
    question_lower = question.lower()
    
    # Questions sur les données
    if any(keyword in question_lower for keyword in [
        "table", "client_qt", "base de données", "dataset", "données",
        "structure", "colonne", "champ", "propriétaire"
    ]):
        return "data_explanation"
    
    # Questions sur les KPI et bonnes pratiques
    elif any(keyword in question_lower for keyword in [
        "kpi", "indicateur", "métrique", "performance", "mesure",
        "mise à jour", "actualiser", "modifier", "bonnes pratiques"
    ]):
        return "coaching_kpi"
    
    # Questions sur les processus métier
    elif any(keyword in question_lower for keyword in [
        "processus", "workflow", "procédure", "étapes", "comment faire"
    ]):
        return "process_guidance"
    
    # Questions techniques
    elif any(keyword in question_lower for keyword in [
        "api", "code", "technique", "développement", "intégration"
    ]):
        return "technical_help"
    
    else:
        return "general_question"

async def _generate_base_response(question: str, context: str, question_type: str) -> str:
    """Génère la réponse de base selon le type de question"""
    
    if question_type == "data_explanation":
        return await _prepare_data_explanation(question, context)
    
    elif question_type == "coaching_kpi":
        return await _prepare_kpi_coaching_response(question)
    
    elif question_type == "process_guidance":
        return await _prepare_process_guidance(question)
    
    elif question_type == "technical_help":
        return await _prepare_technical_response(question)
    
    else:
        return f"Je comprends votre question sur '{question}'. Laissez-moi vous expliquer cela de manière claire et structurée."

def _needs_coaching(question: str, question_type: str) -> bool:
    """Détermine si la question nécessite un module de coaching"""
    coaching_triggers = [
        "kpi", "mise à jour", "bonnes pratiques", "comment faire",
        "procédure", "optimiser", "améliorer", "formation"
    ]
    
    return (
        question_type in ["coaching_kpi", "process_guidance"] or
        any(trigger in question.lower() for trigger in coaching_triggers)
    )

async def _generate_coaching_module(question: str, question_type: str, user_level: str) -> CoachingModule:
    """Génère un module de coaching interactif"""
    
    if question_type == "coaching_kpi":
        return await _create_kpi_coaching_module(question, user_level)
    elif question_type == "process_guidance":
        return await _create_process_coaching_module(question, user_level)
    else:
        return await _create_general_coaching_module(question, user_level)

async def _create_kpi_coaching_module(question: str, user_level: str) -> CoachingModule:
    """Crée un module de coaching spécifique aux KPI"""
    
    # Adapter le contenu selon le niveau
    if user_level == "beginner":
        lessons = [
            "📊 Qu'est-ce qu'un KPI ? Un indicateur clé de performance mesure l'efficacité d'une action.",
            "🎯 Choisir les bons KPI : SMART (Spécifique, Mesurable, Atteignable, Relevant, Temporel)",
            "📈 Mise à jour régulière : Fréquence selon l'importance (quotidien, hebdomadaire, mensuel)",
            "🔍 Analyse des écarts : Comprendre pourquoi un KPI dévie de son objectif",
            "🚀 Actions correctives : Définir un plan d'action basé sur l'analyse"
        ]
        duration = 5
    else:
        lessons = [
            "📊 KPI avancés : Leading vs Lagging indicators, corrélations multi-factorielles",
            "🎯 Méthodologie Six Sigma : DMAIC pour l'amélioration continue des KPI",
            "📈 Automatisation : Mise en place de tableaux de bord temps réel",
            "🔍 Analyse prédictive : Utiliser l'IA pour anticiper les tendances",
            "🚀 Gouvernance : Framework de validation et d'approbation des KPI"
        ]
        duration = 8
    
    quiz_questions = [
        QuizQuestion(
            question="Quelle est la fréquence recommandée pour mettre à jour un KPI critique ?",
            options=["Une fois par mois", "Une fois par semaine", "Quotidiennement", "En temps réel"],
            correct_answer=3,
            explanation="Les KPI critiques doivent être mis à jour en temps réel pour permettre une réaction rapide."
        ),
        QuizQuestion(
            question="Que signifie l'acronyme SMART pour les KPI ?",
            options=[
                "Simple, Mesurable, Applicable, Rapide, Technique",
                "Spécifique, Mesurable, Atteignable, Relevant, Temporel", 
                "Statistique, Mathématique, Analytique, Rigoureux, Technique",
                "Système, Méthode, Application, Résultat, Total"
            ],
            correct_answer=1,
            explanation="SMART signifie Spécifique, Mesurable, Atteignable, Relevant et Temporel - les critères d'un bon KPI."
        )
    ]
    
    return CoachingModule(
        title="🎯 Maîtriser les KPI Bancaires",
        description="Guide complet pour créer, mettre à jour et optimiser vos indicateurs de performance",
        lessons=lessons,
        quiz=quiz_questions,
        duration_minutes=duration
    )

async def _create_process_coaching_module(question: str, user_level: str) -> CoachingModule:
    """Crée un module de coaching pour les processus métier"""
    
    lessons = [
        "🔄 Cartographie des processus : Identifier les étapes clés et les responsabilités",
        "⚡ Optimisation : Éliminer les redondances et automatiser les tâches répétitives",
        "📋 Documentation : Maintenir une documentation claire et accessible",
        "🎛️ Contrôles qualité : Mettre en place des points de validation",
        "📊 Métriques de suivi : Définir des indicateurs pour mesurer l'efficacité"
    ]
    
    quiz_questions = [
        QuizQuestion(
            question="Quelle est la première étape dans l'optimisation d'un processus ?",
            options=[
                "Automatiser immédiatement",
                "Cartographier le processus existant",
                "Former les équipes",
                "Acheter de nouveaux outils"
            ],
            correct_answer=1,
            explanation="Il faut d'abord comprendre le processus actuel avant de l'améliorer."
        )
    ]
    
    return CoachingModule(
        title="⚙️ Excellence Opérationnelle",
        description="Optimiser vos processus métier pour une efficacité maximale",
        lessons=lessons,
        quiz=quiz_questions,
        duration_minutes=6
    )

async def _create_general_coaching_module(question: str, user_level: str) -> CoachingModule:
    """Module de coaching générique"""
    
    lessons = [
        "💡 Analyse de votre besoin : Comprendre le contexte et les enjeux",
        "🎯 Définition d'objectifs : Clarifier ce que vous voulez accomplir",
        "📚 Bonnes pratiques : Appliquer les standards de l'industrie",
        "🚀 Plan d'action : Étapes concrètes pour atteindre vos objectifs"
    ]
    
    quiz_questions = [
        QuizQuestion(
            question="Quelle est la clé du succès dans tout projet ?",
            options=[
                "Avoir de bons outils",
                "Une planification rigoureuse",
                "Un budget important", 
                "Une équipe nombreuse"
            ],
            correct_answer=1,
            explanation="Une bonne planification est essentielle pour le succès de tout projet."
        )
    ]
    
    return CoachingModule(
        title="🎓 Fondamentaux du Succès",
        description="Les bases pour réussir dans vos projets bancaires",
        lessons=lessons,
        quiz=quiz_questions,
        duration_minutes=4
    )

async def _prepare_kpi_coaching_response(question: str) -> str:
    """Prépare une réponse spécialisée pour les questions KPI"""
    question_lower = question.lower()
    
    if "mise à jour" in question_lower or "actualiser" in question_lower:
        return """
        🎯 **Mise à jour efficace des KPI**
        
        Pour mettre à jour vos KPI de manière optimale :
        
        1. **📊 Fréquence adaptée** : KPI stratégiques (mensuel), opérationnels (hebdomadaire), critiques (temps réel)
        
        2. **🔄 Processus automatisé** : Connecter directement aux sources de données pour éviter les erreurs manuelles
        
        3. **✅ Validation qualité** : Vérifier la cohérence et identifier les anomalies
        
        4. **📈 Analyse contextuelle** : Comprendre les variations et leurs causes
        
        5. **🚀 Actions décisionnelles** : Transformer les insights en actions concrètes
        
        **Conseil pro** : Utilisez un tableau de bord centralisé avec alertes automatiques !
        """
    
    else:
        return """
        📊 **Excellence dans la gestion des KPI**
        
        Les indicateurs de performance sont le cœur de la prise de décision bancaire.
        Voici comment les maîtriser efficacement pour optimiser vos résultats.
        """

async def _prepare_process_guidance(question: str) -> str:
    """Prépare une réponse pour les questions de processus"""
    return """
    ⚙️ **Optimisation des processus métier**
    
    Pour améliorer vos processus bancaires :
    
    - **Cartographie** : Visualiser le flux actuel
    - **Analyse** : Identifier les goulots d'étranglement  
    - **Optimisation** : Éliminer les étapes inutiles
    - **Automatisation** : Digitaliser les tâches répétitives
    - **Monitoring** : Suivre les performances en continu
    """

async def _prepare_technical_response(question: str) -> str:
    """Prépare une réponse technique"""
    return """
    🔧 **Support technique expert**
    
    Je vais vous guider étape par étape pour résoudre votre problématique technique.
    Appliquons les meilleures pratiques de développement et d'intégration.
    """

async def _generate_tts_audio(text: str, coaching_module: Optional[CoachingModule]) -> str:
    """Génère l'audio TTS pour la réponse et le coaching"""
    
    # Construire le script audio complet
    full_script = text
    
    if coaching_module:
        full_script += f"\n\nMaintenant, commençons votre module de formation : {coaching_module.title}. "
        full_script += f"Ce module dure environ {coaching_module.duration_minutes} minutes. "
        
        for i, lesson in enumerate(coaching_module.lessons, 1):
            full_script += f"\n\nLeçon {i}: {lesson}"
    
    # Simulation de génération TTS
    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, f"avatar_audio_{hash(full_script) % 10000}.wav")
    
    # Créer un fichier audio factice
    with open(audio_path, "wb") as f:
        f.write(b"FAKE_AUDIO_DATA_TTS")
    
    logger.info(f"Generated TTS audio: {len(full_script)} characters")
    return audio_path

async def _generate_wav2lip_video(audio_path: str, question_type: str) -> str:
    """Génère la vidéo avec synchronisation labiale Wav2Lip"""
    
    # Choisir l'avatar selon le type de question
    avatar_type = "professional" if question_type in ["data_explanation", "technical_help"] else "friendly"
    
    temp_dir = tempfile.gettempdir()
    video_path = os.path.join(temp_dir, f"avatar_video_{hash(audio_path) % 10000}.mp4")
    
    # Simulation de génération Wav2Lip
    with open(video_path, "wb") as f:
        f.write(b"FAKE_WAV2LIP_VIDEO_DATA")
    
    logger.info(f"Generated Wav2Lip video with {avatar_type} avatar")
    return video_path

async def _generate_interactive_elements(question_type: str, coaching_module: Optional[CoachingModule]) -> Dict[str, Any]:
    """Génère les éléments interactifs pour l'interface"""
    
    elements = {
        "has_quiz": coaching_module is not None,
        "question_type": question_type,
        "suggested_actions": []
    }
    
    if question_type == "coaching_kpi":
        elements["suggested_actions"] = [
            "📊 Créer un nouveau KPI",
            "📈 Analyser les tendances",
            "🎯 Définir des objectifs",
            "📋 Générer un rapport"
        ]
    elif question_type == "data_explanation":
        elements["suggested_actions"] = [
            "🔍 Explorer les données",
            "📁 Télécharger l'échantillon",
            "📊 Voir la structure complète",
            "🔗 APIs disponibles"
        ]
    
@router.post("/quiz/submit")
async def submit_quiz_answer(
    question_id: int = Form(...),
    answer: int = Form(...),
    coaching_session_id: str = Form(...)
):
    """Soumet une réponse de quiz et retourne le feedback"""
    
    # Ici on pourrait stocker les résultats en base
    # Pour la démo, on simule une validation
    
    is_correct = True  # Simulation
    feedback = "Excellente réponse ! Vous maîtrisez bien ce concept." if is_correct else "Pas tout à fait. Revoyons ce point ensemble."
    
    return {
        "correct": is_correct,
        "feedback": feedback,
        "explanation": "Les KPI doivent être mis à jour selon leur criticité.",
        "next_action": "continue_course" if is_correct else "review_lesson"
    }

@router.get("/videos/{filename}")
async def serve_video(filename: str):
    """Sert les fichiers vidéo générés"""
    temp_dir = tempfile.gettempdir()
    video_path = os.path.join(temp_dir, filename)
    
    if os.path.exists(video_path):
        return FileResponse(video_path, media_type="video/mp4")
    else:
        raise HTTPException(status_code=404, detail="Video not found")

@router.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Sert les fichiers audio générés"""
    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, filename)
    
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/wav")
    else:
        raise HTTPException(status_code=404, detail="Audio not found")

@router.post("/stream-response")
async def stream_avatar_response(
    question: str = Form(...),
    include_coaching: bool = Form(default=True)
):
    """Stream une réponse avatar en temps réel"""
    
    async def generate_stream():
        # 1. Analyse initiale
        yield f"data: {json.dumps({'type': 'analysis', 'content': 'Analyse de votre question...'})}\n\n"
        await asyncio.sleep(0.5)
        
        # 2. Génération du contenu
        yield f"data: {json.dumps({'type': 'generation', 'content': 'Génération de la réponse...'})}\n\n"
        await asyncio.sleep(1)
        
        # 3. Création de l'avatar
        yield f"data: {json.dumps({'type': 'avatar', 'content': 'Création de votre avatar personnalisé...'})}\n\n"
        await asyncio.sleep(1.5)
        
        # 4. Résultat final
        result = {
            'type': 'complete',
            'video_url': '/avatar/videos/demo_response.mp4',
            'transcript': 'Voici votre réponse complète avec avatar...',
            'has_coaching': include_coaching
        }
        yield f"data: {json.dumps(result)}\n\n"
    
    return StreamingResponse(
        generate_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
