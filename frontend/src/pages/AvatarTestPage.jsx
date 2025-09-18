import React, { useState, useRef, useEffect } from 'react';
import './AvatarTestPage.css';

const AvatarTestPage = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [token, setToken] = useState(null);
    const [currentQuestion, setCurrentQuestion] = useState('');
    const [avatarResponse, setAvatarResponse] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [testHistory, setTestHistory] = useState([]);
    const [selectedTestType, setSelectedTestType] = useState('kpi');
    const videoRef = useRef(null);
    const audioRef = useRef(null);

    // Questions de test prédéfinies
    const testQuestions = {
        kpi: [
            "Comment mettre à jour un KPI efficacement ?",
            "Quelles sont les bonnes pratiques pour les indicateurs ?",
            "Je veux optimiser mes métriques de performance"
        ],
        data: [
            "Qu'est-ce que la table CLIENT_QT ?",
            "Qui est propriétaire des données bancaires ?",
            "Comment sont structurées les données clients ?",
            "Comment assurer la sécurité des données ?"
        ],
        process: [
            "Comment améliorer nos processus métier ?",
            "Quelles étapes pour automatiser un workflow ?",
            "Comment optimiser la documentation ?"
        ]
    };

    // Authentification automatique
    useEffect(() => {
        const autoLogin = async () => {
            try {
                const response = await fetch('/api/api/v1/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        username: 'admin',
                        password: 'admin123'
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    setToken(data.access_token);
                    setIsAuthenticated(true);
                    console.log('✅ Authentification automatique réussie');
                } else {
                    console.error('❌ Échec authentification');
                }
            } catch (error) {
                console.error('❌ Erreur lors de l\'authentification:', error);
            }
        };

        autoLogin();
    }, []);

    // Fonction pour tester l'avatar
    const testAvatar = async (question, userLevel = 'beginner') => {
        if (!token) {
            alert('Vous devez être connecté pour tester l\'avatar');
            return;
        }

        setIsLoading(true);
        setCurrentQuestion(question);
        
        try {
            console.log(`🧪 Test avatar pour: "${question}"`);
            
            const formData = new FormData();
            formData.append('question', question);
            formData.append('user_level', userLevel);
            formData.append('include_coaching', 'true');
            formData.append('context', 'Test depuis interface web');

            const response = await fetch('/api/avatar/generate-real-time-response', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Réponse avatar reçue:', result);
                
                setAvatarResponse(result);
                
                // Ajouter à l'historique
                const testEntry = {
                    timestamp: new Date().toLocaleTimeString(),
                    question: question,
                    result: result,
                    success: true
                };
                setTestHistory(prev => [testEntry, ...prev]);

            } else {
                console.error('❌ Erreur génération avatar:', response.status);
                const errorText = await response.text();
                console.error(errorText);
                
                setTestHistory(prev => [{
                    timestamp: new Date().toLocaleTimeString(),
                    question: question,
                    error: `Erreur ${response.status}: ${errorText}`,
                    success: false
                }, ...prev]);
            }
        } catch (error) {
            console.error('❌ Erreur réseau:', error);
            setTestHistory(prev => [{
                timestamp: new Date().toLocaleTimeString(),
                question: question,
                error: `Erreur réseau: ${error.message}`,
                success: false
            }, ...prev]);
        } finally {
            setIsLoading(false);
        }
    };

    // Fonction pour jouer la vidéo/audio
    const playAvatarMedia = () => {
        if (avatarResponse) {
            // Simuler la lecture de média
            console.log('🎬 Lecture de l\'avatar:', avatarResponse.video_url);
            alert('🎬 Lecture de l\'avatar simulée!\n\n' + 
                  `Vidéo: ${avatarResponse.video_url}\n` +
                  `Audio: ${avatarResponse.audio_url}\n` +
                  `Transcript: ${avatarResponse.transcript.substring(0, 200)}...`);
        }
    };

    // Fonction pour tester le coaching
    const testCoaching = () => {
        if (avatarResponse?.coaching_module) {
            const module = avatarResponse.coaching_module;
            alert('🎓 Module de coaching détecté!\n\n' +
                  `Titre: ${module.title}\n` +
                  `Durée: ${module.duration_minutes} minutes\n` +
                  `Leçons: ${module.lessons.length}\n` +
                  `Quiz: ${module.quiz.length} questions`);
        } else {
            alert('ℹ️ Aucun module de coaching pour cette réponse');
        }
    };

    return (
        <div className="avatar-test-page">
            <div className="header">
                <h1>🎭 Test Avatar en Temps Réel</h1>
                <div className="status">
                    {isAuthenticated ? (
                        <span className="authenticated">✅ Connecté</span>
                    ) : (
                        <span className="not-authenticated">❌ Non connecté</span>
                    )}
                </div>
            </div>

            <div className="test-container">
                {/* Section de sélection du type de test */}
                <div className="test-type-selector">
                    <h3>📋 Type de test :</h3>
                    <div className="type-buttons">
                        <button 
                            className={selectedTestType === 'kpi' ? 'active' : ''}
                            onClick={() => setSelectedTestType('kpi')}
                        >
                            🎯 KPI & Performance
                        </button>
                        <button 
                            className={selectedTestType === 'data' ? 'active' : ''}
                            onClick={() => setSelectedTestType('data')}
                        >
                            💼 Données Bancaires
                        </button>
                        <button 
                            className={selectedTestType === 'process' ? 'active' : ''}
                            onClick={() => setSelectedTestType('process')}
                        >
                            ⚙️ Processus Métier
                        </button>
                    </div>
                </div>

                {/* Questions prédéfinies */}
                <div className="predefined-questions">
                    <h3>🔥 Tests rapides :</h3>
                    <div className="question-grid">
                        {testQuestions[selectedTestType].map((question, index) => (
                            <button
                                key={index}
                                className="question-button"
                                onClick={() => testAvatar(question)}
                                disabled={isLoading || !isAuthenticated}
                            >
                                {question}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Test personnalisé */}
                <div className="custom-test">
                    <h3>✏️ Test personnalisé :</h3>
                    <div className="custom-input">
                        <input
                            type="text"
                            placeholder="Tapez votre question..."
                            value={currentQuestion}
                            onChange={(e) => setCurrentQuestion(e.target.value)}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter' && !isLoading && isAuthenticated) {
                                    testAvatar(currentQuestion);
                                }
                            }}
                        />
                        <button
                            onClick={() => testAvatar(currentQuestion)}
                            disabled={isLoading || !isAuthenticated || !currentQuestion.trim()}
                            className="test-button"
                        >
                            {isLoading ? '⏳ Test en cours...' : '🚀 Tester'}
                        </button>
                    </div>
                </div>

                {/* Résultats en temps réel */}
                {isLoading && (
                    <div className="loading-indicator">
                        <div className="spinner"></div>
                        <p>🎭 Génération de l'avatar en cours...</p>
                        <p className="current-question">Question: "{currentQuestion}"</p>
                    </div>
                )}

                {/* Affichage des résultats */}
                {avatarResponse && !isLoading && (
                    <div className="avatar-result">
                        <h3>🎬 Résultat Avatar :</h3>
                        <div className="result-content">
                            <div className="media-controls">
                                <button onClick={playAvatarMedia} className="play-button">
                                    ▶️ Jouer l'Avatar
                                </button>
                                {avatarResponse.coaching_module && (
                                    <button onClick={testCoaching} className="coaching-button">
                                        🎓 Voir le Coaching
                                    </button>
                                )}
                            </div>
                            
                            <div className="result-info">
                                <div className="info-item">
                                    <strong>🎥 Vidéo:</strong> {avatarResponse.video_url}
                                </div>
                                <div className="info-item">
                                    <strong>🔊 Audio:</strong> {avatarResponse.audio_url}
                                </div>
                                <div className="info-item">
                                    <strong>📝 Transcript:</strong> 
                                    <div className="transcript">
                                        {avatarResponse.transcript}
                                    </div>
                                </div>
                                {avatarResponse.coaching_module && (
                                    <div className="coaching-info">
                                        <strong>🎓 Coaching:</strong> {avatarResponse.coaching_module.title}
                                        <br />
                                        <small>⏱️ {avatarResponse.coaching_module.duration_minutes} min - {avatarResponse.coaching_module.lessons.length} leçons</small>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Historique des tests */}
                <div className="test-history">
                    <h3>📊 Historique des tests :</h3>
                    <div className="history-list">
                        {testHistory.length === 0 ? (
                            <p className="no-history">Aucun test effectué</p>
                        ) : (
                            testHistory.slice(0, 5).map((entry, index) => (
                                <div key={index} className={`history-item ${entry.success ? 'success' : 'error'}`}>
                                    <div className="history-time">{entry.timestamp}</div>
                                    <div className="history-question">"{entry.question}"</div>
                                    <div className="history-result">
                                        {entry.success ? (
                                            <span className="success-indicator">✅ Succès</span>
                                        ) : (
                                            <span className="error-indicator">❌ {entry.error}</span>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Tests de service */}
            <div className="service-tests">
                <h3>🔧 Tests de service :</h3>
                <div className="service-buttons">
                    <button onClick={() => window.open('/api/health', '_blank')}>
                        🏥 API Health
                    </button>
                    <button onClick={() => window.open('/api/avatar/health', '_blank')}>
                        🎭 Avatar Health  
                    </button>
                    <button onClick={() => window.open('/whisper/health', '_blank')}>
                        🎤 Whisper Health
                    </button>
                    <button onClick={() => window.open('/api/docs', '_blank')}>
                        📚 API Docs
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AvatarTestPage;
