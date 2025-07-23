// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { chatService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // Importer axios pour isCancel
import { FiRefreshCcw, FiSquare, FiTrash2, FiThumbsUp, FiThumbsDown, FiCopy, FiHelpCircle, FiBarChart2, FiVolume2 } from "react-icons/fi"; // Import de l'icône de relance, FiSquare et FiTrash2, FiThumbsUp, FiThumbsDown, FiCopy, FiHelpCircle, FiBarChart2, FiVolume2
import DOMPurify from 'dompurify'; // Import DOMPurify pour la sanitisation HTML
import Joyride, { STATUS } from 'react-joyride';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]); // Messages for the current conversation
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false); // For message sending/loading
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null); // Ref to scroll to bottom
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileUploading, setFileUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState({});
  const [lastUsedFileId, setLastUsedFileId] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // <-- State for sidebar visibility
  const [feedbackState, setFeedbackState] = useState({}); // <-- State for feedback { [msgIndex]: 'up' | 'down' }
  const [currentAbortController, setCurrentAbortController] = useState(null); // <-- State for AbortController

  // NEW: State for detailed feedback form
  const [detailedFeedbackOpenFor, setDetailedFeedbackOpenFor] = useState(null); // msgIndex or null
  const [detailedFeedbackProblem, setDetailedFeedbackProblem] = useState('');
  const [detailedFeedbackComment, setDetailedFeedbackComment] = useState('');

  // NEW: State for copy confirmation
  const [copiedMessageIndex, setCopiedMessageIndex] = useState(null);

  // NEW: State for Joyride tour
  const [runTour, setRunTour] = useState(false);
  const [tourSteps, setTourSteps] = useState([]);

  const [showStats, setShowStats] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Ajouter un nouvel état pour suivre si c'est une nouvelle conversation
  const [isNewConversation, setIsNewConversation] = useState(false);

  // NEW: Add state for currently speaking message
  const [speakingMessageIndex, setSpeakingMessageIndex] = useState(null);
  const speechSynthRef = useRef(null);
  const audioRef = useRef(null); // For audio element fallback
  
  // NEW: Add state for available voices
  const [voices, setVoices] = useState([]);
  const [voicesLoaded, setVoicesLoaded] = useState(false);
  const [useTextToSpeechAPI, setUseTextToSpeechAPI] = useState(true);

  const PREDEFINED_FEEDBACK_PROBLEMS = [
    "Information incorrecte",
    "Réponse pas claire",
    "Ne répond pas à la question",
    "Contenu offensant",
    "Autre"
  ];

  // Function to use a fallback text-to-speech approach using a TTS API service
  const useTextToSpeechFallback = async (text) => {
    try {
      // Clean up text first
      const cleanText = text.replace(/<[^>]*>/g, ' ').substring(0, 500);
      console.log("Using text-to-speech API fallback with text:", cleanText.substring(0, 100) + "...");
      
      // Create new Audio element if needed
      if (!audioRef.current) {
        audioRef.current = new Audio();
      }
      
      // Stop any currently playing audio
      if (!audioRef.current.paused) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      
      // Try using the VoiceRSS API or similar (demo mode)
      const encodedText = encodeURIComponent(cleanText);
      const language = 'fr-fr';
      
      // The Google TTS endpoint - note this is not officially supported and has limitations
      // This would need to be replaced with a proper TTS API in production
      const url = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${language}&client=tw-ob&q=${encodedText}`;
      
      console.log("TTS API URL:", url);
      
      // Set up audio event handlers
      audioRef.current.onplay = () => {
        console.log("Audio started playing");
      };
      
      audioRef.current.onended = () => {
        console.log("Audio finished playing");
        setSpeakingMessageIndex(null);
      };
      
      audioRef.current.onerror = (e) => {
        console.error("Audio error:", e);
        setError("Erreur lors de la lecture audio");
        setSpeakingMessageIndex(null);
      };
      
      // Set the source and play
      audioRef.current.src = url;
      const playPromise = audioRef.current.play();
      
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log("Audio playing successfully");
          })
          .catch(err => {
            console.error("Failed to play audio:", err);
            setError("Impossible de lire l'audio. Cela peut être dû à des restrictions du navigateur.");
            setSpeakingMessageIndex(null);
          });
      }
      
      return true;
    } catch (error) {
      console.error("TTS API fallback error:", error);
      setError(`Erreur API TTS: ${error.message}`);
      return false;
    }
  };

  // NEW: Load voices when speech synthesis is available
  useEffect(() => {
    // Function to load voices
    const loadVoices = () => {
      if (window.speechSynthesis) {
        const availableVoices = window.speechSynthesis.getVoices();
        if (availableVoices && availableVoices.length > 0) {
          console.log("Voices loaded:", availableVoices.length);
          setVoices(availableVoices);
          setVoicesLoaded(true);
        }
      }
    };

    // Initial load attempt
    loadVoices();

    // Some browsers require the voiceschanged event to access voices
    if (window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    // Cleanup
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  // NEW: Setup Joyride tour steps
  useEffect(() => {
    // Define tour steps
    const steps = [
      {
        target: '.conversation-list',
        content: 'Ici vous pouvez voir l\'historique de vos conversations. Cliquez sur une conversation pour l\'ouvrir.',
        disableBeacon: true,
      },
      {
        target: '.new-chat-button',
        content: 'Cliquez ici pour démarrer une nouvelle conversation avec l\'assistant.',
      },
      {
        target: '.message-input',
        content: 'Saisissez vos messages ici pour interagir avec l\'assistant IA.',
      },
      {
        target: '.file-upload',
        content: 'Vous pouvez télécharger des fichiers Excel ici pour que l\'IA puisse les analyser.',
      },
      {
        target: '.feedback-buttons',
        content: 'Donnez votre avis sur les réponses de l\'IA pour aider à améliorer le système.',
      },
      {
        target: '.copy-button',
        content: 'Copiez n\'importe quelle réponse de l\'IA dans votre presse-papiers en un clic.',
      },
      {
        target: '.stats-button',
        content: 'Visualisez les statistiques et analyses des données de vos conversations.',
        placement: 'left',
      }
    ];
    
    setTourSteps(steps);

    // Check if this is the user's first visit
    const hasCompletedTour = localStorage.getItem('hasCompletedTour');
    if (!hasCompletedTour) {
      // Set timeout to allow the UI to fully render first
      setTimeout(() => {
        setRunTour(true);
      }, 1000);
    }
  }, []);

  // Handle tour callbacks
  const handleJoyrideCallback = (data) => {
    const { status } = data;
    
    if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
      // Set tour as completed in localStorage
      localStorage.setItem('hasCompletedTour', 'true');
      setRunTour(false);
    }
  };

  // Function to scroll to the bottom of the messages list
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Fetch conversations on component mount
  useEffect(() => {
    const fetchConversations = async () => {
      setIsLoading(true); // Indicate loading conversations
      try {
        setError('');
        const response = await chatService.getConversations();
        // Sort by timestamp descending if not already sorted by API
        const sortedConvos = response.data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        setConversations(sortedConvos);
        // Load the latest conversation automatically if none selected
        if (sortedConvos.length > 0 && !currentConversationId) {
           selectConversation(sortedConvos[0].id);
        } else if (sortedConvos.length === 0) {
            setCurrentConversationId(null); // Ensure no convo selected if list is empty
            setMessages([]);
        }
      } catch (err) {
        console.error("Failed to fetch conversations:", err);
        setError('Could not load conversations.');
        if (err.response?.status === 401) logout();
      } finally {
        setIsLoading(false);
      }
    };
    fetchConversations();
  }, [logout]); // Removed currentConversationId


  // Fetch messages when a conversation is selected
  useEffect(() => {
    const fetchMessages = async () => {
      if (!currentConversationId) {
        setMessages([]); // Clear messages if no conversation selected
        setLastUsedFileId(null); // Clear last used file
        return;
      }
      setIsLoading(true); // Indicate loading messages
      setError('');
      try {
        const response = await chatService.getConversation(currentConversationId);
        setMessages(response.data.messages || []);
        
        // Update uploaded files for this conversation
        if (response.data.files && response.data.files.length > 0) {
          const filesMap = {};
          response.data.files.forEach(file => {
            filesMap[file.id] = file;
          });
          setUploadedFiles(filesMap);
        } else {
          setUploadedFiles({});
        }
        // Reset feedback states when conversation changes
        setFeedbackState({});
        setDetailedFeedbackOpenFor(null);
        setDetailedFeedbackProblem('');
        setDetailedFeedbackComment('');

      } catch (err) {
        console.error("Failed to fetch messages:", err);
        setError(`Could not load messages.`);
         if (err.response?.status === 401) logout();
      } finally {
        setIsLoading(false);
      }
    };
    fetchMessages();
  }, [currentConversationId, logout]); // Re-run when conversation ID changes


  // Scroll to bottom whenever messages update
  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const selectConversation = (id) => {
    if (id !== currentConversationId) {
        setCurrentConversationId(id);
        setLastUsedFileId(null); // Reset last used file when switching conversations
    }
  };

  const handleNewConversation = async () => {
    // Check if current conversation is empty
    if (currentConversationId && messages.length === 0) {
        console.log("Current conversation is empty, not creating a new one.");
        return;
    }

    setIsLoading(true);
    setError('');
    try {
        const response = await chatService.startConversation();
        const newConv = response.data;
        setConversations(prev => [newConv, ...prev].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
        setCurrentConversationId(newConv.id);
        setMessages([]);
        setLastUsedFileId(null);
        setIsNewConversation(true); // Marquer comme nouvelle conversation
    } catch (err) {
        console.error("Failed to start new conversation:", err);
        setError('Could not start a new conversation.');
        if (err.response?.status === 401) logout();
    } finally {
        setIsLoading(false);
    }
};

  const handleDeleteConversation = async (idToDelete, e) => {
      e.stopPropagation(); // Prevent conversation selection when clicking delete
      if (!window.confirm("Are you sure you want to delete this conversation?")) {
          return;
      }
      try {
          await chatService.deleteConversation(idToDelete);
          // Remove from state and select the next newest one if the current was deleted
          let nextConversationId = null;
          const remainingConvos = conversations.filter(conv => conv.id !== idToDelete);
          setConversations(remainingConvos);

          if (currentConversationId === idToDelete) {
              if (remainingConvos.length > 0) {
                  // Sort remaining to find the newest
                  nextConversationId = remainingConvos.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0].id;
              }
              setCurrentConversationId(nextConversationId); // Select next newest or null
              setMessages([]); // Clear messages
              setLastUsedFileId(null); // Clear last used file
          }
      } catch (err) {
          console.error("Failed to delete conversation:", err);
          setError('Could not delete conversation.');
          if (err.response?.status === 401) logout();
      }
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    } else {
      setSelectedFile(null);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile || !currentConversationId || fileUploading) {
      return;
    }

    // Validate file type
    if (!selectedFile.name.endsWith('.xlsx')) {
      setError('Only Excel files (.xlsx) are allowed.');
      return;
    }

    setFileUploading(true);
    setError('');

    try {
      const response = await chatService.uploadExcelFile(currentConversationId, selectedFile);
      const { file_id, filename } = response.data;
      
      // Update uploaded files with new file
      setUploadedFiles(prev => ({
        ...prev,
        [file_id]: {
          id: file_id,
          filename: filename,
          upload_date: new Date().toISOString(),
          user_id: user.user_id,
          conversation_id: currentConversationId
        }
      }));
      
      setSelectedFile(null);
      
      // Auto-set as the file to use
      setLastUsedFileId(file_id);
      
      // Update conversation in list to show it has files
      const updatedConvResponse = await chatService.getConversation(currentConversationId);
      setConversations(prevConvos => 
        prevConvos.map(conv => conv.id === currentConversationId ? updatedConvResponse.data : conv)
      );
      
    } catch (err) {
      console.error("Failed to upload file:", err);
      setError('Failed to upload file. Please try again.');
      if (err.response?.status === 401) logout();
    } finally {
      setFileUploading(false);
    }
  };

  const handleSelectFile = (fileId) => {
    setLastUsedFileId(fileId === lastUsedFileId ? null : fileId);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || isLoading || !currentConversationId) return;

    if (currentAbortController) {
        currentAbortController.abort();
    }
    const controller = new AbortController();
    setCurrentAbortController(controller);

    const userMessage = { role: 'user', content: newMessage, file_id: lastUsedFileId };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = newMessage;
    setNewMessage('');
    setIsLoading(true);
    setError('');
    setIsNewConversation(false); // Réinitialiser l'état de nouvelle conversation

    try {
        const response = await chatService.sendMessage({
            prompt: userMessage.content,
            conversation_id: currentConversationId,
            file_id: lastUsedFileId
        }, controller.signal);

        const assistantMessage = response.data.assistant_message;
        setMessages(prev => [...prev, assistantMessage]);

        const updatedConvResponse = await chatService.getConversation(currentConversationId);
        const updatedConvData = updatedConvResponse.data;
        if (updatedConvData) {
            setConversations(prevConvos => prevConvos.map(conv =>
                conv.id === currentConversationId ? updatedConvData : conv
            ).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
        }
    } catch (err) {
        if (axios.isCancel(err)) {
            console.log('Request canceled:', err.message);
            setMessages(prev => prev.filter(msg => msg !== userMessage));
            setNewMessage(currentInput);
        } else {
            console.error("Failed to send message:", err);
            setError('Failed to send message. Please try again.');
            setNewMessage(currentInput);
            setMessages(prev => prev.filter(msg => msg !== userMessage));
            if (err.response?.status === 401) logout();
        }
    } finally {
        setIsLoading(false);
        setCurrentAbortController(null);
        setTimeout(scrollToBottom, 50);
    }
};

  const handleResendMessage = async (contentToResend, fileIdToResend) => {
    if (!contentToResend.trim() || isLoading || !currentConversationId) return;

    // Si une requête est déjà en cours et qu'un AbortController existe, l'annuler avant d'en envoyer une nouvelle.
    if (currentAbortController) {
      currentAbortController.abort();
    }
    const controller = new AbortController();
    setCurrentAbortController(controller);

    const userMessage = { role: 'user', content: contentToResend, file_id: fileIdToResend };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError('');

    try {
      const response = await chatService.sendMessage({
        prompt: userMessage.content,
        conversation_id: currentConversationId,
        file_id: userMessage.file_id 
      }, controller.signal); // Passer le signal

      const assistantMessage = response.data.assistant_message;
      setMessages(prev => [...prev, assistantMessage]);

      // Update conversation list timestamp/title
      const updatedConvResponse = await chatService.getConversation(currentConversationId);
      const updatedConvData = updatedConvResponse.data;
      if (updatedConvData) {
            setConversations(prevConvos => prevConvos.map(conv =>
                conv.id === currentConversationId ? updatedConvData : conv
            ).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))); // Re-sort
       }

    } catch (err) {
      if (axios.isCancel(err)) {
        console.log('Request canceled:', err.message);
        // Optionnel: Mettre à jour l'état pour indiquer l'annulation
        // setError('La requête a été annulée.');
        // Restaurer le message utilisateur si l'envoi a été annulé
        setMessages(prev => prev.filter(msg => msg !== userMessage));

      } else {
        console.error("Failed to resend message:", err);
        setError('Failed to resend message. Please try again.');
        // Remove optimistic user message on error
        setMessages(prev => prev.filter(msg => msg !== userMessage));
         if (err.response?.status === 401) logout();
      }
    } finally {
      setIsLoading(false);
      setCurrentAbortController(null); // Nettoyer le controller
       setTimeout(scrollToBottom, 50);
    }
  };

  const handleFeedbackSubmit = async (msgIndex, rating) => {
    if (!currentConversationId) return;

    if (rating === 'up') {
      const newRating = feedbackState[msgIndex] === 'up' ? null : 'up';
      // Optimistically update UI
      setFeedbackState(prev => ({ ...prev, [msgIndex]: newRating }));
      setDetailedFeedbackOpenFor(null); // Close detailed form if it was open for this message

      if (newRating) { // Only send to backend if we are setting a rating (not clearing)
        try {
          await chatService.submitFeedback(currentConversationId, msgIndex, { rating: newRating });
        } catch (error) {
          console.error("Failed to submit 'up' feedback:", error);
          // Revert UI state
          const oldRating = feedbackState[msgIndex]; // Get the current state before optimistic update
          setFeedbackState(prev => ({ ...prev, [msgIndex]: oldRating === 'up' ? null : 'up' })); 
          setError('Failed to submit feedback.');
        }
      } else {
        // If newRating is null, it means we are clearing the 'up' vote.
        console.log(`Feedback 'up' cleared for message ${msgIndex}`);
      }
    } else if (rating === 'down') {
      // Automatically open the detailed feedback form
      setDetailedFeedbackOpenFor(msgIndex);
      setDetailedFeedbackProblem(PREDEFINED_FEEDBACK_PROBLEMS[0]); // Default problem
      setDetailedFeedbackComment(''); // Clear previous comment
      
      // If 'up' was selected, clear it from UI
      if (feedbackState[msgIndex] === 'up') {
        setFeedbackState(prev => ({ ...prev, [msgIndex]: null }));
      }
      
      // Scroll to the feedback form
      setTimeout(() => {
        const feedbackForm = document.getElementById(`feedback-problem-${msgIndex}`);
        if (feedbackForm) {
          feedbackForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  };

  const handleDetailedFeedbackFormSubmit = async (e) => {
    e.preventDefault();
    if (detailedFeedbackOpenFor === null || !currentConversationId) return;

    const feedbackPayload = {
      rating: 'down',
      comment: detailedFeedbackProblem === "Autre" 
        ? detailedFeedbackComment // If "Autre", comment is primary
        : `${detailedFeedbackProblem}${detailedFeedbackComment ? ': ' + detailedFeedbackComment : ''}` // Combine problem and comment
    };
    
    // Ensure comment is not empty if "Autre" is selected and comment is required
    if (detailedFeedbackProblem === "Autre" && !detailedFeedbackComment.trim()) {
        setError("Veuillez préciser la nature du problème dans le champ commentaire.");
        return;
    }

    const originalFeedbackStateForMessage = feedbackState[detailedFeedbackOpenFor];
    // Optimistically update UI to show 'down' thumb selected
    setFeedbackState(prev => ({ ...prev, [detailedFeedbackOpenFor]: 'down' }));

    try {
      await chatService.submitFeedback(currentConversationId, detailedFeedbackOpenFor, feedbackPayload);
      setDetailedFeedbackOpenFor(null); // Close form on successful submission
      setError(''); // Clear any previous error
    } catch (error) {
      console.error("Failed to submit detailed feedback:", error);
      // Revert UI state on error
      setFeedbackState(prev => ({ ...prev, [detailedFeedbackOpenFor]: originalFeedbackStateForMessage }));
      setError('Failed to submit detailed feedback.');
    }
  };
  
  const handleCancelDetailedFeedback = () => {
    setDetailedFeedbackOpenFor(null);
  };

  // NEW: Function to handle copying message content
  const handleCopyMessage = async (contentToCopy, msgIndex) => {
    if (!navigator.clipboard) {
      // Clipboard API not available (e.g., insecure context, old browser)
      setError("La copie dans le presse-papiers n'est pas disponible sur ce navigateur ou cette connexion.");
      return;
    }
    try {
      // Convertir le HTML en texte pur
      let textContent = contentToCopy;
      if (contentToCopy.includes('<')) {
        // Créer un élément div temporaire pour extraire le texte
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = contentToCopy;
        textContent = tempDiv.textContent || tempDiv.innerText || contentToCopy;
      }
      
      await navigator.clipboard.writeText(textContent);
      setCopiedMessageIndex(msgIndex); // Show confirmation for this message
      setTimeout(() => {
        setCopiedMessageIndex(null); // Hide confirmation after 2 seconds
      }, 2000);
    } catch (err) {
      console.error('Failed to copy message: ', err);
      setError('Impossible de copier le message.');
    }
  };

  // NEW: Function to handle text-to-speech
  const handleTextToSpeech = async (content, msgIndex) => {
    // If already speaking this message, stop it
    if (speakingMessageIndex === msgIndex) {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      
      // Also stop audio fallback if active
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      
      setSpeakingMessageIndex(null);
      return;
    }
    
    // If speaking a different message, cancel it first
    if (speakingMessageIndex !== null) {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      
      // Also stop audio fallback if active
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    }
    
    // Set the speaking message index first so UI shows activity
    setSpeakingMessageIndex(msgIndex);
    
    // Convert HTML to plain text if needed
    let textContent = content;
    if (content.includes('<')) {
      // Create a temp div to extract text
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = content;
      textContent = tempDiv.textContent || tempDiv.innerText || content;
    }
    
    // If using the API fallback approach
    if (!useTextToSpeechAPI) {
      const success = await useTextToSpeechFallback(textContent);
      if (!success) {
        setSpeakingMessageIndex(null);
      }
      return;
    }
    
    // Check if speech synthesis is available
    if (!window.speechSynthesis) {
      console.log("SpeechSynthesis not available, trying fallback");
      const success = await useTextToSpeechFallback(textContent);
      if (!success) {
        setSpeakingMessageIndex(null);
        setError("La synthèse vocale n'est pas disponible sur ce navigateur.");
      }
      return;
    }
    
    try {
      // Truncate text if it's too long (some browsers have limits)
      if (textContent.length > 4000) {
        textContent = textContent.substring(0, 4000) + "... (texte tronqué pour la lecture vocale)";
        console.log("Text truncated for speech synthesis - length was over 4000 characters");
      }
      
      // Further shorten for testing if still having issues
      if (textContent.length > 500) {
        const shortenedText = textContent.substring(0, 500) + "... (texte très raccourci pour le test)";
        console.log("Using shortened text for troubleshooting");
        
        // Try with an ultra short test message first
        const testUtterance = new SpeechSynthesisUtterance("Ceci est un test de synthèse vocale.");
        testUtterance.lang = 'fr-FR';
        
        // Show speech synthesis state
        console.log("Speech synthesis state: ", {
          pending: window.speechSynthesis.pending,
          speaking: window.speechSynthesis.speaking,
          paused: window.speechSynthesis.paused
        });
        
        // Log all browser info
        console.log("Navigator info:", {
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          language: navigator.language,
          languages: navigator.languages
        });
        
        // Test short utterance first
        window.speechSynthesis.speak(testUtterance);
        
        // Replace with shortened version for main speech
        textContent = shortenedText;
      }

      // Log available voices for debugging
      const currentVoices = voices.length > 0 ? voices : window.speechSynthesis.getVoices();
      console.log("Available voices:", currentVoices.map(v => ({
        name: v.name,
        lang: v.lang,
        default: v.default,
        localService: v.localService
      })));
      
      // Create a new speech synthesis utterance
      const utterance = new SpeechSynthesisUtterance(textContent);
      
      // Get French voice if available, otherwise use default
      let voicesToUse = currentVoices;
      
      const frenchVoice = voicesToUse.find(voice => 
        voice.lang === 'fr-FR' || 
        voice.lang.startsWith('fr') || 
        voice.name.toLowerCase().includes('french') ||
        voice.name.toLowerCase().includes('français')
      );
      
      if (frenchVoice) {
        utterance.voice = frenchVoice;
        console.log("Using French voice:", frenchVoice.name);
      } else {
        console.log("No French voice found, using default voice");
        
        // If no French voice, try to at least get a good default voice
        const defaultVoice = voicesToUse.find(v => v.default === true);
        if (defaultVoice) {
          utterance.voice = defaultVoice;
          console.log("Using default voice:", defaultVoice.name);
        }
      }
      
      utterance.lang = 'fr-FR'; // Set French as the language 
      utterance.rate = 0.9; // Slightly slower for better clarity
      utterance.pitch = 1.0; // Normal pitch
      utterance.volume = 1.0; // Full volume
      
      // Add event handlers for better debugging
      utterance.onstart = () => {
        console.log("Speech started");
      };
      
      utterance.onerror = async (event) => {
        console.error("Speech synthesis error:", event);
        console.error("Error details:", {
          error: event.error,
          message: event.message,
          name: event.name,
          utterance: event.utterance?.text?.substring(0, 100) + '...'
        });
        
        // Try the fallback if speech synthesis fails
        console.log("Speech synthesis failed, trying fallback approach");
        setUseTextToSpeechAPI(false);
        const success = await useTextToSpeechFallback(textContent);
        if (!success) {
          setError(`Erreur de synthèse vocale: ${event.error || 'Erreur inconnue'}`);
          setSpeakingMessageIndex(null);
        }
        
        // Try to recover speech synthesis
        window.speechSynthesis.cancel();
      };
      
      // Store the utterance reference to be able to cancel it later
      speechSynthRef.current = utterance;
      
      // Add an event listener for when speech has finished
      utterance.onend = () => {
        console.log("Speech ended successfully");
        setSpeakingMessageIndex(null);
      };
      
      // Use a workaround for Chrome bug (speech sometimes stops after 15 seconds)
      const resumeSpeechSynthesis = () => {
        if (window.speechSynthesis.speaking) {
          window.speechSynthesis.pause();
          window.speechSynthesis.resume();
          timeoutId = setTimeout(resumeSpeechSynthesis, 5000);
        }
      };
      let timeoutId = setTimeout(resumeSpeechSynthesis, 5000);
      
      // Attach to utterance end to clear the workaround
      utterance.onend = () => {
        clearTimeout(timeoutId);
        console.log("Speech ended successfully");
        setSpeakingMessageIndex(null);
      };
      
      // Start speaking
      setTimeout(() => {
        // Add a slight delay to ensure the test utterance has time to process
        window.speechSynthesis.speak(utterance);
      }, 500);
      
    } catch (err) {
      console.error('Failed to speak message:', err);
      console.error('Error details:', {
        name: err.name,
        message: err.message,
        stack: err.stack
      });
      
      // Try the fallback if speech synthesis fails with an exception
      console.log("Speech synthesis exception, trying fallback approach");
      const success = await useTextToSpeechFallback(textContent);
      if (!success) {
        setError(`Impossible de lire le message à haute voix: ${err.message}`);
        setSpeakingMessageIndex(null);
      }
      
      // Attempt recovery
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    }
  };

  const handleShowStats = async () => {
    setLoadingStats(true);
    try {
      const response = await chatService.getStatistics();
      setStatistics(response.data);
      setShowStats(true);
    } catch (error) {
      console.error("Failed to fetch statistics:", error);
      setError("Failed to load statistics");
    } finally {
      setLoadingStats(false);
    }
  };

  return (
    <div className="flex h-screen bg-bp-gray-light overflow-hidden">
      <Joyride
        steps={tourSteps}
        run={runTour}
        continuous={true}
        showProgress={true}
        showSkipButton={true}
        callback={handleJoyrideCallback}
        locale={{
          back: 'Précédent',
          close: 'Fermer',
          last: 'Terminer',
          next: 'Suivant',
          skip: 'skip'
        }}
        styles={{
          options: {
            primaryColor: '#FF6F00',
            zIndex: 10000,
          }
        }}
      />
      
      <div className={`bg-gray-200 text-gray-800 flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out ${isSidebarOpen ? 'w-64 p-4' : 'w-0 p-0 overflow-hidden'}`}>
        <div className={`${isSidebarOpen ? 'opacity-100 delay-200' : 'opacity-0'} transition-opacity duration-200 flex flex-col h-full overflow-hidden`}>
          <div className="flex items-center mb-4 flex-shrink-0">
              <img src="https://www.zonebourse.com/static/private-issuer-squared-9I42B.png" alt="Logo Banque Populaire" className="h-8 w-auto mr-2" />
              <h2 className="text-xl font-semibold">Assistant BCP</h2>
          </div>
          <button
            onClick={handleNewConversation}
            className="mb-4 bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded w-full transition duration-150 ease-in-out flex-shrink-0 new-chat-button"
            disabled={isLoading}
          >
            + Nouvelle Discussion
          </button>
          <div className="flex-grow overflow-y-auto pr-1 mb-4 conversation-list">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={`p-2 mb-1 rounded cursor-pointer flex justify-between items-center text-xs transition duration-150 ease-in-out ${ 
                  currentConversationId === conv.id ? 'bg-bp-orange-bright text-white': 'text-gray-700 hover:bg-gray-300 hover:text-gray-900'
                }`}
              >
                <span className="truncate flex-grow mr-2">
                  {conv.title || `Chat ${conv.id.substring(0, 6)}`}
                  {conv.files && conv.files.length > 0 && (
                    <span className="ml-1 text-xs">📎{conv.files.length}</span>
                  )}
                </span>
                <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="text-bp-gray-dark hover:text-red-500 flex-shrink-0 px-1.5 py-0 rounded-full hover:bg-gray-700 transition-colors duration-150"
                      title="Delete Conversation"
                      disabled={isLoading}
                  >
                      <span className="font-bold">×</span> 
                  </button>
              </div>
            ))}
            {conversations.length === 0 && !isLoading && (
              <div className="text-center text-bp-gray-lighter p-4">
                No conversations yet.
              </div>
            )}
          </div>
          <div className="mt-auto pt-4 border-t border-gray-700 flex-shrink-0">
            {user && (
              <div className="mb-3">
                <div className="flex items-center">
                  <p className="text-xs text-bp-gray-lighter">
                  Logged in as: <span className="font-bold text-black">{user.full_name || user.username}</span>
                </p>
                </div>
              </div>
            )}
            {user && user.is_admin && (
              <button
                onClick={() => navigate('/admin')}
                className="mb-2 w-full bg-bp-orange hover:bg-bp-orange-bright text-white font-bold py-2 px-3 rounded text-sm transition duration-150 ease-in-out"
              >
                Panneau Admin
              </button>
            )}
            <button
              onClick={() => navigate('/profile')}
              className="mb-2 w-full bg-bp-gray hover:bg-bp-gray-dark text-bp-gray-dark hover:text-white font-bold py-2 px-3 rounded text-sm transition duration-150 ease-in-out"
            >
              Profil Utilisateur
              {user && user.two_factor_enabled && user.two_factor_confirmed && (
                <span className="ml-1 text-green-600 font-bold">🔒</span>
              )}
            </button>
            <button
              onClick={logout}
              className="w-full bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-3 rounded text-sm transition duration-150 ease-in-out"
            >
              Déconnexion
            </button>
          </div>
        </div> 
      </div>

      <div className="flex-grow flex flex-col h-full relative">
        <button 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
          className="absolute top-4 left-2 z-20 p-1 bg-bp-sidebar-bg text-white rounded-md hover:bg-bp-sidebar-hover focus:outline-none focus:ring-2 focus:ring-bp-orange" 
          aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          title={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          {isSidebarOpen ? '«' : '»'}
        </button>

        <div className="flex-grow overflow-y-auto p-4 pb-0 pt-16 flex flex-col">
          {Object.keys(uploadedFiles).length > 0 && (
            <div className="mb-4 p-2 rounded bg-bp-sidebar-hover text-bp-white text-sm">
              <h3 className="text-xs font-semibold mb-1">Fichiers téléchargés:</h3>
              <div className="flex flex-wrap">
                {Object.values(uploadedFiles).map(file => (
                  <button
                    key={file.id}
                    onClick={() => handleSelectFile(file.id)}
                    className={`m-1 px-2 py-1 text-xs rounded-md flex items-center ${
                      lastUsedFileId === file.id 
                        ? 'bg-bp-orange-bright text-white' 
                        : 'bg-gray-700 hover:bg-gray-600'
                    }`}
                  >
                    <span className="mr-1">📊</span>
                    <span className="truncate max-w-[100px]">{file.filename}</span>
                  </button>
                ))}
              </div>
              {lastUsedFileId && (
                <p className="text-xs mt-1 text-bp-orange-bright">
                  Utiliser: {uploadedFiles[lastUsedFileId]?.filename} pour le prochain message
                </p>
              )}
            </div>
          )}

          {messages.map((msg, index) => {
            return (
              <div 
                key={msg.id || index}
                className={`mb-2 flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`} 
              >
                <div className={`inline-block max-w-[80%] p-3 rounded-lg shadow-sm ${ 
                  msg.role === 'user' 
                    ? 'bg-bp-orange text-white rounded-tr-none' 
                    : 'bg-bp-chat-bubble text-bp-text rounded-tl-none'
                }`}>
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                  ) : (
                    <div 
                      className="whitespace-pre-line break-words assistant-content"
                      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(msg.content || '') }}
                    />
                  )}
                  {msg.file_id && uploadedFiles[msg.file_id] && (
                    <div className="mt-1 text-xs opacity-70 flex items-center">
                      <span className="mr-1">📊</span>
                      Referenced: {uploadedFiles[msg.file_id].filename}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="mt-1 self-end flex items-center space-x-2"> 
                    <button
                      onClick={() => handleResendMessage(msg.content, msg.file_id)}
                      className="text-base text-gray-700 hover:text-bp-orange bg-white border border-gray-300 rounded p-1 shadow-sm hover:bg-gray-50 transition-colors focus:outline-none"
                      title="Relancer cette requête"
                      disabled={isLoading}
                    >
                      <FiRefreshCcw size={16} />
                    </button>
                  </div>
                )}
                {msg.role === 'assistant' && (
                  <div className="mt-1 self-start">
                    <div className="flex items-center space-x-2 px-1 feedback-buttons">
                      <button 
                          onClick={() => handleFeedbackSubmit(index, 'up')}
                          className={`text-xs p-1 rounded-full hover:bg-gray-200 transition-colors ${ 
                              feedbackState[index] === 'up' ? 'text-green-700' : 'text-black hover:text-green-600' 
                          }`}
                          title="Bonne réponse"
                      >
                          <FiThumbsUp size={16} />
                      </button>
                      <button 
                          onClick={() => handleFeedbackSubmit(index, 'down')}
                          className={`text-xs p-1 rounded-full hover:bg-gray-200 transition-colors ${ 
                              (feedbackState[index] === 'down' || detailedFeedbackOpenFor === index) ? 'text-red-700' : 'text-black hover:text-red-600'
                          }`}
                          title="Mauvaise réponse"
                      >
                          <FiThumbsDown size={16} />
                      </button>
                      <button 
                          onClick={() => handleCopyMessage(msg.content, index)}
                          className="text-xs p-1 rounded-full text-gray-400 hover:text-bp-orange hover:bg-gray-200 transition-colors copy-button"
                          title="Copier la réponse"
                      >
                          <FiCopy size={16} />
                      </button>
                      <button 
                          onClick={() => handleTextToSpeech(msg.content, index)}
                          className={`text-xs p-1 rounded-full hover:bg-gray-200 transition-colors ${
                            speakingMessageIndex === index ? 'text-bp-orange' : 'text-gray-400 hover:text-bp-orange'
                          }`}
                          title={speakingMessageIndex === index ? "Arrêter la lecture" : "Lire à haute voix"}
                      >
                          <FiVolume2 size={16} />
                      </button>
                      <button 
                          onClick={handleShowStats}
                          className="text-xs p-1 rounded-full text-gray-400 hover:text-bp-orange hover:bg-gray-200 transition-colors stats-button"
                          title="Voir les statistiques"
                          disabled={loadingStats}
                      >
                          <FiBarChart2 size={16} />
                      </button>
                      {copiedMessageIndex === index && (
                          <span className="text-xs text-green-600 ml-1">Copié !</span>
                      )}
                      {speakingMessageIndex === index && (
                          <span className="text-xs text-bp-orange ml-1">Lecture en cours...</span>
                      )}
                    </div>
                    {detailedFeedbackOpenFor === index && (
                      <form onSubmit={handleDetailedFeedbackFormSubmit} className="mt-2 p-4 bg-white rounded-lg shadow-lg border border-gray-200 text-sm w-full max-w-xs sm:max-w-sm md:max-w-md self-start">
                        <div className="mb-4">
                          <label htmlFor={`feedback-problem-${index}`} className="block text-sm font-semibold text-gray-700 mb-2">
                            Quel est le problème avec cette réponse ?
                          </label>
                          <select
                            id={`feedback-problem-${index}`}
                            value={detailedFeedbackProblem}
                            onChange={(e) => setDetailedFeedbackProblem(e.target.value)}
                            className="w-full p-2.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-bp-orange focus:border-bp-orange text-sm bg-gray-50 hover:bg-white transition-colors duration-200"
                          >
                            {PREDEFINED_FEEDBACK_PROBLEMS.map(problem => (
                              <option key={problem} value={problem} className="py-1">{problem}</option>
                            ))}
                          </select>
                        </div>
                        <div className="mb-4">
                          <label htmlFor={`feedback-comment-${index}`} className="block text-sm font-semibold text-gray-700 mb-2">
                            Précisions {detailedFeedbackProblem === 'Autre' ? '(requis)' : '(optionnel)'} :
                          </label>
                          <textarea
                            id={`feedback-comment-${index}`}
                            value={detailedFeedbackComment}
                            onChange={(e) => setDetailedFeedbackComment(e.target.value)}
                            rows="3"
                            className="w-full p-2.5 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-bp-orange focus:border-bp-orange text-sm bg-gray-50 hover:bg-white transition-colors duration-200 resize-none"
                            placeholder={detailedFeedbackProblem === 'Autre' ? "Veuillez décrire le problème en détail..." : "Donnez plus de détails ici..."}
                          />
                        </div>
                        <div className="flex justify-end space-x-3">
                          <button
                            type="button"
                            onClick={handleCancelDetailedFeedback}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-400"
                          >
                            Annuler
                          </button>
                          <button
                            type="submit"
                            className="px-4 py-2 text-sm font-medium text-white bg-bp-orange hover:bg-bp-orange-bright rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-bp-orange focus:ring-offset-2"
                          >
                            Envoyer le feedback
                          </button>
                        </div>
                      </form>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          {!currentConversationId && !messages.length && !isLoading && (
            <div className="flex-grow flex items-center justify-center">
                <div className="text-center text-bp-gray-dark">
                    <p className="mb-2 text-lg font-semibold">Assistant de Chat</p>
                    <p className="text-xs mb-4">Sélectionnez ou démarrez une conversation.</p>
                </div>
            </div>
          )}
          {isNewConversation && messages.length === 0 && !isLoading && (
            <div className="flex-grow flex items-center justify-center">
                <div className="text-center text-bp-gray-dark">
                    <button
                        onClick={handleShowStats}
                        className="flex items-center justify-center gap-2 bg-bp-orange hover:bg-bp-orange-bright text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
                        disabled={loadingStats}
                    >
                        <FiBarChart2 size={20} />
                        <span>Voir les Statistiques</span>
                        {loadingStats && (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        )}
                    </button>
                </div>
            </div>
          )}
          {isLoading && (
            <div className="text-center py-4">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-bp-orange border-r-transparent"></div>
            </div>
          )}
          <div ref={messagesEndRef} />
          
          {/* Statistics Modal */}
          {showStats && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold text-bp-orange">Analyse des Données</h2>
                  <button
                    onClick={() => setShowStats(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>

                {loadingStats ? (
                  <div className="flex justify-center items-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-bp-orange"></div>
                  </div>
                ) : statistics && statistics.data_analysis ? (
                  <>
                    {/* Overview Cards */}
                    <div className="grid grid-cols-4 gap-4 mb-6">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-sm font-medium mb-2">Total des Flux</h3>
                        <p className="text-2xl font-bold text-bp-orange">{statistics.data_analysis.total_flux || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-sm font-medium mb-2">Filiales</h3>
                        <p className="text-2xl font-bold text-bp-orange">{statistics.data_analysis.total_filiales || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-sm font-medium mb-2">Types de Source</h3>
                        <p className="text-2xl font-bold text-bp-orange">{statistics.data_analysis.total_types_source || 0}</p>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-sm font-medium mb-2">Technologies</h3>
                        <p className="text-2xl font-bold text-bp-orange">{statistics.data_analysis.total_technologies || 0}</p>
                      </div>
                    </div>

                    {/* Charts Grid */}
                    <div className="grid grid-cols-2 gap-6">
                      {/* Flux par Filiale */}
                      {statistics.data_analysis.flux_par_filiale && Object.keys(statistics.data_analysis.flux_par_filiale).length > 0 && (
                        <div className="bg-white p-4 rounded-lg shadow">
                          <h3 className="text-lg font-medium mb-4">Flux par Filiale</h3>
                          <div className="h-80">
                            <Bar
                              data={{
                                labels: Object.keys(statistics.data_analysis.flux_par_filiale),
                                datasets: [{
                                  label: 'Nombre de flux',
                                  data: Object.values(statistics.data_analysis.flux_par_filiale).map(item => item.count),
                                  backgroundColor: 'rgba(255, 111, 0, 0.6)',
                                  borderColor: 'rgba(255, 111, 0, 1)',
                                  borderWidth: 1
                                }]
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                  legend: {
                                    display: false
                                  }
                                },
                                scales: {
                                  y: {
                                    beginAtZero: true,
                                    title: {
                                      display: true,
                                      text: 'Nombre de flux'
                                    }
                                  }
                                }
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Types de Source */}
                      {statistics.data_analysis.types_source && Object.keys(statistics.data_analysis.types_source).length > 0 && (
                        <div className="bg-white p-4 rounded-lg shadow">
                          <h3 className="text-lg font-medium mb-4">Types de Source</h3>
                          <div className="h-80">
                            <Pie
                              data={{
                                labels: Object.keys(statistics.data_analysis.types_source),
                                datasets: [{
                                  data: Object.values(statistics.data_analysis.types_source).map(item => item.count),
                                  backgroundColor: [
                                    'rgba(255, 111, 0, 0.6)',
                                    'rgba(255, 159, 64, 0.6)',
                                    'rgba(255, 205, 86, 0.6)',
                                    'rgba(75, 192, 192, 0.6)',
                                    'rgba(54, 162, 235, 0.6)'
                                  ],
                                  borderColor: [
                                    'rgba(255, 111, 0, 1)',
                                    'rgba(255, 159, 64, 1)',
                                    'rgba(255, 205, 86, 1)',
                                    'rgba(75, 192, 192, 1)',
                                    'rgba(54, 162, 235, 1)'
                                  ],
                                  borderWidth: 1
                                }]
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                  legend: {
                                    position: 'right'
                                  }
                                }
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Plateformes Source vs Cible */}
                      {statistics.data_analysis.plateformes && 
                       statistics.data_analysis.plateformes.source && 
                       statistics.data_analysis.plateformes.cible && 
                       Object.keys(statistics.data_analysis.plateformes.source).length > 0 && (
                        <div className="bg-white p-4 rounded-lg shadow">
                          <h3 className="text-lg font-medium mb-4">Plateformes Source vs Cible</h3>
                          <div className="h-80">
                            <Bar
                              data={{
                                labels: Object.keys(statistics.data_analysis.plateformes.source),
                                datasets: [
                                  {
                                    label: 'Source',
                                    data: Object.values(statistics.data_analysis.plateformes.source).map(item => item.count),
                                    backgroundColor: 'rgba(255, 111, 0, 0.6)',
                                    borderColor: 'rgba(255, 111, 0, 1)',
                                    borderWidth: 1
                                  },
                                  {
                                    label: 'Cible',
                                    data: Object.values(statistics.data_analysis.plateformes.cible).map(item => item.count),
                                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                                    borderColor: 'rgba(75, 192, 192, 1)',
                                    borderWidth: 1
                                  }
                                ]
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                  legend: {
                                    position: 'top'
                                  }
                                },
                                scales: {
                                  y: {
                                    beginAtZero: true,
                                    title: {
                                      display: true,
                                      text: 'Nombre de flux'
                                    }
                                  }
                                }
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Formats de Fichiers */}
                      {statistics.data_analysis.formats && Object.keys(statistics.data_analysis.formats).length > 0 && (
                        <div className="bg-white p-4 rounded-lg shadow">
                          <h3 className="text-lg font-medium mb-4">Formats de Fichiers</h3>
                          <div className="h-80">
                            <Pie
                              data={{
                                labels: Object.keys(statistics.data_analysis.formats),
                                datasets: [{
                                  data: Object.values(statistics.data_analysis.formats).map(item => item.count),
                                  backgroundColor: [
                                    'rgba(255, 111, 0, 0.6)',
                                    'rgba(255, 159, 64, 0.6)',
                                    'rgba(255, 205, 86, 0.6)',
                                    'rgba(75, 192, 192, 0.6)',
                                    'rgba(54, 162, 235, 0.6)'
                                  ],
                                  borderColor: [
                                    'rgba(255, 111, 0, 1)',
                                    'rgba(255, 159, 64, 1)',
                                    'rgba(255, 205, 86, 1)',
                                    'rgba(75, 192, 192, 1)',
                                    'rgba(54, 162, 235, 1)'
                                  ],
                                  borderWidth: 1
                                }]
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                  legend: {
                                    position: 'right'
                                  }
                                }
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Fréquence de Mise à Jour */}
                      {statistics.data_analysis.frequence_maj && Object.keys(statistics.data_analysis.frequence_maj).length > 0 && (
                        <div className="bg-white p-4 rounded-lg shadow">
                          <h3 className="text-lg font-medium mb-4">Fréquence de Mise à Jour</h3>
                          <div className="h-80">
                            <Bar
                              data={{
                                labels: Object.keys(statistics.data_analysis.frequence_maj),
                                datasets: [{
                                  label: 'Nombre de flux',
                                  data: Object.values(statistics.data_analysis.frequence_maj).map(item => item.count),
                                  backgroundColor: 'rgba(255, 111, 0, 0.6)',
                                  borderColor: 'rgba(255, 111, 0, 1)',
                                  borderWidth: 1
                                }]
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                  legend: {
                                    display: false
                                  }
                                },
                                scales: {
                                  y: {
                                    beginAtZero: true,
                                    title: {
                                      display: true,
                                      text: 'Nombre de flux'
                                    }
                                  }
                                }
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Technologies */}
                      {statistics.data_analysis.technologies && Object.keys(statistics.data_analysis.technologies).length > 0 && (
                        <div className="bg-white p-4 rounded-lg shadow">
                          <h3 className="text-lg font-medium mb-4">Technologies Utilisées</h3>
                          <div className="h-80">
                            <Pie
                              data={{
                                labels: Object.keys(statistics.data_analysis.technologies),
                                datasets: [{
                                  data: Object.values(statistics.data_analysis.technologies).map(item => item.count),
                                  backgroundColor: [
                                    'rgba(255, 111, 0, 0.6)',
                                    'rgba(255, 159, 64, 0.6)',
                                    'rgba(255, 205, 86, 0.6)',
                                    'rgba(75, 192, 192, 0.6)',
                                    'rgba(54, 162, 235, 0.6)'
                                  ],
                                  borderColor: [
                                    'rgba(255, 111, 0, 1)',
                                    'rgba(255, 159, 64, 1)',
                                    'rgba(255, 205, 86, 1)',
                                    'rgba(75, 192, 192, 1)',
                                    'rgba(54, 162, 235, 1)'
                                  ],
                                  borderWidth: 1
                                }]
                              }}
                              options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                  legend: {
                                    position: 'right'
                                  }
                                }
                              }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    Aucune donnée disponible pour l'analyse
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="px-4 py-2 bg-red-100 text-red-800 text-sm">
            Erreur: {error}
          </div>
        )}

        {currentConversationId && (
          <div className="px-4 pt-2 pb-1 bg-bp-gray-light flex flex-wrap items-center file-upload">
            <input 
              type="file" 
              id="file-upload" 
              className="hidden"
              onChange={handleFileChange}
              accept=".xlsx"
            />
            <label 
              htmlFor="file-upload"
              className="cursor-pointer text-sm text-bp-orange hover:text-bp-orange-bright mr-2 flex items-center"
            >
              <span className="mr-1">📎</span>
              {selectedFile ? selectedFile.name : "Joindre Excel"}
            </label>
            
            {selectedFile && (
              <button
                onClick={handleFileUpload}
                disabled={fileUploading}
                className={`text-xs px-2 py-1 rounded ${
                  fileUploading 
                    ? 'bg-gray-400 text-gray-700' 
                    : 'bg-bp-orange hover:bg-bp-orange-bright text-white'
                }`}
              >
                {fileUploading ? 'Téléchargement...' : 'Télécharger'}
              </button>
            )}
            
            {lastUsedFileId && (
              <div className="ml-auto text-xs text-bp-orange-bright flex items-center">
                <span className="mr-1">📊</span>
                Using: {uploadedFiles[lastUsedFileId]?.filename}
                <button 
                  onClick={() => setLastUsedFileId(null)}
                  className="ml-1 text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
            )}
          </div>
        )}

        <div className="p-4 pt-2 bg-bp-gray-light border-t border-bp-sidebar-bg">
          <form onSubmit={handleSendMessage} className="flex items-center">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Écrivez un message..."
              className="flex-grow mr-2 p-2 rounded border focus:outline-none focus:ring-2 focus:ring-bp-orange message-input"
              disabled={isLoading || !currentConversationId}
            />
            {isLoading && currentAbortController ? (
              <button
                type="button"
                onClick={() => {
                  console.log("Attempting to stop. Controller:", currentAbortController);
                  if (currentAbortController) {
                    currentAbortController.abort();
                    console.log("Abort function called.");
                  } else {
                    console.error("Stop clicked but no controller available!");
                  }
                }}
                className="p-2 rounded bg-white border border-gray-300 text-red-500 hover:bg-gray-100 shadow-sm hover:shadow transition duration-150 ease-in-out focus:outline-none"
                aria-label="Stop generating response"
              >
                <FiSquare size={22} className="text-red-500" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || !newMessage.trim() || !currentConversationId}
                className={`p-2 rounded ${
                  isLoading || !newMessage.trim() || !currentConversationId
                    ? 'bg-gray-400 text-gray-700'
                    : 'bg-bp-orange hover:bg-bp-orange-bright text-white'
                } transition duration-150 ease-in-out`}
                aria-label="Send message"
              >
                <span className="text-xl">➤</span>
              </button>
            )}
          </form>
        </div>

      <button 
        onClick={() => {
          localStorage.removeItem('hasCompletedTour');
          setRunTour(true);
        }}
        className="fixed top-4 right-4 z-50 p-2 bg-bp-chat-bubble text-bp-orange shadow-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-bp-orange transition-all duration-300 ease-in-out cursor-pointer"
        style={{ 
          borderRadius: '12px', 
          borderTopRight: 'none',
          width: 'auto',
          height: 'auto'
        }}
        aria-label="Guide d'utilisation"
        title="Guide d'utilisation"
      >
        <div className="flex items-center">
          <FiHelpCircle size={20} />
        </div>
      </button>
    </div>
  </div>
);
}

export default ChatPage;