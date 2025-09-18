import React, { useState, useEffect, useRef } from 'react';
import './AdvancedAvatarCoach.css';

const AdvancedAvatarCoach = ({ 
  question, 
  onResponse, 
  userLevel = 'beginner',
  enableVoiceInput = true 
}) => {
  // États pour l'avatar et le coaching
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [coachingModule, setCoachingModule] = useState(null);
  const [currentLesson, setCurrentLesson] = useState(0);
  const [quizActive, setQuizActive] = useState(false);
  const [quizResults, setQuizResults] = useState({});
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  
  // Refs pour les éléments media
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);

  // État pour la reconnaissance vocale
  const [voiceSession, setVoiceSession] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);

  // Génération de réponse avatar en temps réel
  const generateAvatarResponse = async (userQuestion) => {
    setIsGenerating(true);
    
    try {
      const formData = new FormData();
      formData.append('question', userQuestion);
      formData.append('user_level', userLevel);
      formData.append('include_coaching', 'true');

      const response = await fetch('/api/avatar/generate-real-time-response', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setCurrentResponse(result);
        
        if (result.coaching_module) {
          setCoachingModule(result.coaching_module);
          setCurrentLesson(0);
        }
        
        // Démarrer la lecture vidéo
        if (videoRef.current && result.video_url) {
          videoRef.current.src = result.video_url;
          videoRef.current.play();
        }
        
        onResponse(result);
      }
    } catch (error) {
      console.error('Erreur génération avatar:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  // Démarrer la reconnaissance vocale
  const startVoiceRecognition = async () => {
    if (!enableVoiceInput) return;
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      
      streamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      setAudioChunks([]);
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks(prev => [...prev, event.data]);
        }
      };
      
      mediaRecorder.onstop = async () => {
        await processVoiceInput();
      };
      
      mediaRecorder.start(100); // Enregistrer par chunks de 100ms
      setIsListening(true);
      
      // Générer un ID de session unique
      setVoiceSession(`voice_${Date.now()}`);
      
    } catch (error) {
      console.error('Erreur accès microphone:', error);
      alert('Impossible d\'accéder au microphone');
    }
  };

  // Arrêter la reconnaissance vocale
  const stopVoiceRecognition = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
  };

  // Traiter l'input vocal
  const processVoiceInput = async () => {
    if (audioChunks.length === 0) return;
    
    try {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'voice_input.webm');
      formData.append('language', 'fr');
      formData.append('include_timestamps', 'true');
      
      const response = await fetch('/api/whisper/transcribe', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        setTranscript(result.text);
        
        // Analyser l'intention et générer une réponse avatar
        if (result.text.trim()) {
          await analyzeAndRespond(result.text);
        }
      }
    } catch (error) {
      console.error('Erreur transcription:', error);
    }
  };

  // Analyser l'intention et répondre
  const analyzeAndRespond = async (spokenText) => {
    try {
      const formData = new FormData();
      formData.append('text', spokenText);
      formData.append('detect_intent', 'true');
      formData.append('extract_keywords', 'true');
      
      const analysisResponse = await fetch('/api/whisper/analyze-speech', {
        method: 'POST',
        body: formData
      });
      
      if (analysisResponse.ok) {
        const analysis = await analysisResponse.json();
        
        // Générer une réponse avatar adaptée
        await generateAvatarResponse(spokenText);
        
        // Si coaching nécessaire, l'activer
        if (analysis.coaching_needed) {
          console.log('Coaching recommandé pour cette question');
        }
      }
    } catch (error) {
      console.error('Erreur analyse vocal:', error);
    }
  };

  // Navigation dans les leçons
  const nextLesson = () => {
    if (coachingModule && currentLesson < coachingModule.lessons.length - 1) {
      setCurrentLesson(currentLesson + 1);
    } else if (coachingModule && coachingModule.quiz.length > 0) {
      setQuizActive(true);
    }
  };

  const previousLesson = () => {
    if (currentLesson > 0) {
      setCurrentLesson(currentLesson - 1);
    }
  };

  // Gestion du quiz
  const submitQuizAnswer = async (questionIndex, selectedAnswer) => {
    try {
      const formData = new FormData();
      formData.append('question_id', questionIndex);
      formData.append('answer', selectedAnswer);
      formData.append('coaching_session_id', voiceSession || 'default');
      
      const response = await fetch('/api/avatar/quiz/submit', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        setQuizResults(prev => ({
          ...prev,
          [questionIndex]: result
        }));
      }
    } catch (error) {
      console.error('Erreur soumission quiz:', error);
    }
  };

  // Effect pour nettoyer les ressources
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Auto-génération si question fournie
  useEffect(() => {
    if (question && question.trim()) {
      generateAvatarResponse(question);
    }
  }, [question]);

  return (
    <div className="advanced-avatar-coach">
      {/* Contrôles vocaux */}
      {enableVoiceInput && (
        <div className="voice-controls">
          <button 
            className={`voice-btn ${isListening ? 'listening' : ''}`}
            onClick={isListening ? stopVoiceRecognition : startVoiceRecognition}
            disabled={isGenerating}
          >
            {isListening ? '🔴 Arrêter' : '🎤 Parler'}
          </button>
          {transcript && (
            <div className="transcript">
              <small>Vous avez dit: "{transcript}"</small>
            </div>
          )}
        </div>
      )}

      {/* Zone avatar principal */}
      <div className="avatar-display">
        {isGenerating ? (
          <div className="generating-state">
            <div className="avatar-placeholder pulse">
              <div className="loading-spinner"></div>
            </div>
            <p>🎭 Création de votre avatar personnalisé...</p>
          </div>
        ) : currentResponse ? (
          <div className="avatar-active">
            <video
              ref={videoRef}
              className="avatar-video"
              controls
              autoPlay
              muted={false}
            />
            <div className="response-info">
              <p className="transcript-text">{currentResponse.transcript}</p>
            </div>
          </div>
        ) : (
          <div className="avatar-idle">
            <div className="avatar-placeholder">👨‍💼</div>
            <p>Posez-moi une question ou utilisez la reconnaissance vocale !</p>
          </div>
        )}
      </div>

      {/* Module de coaching */}
      {coachingModule && !quizActive && (
        <div className="coaching-module">
          <div className="module-header">
            <h3>{coachingModule.title}</h3>
            <span className="duration">⏱️ {coachingModule.duration_minutes} min</span>
          </div>
          
          <div className="lesson-content">
            <div className="lesson-counter">
              Leçon {currentLesson + 1} / {coachingModule.lessons.length}
            </div>
            <div className="lesson-text">
              {coachingModule.lessons[currentLesson]}
            </div>
          </div>
          
          <div className="lesson-navigation">
            <button 
              onClick={previousLesson}
              disabled={currentLesson === 0}
              className="nav-btn prev"
            >
              ⬅️ Précédent
            </button>
            
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{
                  width: `${((currentLesson + 1) / coachingModule.lessons.length) * 100}%`
                }}
              ></div>
            </div>
            
            <button 
              onClick={nextLesson}
              className="nav-btn next"
            >
              {currentLesson < coachingModule.lessons.length - 1 ? 'Suivant ➡️' : 'Quiz 🎯'}
            </button>
          </div>
        </div>
      )}

      {/* Quiz interactif */}
      {quizActive && coachingModule?.quiz && (
        <div className="quiz-section">
          <h3>🎯 Quiz de validation</h3>
          
          {coachingModule.quiz.map((quizQuestion, index) => (
            <div key={index} className="quiz-question">
              <h4>Question {index + 1}</h4>
              <p>{quizQuestion.question}</p>
              
              <div className="quiz-options">
                {quizQuestion.options.map((option, optionIndex) => (
                  <button
                    key={optionIndex}
                    className={`quiz-option ${
                      quizResults[index] ? (
                        optionIndex === quizQuestion.correct_answer ? 'correct' :
                        quizResults[index].correct === false ? 'incorrect' : ''
                      ) : ''
                    }`}
                    onClick={() => submitQuizAnswer(index, optionIndex)}
                    disabled={quizResults[index]}
                  >
                    {option}
                  </button>
                ))}
              </div>
              
              {quizResults[index] && (
                <div className="quiz-feedback">
                  <div className={`feedback ${quizResults[index].correct ? 'success' : 'error'}`}>
                    {quizResults[index].feedback}
                  </div>
                  <div className="explanation">
                    <strong>Explication :</strong> {quizQuestion.explanation}
                  </div>
                </div>
              )}
            </div>
          ))}
          
          <button 
            className="quiz-complete-btn"
            onClick={() => setQuizActive(false)}
          >
            🎓 Terminer la formation
          </button>
        </div>
      )}

      {/* Actions suggérées */}
      {currentResponse?.interactive_elements?.suggested_actions && (
        <div className="suggested-actions">
          <h4>Actions suggérées :</h4>
          <div className="action-buttons">
            {currentResponse.interactive_elements.suggested_actions.map((action, index) => (
              <button key={index} className="action-btn">
                {action}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedAvatarCoach;
