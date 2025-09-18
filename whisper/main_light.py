#!/usr/bin/env python3
"""
Service de transcription audio léger pour les tests
Simule les fonctionnalités Whisper sans les dépendances lourdes
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Configuration
app = FastAPI(
    title="Whisper Transcription Service (Light)",
    description="Service de transcription audio simplifié pour tests",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockWhisperService:
    """Service Whisper simulé pour les tests"""
    
    def __init__(self):
        self.supported_languages = ["fr", "en", "es", "de", "it"]
        # Dictionnaire de reconnaissance des termes bancaires
        self.banking_terms = {
            "client_qt": ["CLIENT_QT", "client qt", "table CLIENT_QT", "base CLIENT_QT"],
            "types_colonnes": ["types de colonnes", "type de colonne", "types des champs", "structure des données"],
            "donnees_bancaires": ["données bancaires", "data bancaire", "informations client", "base de données"],
            "kpi": ["KPI", "indicateur", "performance", "mesure", "métrique"],
            "securite": ["sécurité", "confidentialité", "accès", "protection"],
            "structure": ["structure", "schéma", "format", "organisation"]
        }
    
    def _smart_transcription_simulation(self, audio_data: np.ndarray, duration: float) -> str:
        """Simulation intelligente de transcription basée sur l'analyse audio"""
        # Analyse de l'énergie audio pour détecter le type de question
        energy_level = np.mean(np.abs(audio_data))
        
        # Patterns de transcription basés sur la durée et l'énergie
        if duration < 1:
            return "Bonjour"
        elif duration < 2.5:
            return "CLIENT_QT"
        elif duration < 4:
            # Questions courtes sur les types de données - incluons les variantes mal reconnues
            if energy_level > 0.15:  # Voix plus forte/claire
                return "Je veux savoir les types de colonnes CLIENT_QT"
            else:
                return "Quels sont les types de colande client culant" # Simuler l'erreur pour la corriger
        elif duration < 6:
            return "Quels sont les types de données des colonnes CLIENT_QT dans la base ?"
        elif duration < 8:
            return "Comment connaître la structure et les types de données de la table CLIENT_QT ?"
        else:
            return "Je voudrais obtenir des informations détaillées sur les types de colonnes et la structure de la table CLIENT_QT pour mon analyse."
    
    def _correct_banking_terms(self, text: str) -> str:
        """Correction des erreurs de transcription courantes pour les termes bancaires"""
        corrections = {
            # Variantes de CLIENT_QT
            "cléons": "CLIENT_QT",
            "culon": "CLIENT_QT", 
            "tecs": "CLIENT_QT",
            "client cute": "CLIENT_QT",
            "client cu": "CLIENT_QT",
            "clien qt": "CLIENT_QT",
            "colande": "CLIENT_QT",
            "culant": "CLIENT_QT",
            "client": "CLIENT_QT",
            "cliant": "CLIENT_QT",
            "culent": "CLIENT_QT",
            "colonnes cléons": "colonnes CLIENT_QT",
            "colonnes colande": "colonnes CLIENT_QT", 
            "colonnes culant": "colonnes CLIENT_QT",
            "table cléons": "table CLIENT_QT",
            "table colande": "table CLIENT_QT",
            "table culant": "table CLIENT_QT",
            "type de colande": "types de colonnes CLIENT_QT",
            "types de colande": "types de colonnes CLIENT_QT",
            "types colande": "types de colonnes CLIENT_QT",
            "type colande": "types de colonnes CLIENT_QT",
            "colande client": "colonnes CLIENT_QT",
            "client culant": "CLIENT_QT",
            # Autres termes bancaires
            "donné bancaire": "données bancaires",
            "donné client": "données client",
            "kp i": "KPI",
            "kay pi ay": "KPI",
            "indicateur de performance": "KPI"
        }
        
        corrected_text = text.lower()
        for wrong, correct in corrections.items():
            corrected_text = corrected_text.replace(wrong.lower(), correct)
        
        return corrected_text
        
    async def transcribe_audio(self, audio_file: bytes, language: str = "fr") -> Dict[str, Any]:
        """Transcription simulée d'un fichier audio"""
        try:
            # Analyser le fichier audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_file)
                temp_path = temp_file.name
            
            try:
                # Lire le fichier audio
                data, sample_rate = sf.read(temp_path)
                duration = len(data) / sample_rate
                
                # Simulation de transcription intelligente
                # Analyser le contenu audio pour détecter les termes bancaires
                raw_transcription = self._smart_transcription_simulation(data, duration)
                # Corriger les erreurs de transcription courantes
                transcribed_text = self._correct_banking_terms(raw_transcription)
                
                return {
                    "text": transcribed_text,
                    "language": language,
                    "confidence": 0.95,
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "segments": [
                        {
                            "start": 0.0,
                            "end": duration,
                            "text": transcribed_text,
                            "confidence": 0.95
                        }
                    ]
                }
                
            finally:
                # Nettoyer le fichier temporaire
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Erreur transcription: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur transcription: {e}")
    
    async def analyze_speech_content(self, text: str) -> Dict[str, Any]:
        """Analyse du contenu vocal pour détecter les intentions"""
        text_lower = text.lower()
        
        # Détection d'intention basique
        intent = "general"
        coaching_needed = False
        keywords = []
        
        # Patterns de coaching
        coaching_patterns = [
            "kpi", "indicateur", "performance", "mettre à jour", "optimiser",
            "bonnes pratiques", "comment faire", "améliorer", "gérer"
        ]
        
        # Patterns de données
        data_patterns = [
            "table", "base de données", "client_qt", "données", "propriétaire",
            "structure", "flux", "sécurité", "bancaire"
        ]
        
        # Analyse des mots-clés
        for pattern in coaching_patterns:
            if pattern in text_lower:
                intent = "coaching_request"
                coaching_needed = True
                keywords.append(pattern)
        
        for pattern in data_patterns:
            if pattern in text_lower:
                if intent == "general":
                    intent = "data_inquiry"
                elif intent == "coaching_request":
                    intent = "coaching_data"
                keywords.append(pattern)
        
        return {
            "text": text,
            "intent": intent,
            "coaching_needed": coaching_needed,
            "keywords": keywords,
            "confidence": 0.85,
            "suggested_response_type": "avatar" if coaching_needed else "simple"
        }

# Instance du service
whisper_service = MockWhisperService()

@app.get("/health")
async def health_check():
    """Check de santé du service"""
    return {
        "status": "healthy",
        "service": "whisper-light",
        "version": "1.0.0",
        "supported_languages": whisper_service.supported_languages
    }

@app.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str = Form("fr"),
    include_timestamps: bool = Form(False),
    include_confidence: bool = Form(True)
):
    """Transcription d'un fichier audio"""
    try:
        # Vérifier le type de fichier
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Fichier audio requis")
        
        # Lire le contenu du fichier
        audio_content = await audio_file.read()
        
        # Transcription
        result = await whisper_service.transcribe_audio(audio_content, language)
        
        # Filtrer les résultats selon les options
        if not include_timestamps:
            result.pop('segments', None)
        
        if not include_confidence:
            result.pop('confidence', None)
            for segment in result.get('segments', []):
                segment.pop('confidence', None)
        
        return JSONResponse(content={
            "transcription": result,
            "status": "success"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {e}")

@app.post("/transcribe-stream")
async def transcribe_stream():
    """Endpoint pour transcription en streaming (simulé)"""
    return {
        "message": "Streaming transcription non implémenté dans la version light",
        "status": "not_implemented",
        "alternative": "Utilisez /transcribe pour les fichiers"
    }

@app.post("/analyze-speech")
async def analyze_speech(
    text: str = Form(...),
    detect_intent: bool = Form(True),
    extract_keywords: bool = Form(True)
):
    """Analyse sémantique du contenu vocal"""
    try:
        result = await whisper_service.analyze_speech_content(text)
        
        # Filtrer selon les options
        if not detect_intent:
            result.pop('intent', None)
            result.pop('suggested_response_type', None)
        
        if not extract_keywords:
            result.pop('keywords', None)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Erreur analyse: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur analyse: {e}")

@app.get("/models")
async def list_models():
    """Liste des modèles disponibles (simulé)"""
    return {
        "models": [
            {
                "name": "whisper-light-fr",
                "language": "fr",
                "description": "Modèle français léger pour tests"
            },
            {
                "name": "whisper-light-en", 
                "language": "en",
                "description": "Modèle anglais léger pour tests"
            }
        ],
        "default": "whisper-light-fr"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=False,
        log_level="info"
    )
