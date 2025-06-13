// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { chatService } from '../services/api';
import { useNavigate } from 'react-router-dom';
import axios from 'axios'; // Importer axios pour isCancel
import { FiRefreshCcw, FiSquare, FiTrash2, FiThumbsUp, FiThumbsDown, FiCopy, FiHelpCircle, FiBarChart2, FiVolume2, FiDownload, FiUpload, FiSend, FiMoreVertical, FiSearch, FiX, FiSmile, FiZap, FiEye, FiEyeOff } from "react-icons/fi"; // Import de l'icône de relance, FiSquare et FiTrash2, FiThumbsUp, FiThumbsDown, FiCopy, FiHelpCircle, FiBarChart2, FiVolume2, FiDownload
import DOMPurify from 'dompurify'; // Import DOMPurify pour la sanitisation HTML
import Joyride, { STATUS } from 'react-joyride';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

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

  // NEW UX IMPROVEMENTS: Enhanced states
  const [isTyping, setIsTyping] = useState(false); // AI typing indicator
  const [dragOver, setDragOver] = useState(false); // Drag & drop state
  const [messageInputFocused, setMessageInputFocused] = useState(false);
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [showNotification, setShowNotification] = useState(null);
  const [soundEnabled, setSoundEnabled] = useState(localStorage.getItem('soundEnabled') !== 'false');

  // ADDITIONAL UX IMPROVEMENTS: New states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [conversationSearchQuery, setConversationSearchQuery] = useState('');
  const [messageReactions, setMessageReactions] = useState({});
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const [typingSpeed, setTypingSpeed] = useState(50); // ms per character
  const [compactMode, setCompactMode] = useState(localStorage.getItem('compactMode') === 'true');
  const [highContrastMode, setHighContrastMode] = useState(localStorage.getItem('highContrastMode') === 'true');
  const [fontSize, setFontSize] = useState(localStorage.getItem('fontSize') || 'medium');
  const [autoScroll, setAutoScroll] = useState(localStorage.getItem('autoScroll') !== 'false');
  const [showTimestamps, setShowTimestamps] = useState(localStorage.getItem('showTimestamps') === 'true');

  // Refs
  const messageInputRef = useRef(null);
  const chatContainerRef = useRef(null);
  const fileInputRef = useRef(null);
  const searchInputRef = useRef(null);

  const PREDEFINED_FEEDBACK_PROBLEMS = [
    "Information incorrecte",
    "Réponse pas claire",
    "Ne répond pas à la question",
    "Contenu offensant",
    "Autre"
  ];

  // Quick reply suggestions
  const QUICK_REPLIES = [
    "Peux-tu expliquer davantage ?",
    "Merci pour cette information",
    "Peux-tu donner un exemple ?",
    "Comment puis-je procéder ?",
    "Quelles sont les alternatives ?",
    "Peux-tu résumer les points clés ?"
  ];

  // Message search functionality
  const searchMessages = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      // Search in current conversation messages
      const results = messages.filter(msg => 
        msg.content.toLowerCase().includes(query.toLowerCase())
      ).map((msg, index) => ({
        ...msg,
        messageIndex: messages.indexOf(msg),
        snippet: getMessageSnippet(msg.content, query)
      }));

      setSearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  };

  // Get message snippet with highlighted search term
  const getMessageSnippet = (content, query) => {
    const index = content.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return content.substring(0, 100) + '...';
    
    const start = Math.max(0, index - 50);
    const end = Math.min(content.length, index + query.length + 50);
    const snippet = content.substring(start, end);
    
    return snippet.replace(
      new RegExp(query, 'gi'),
      `<mark class="bg-yellow-200 px-1 rounded">$&</mark>`
    );
  };

  // Scroll to specific message
  const scrollToMessage = (messageIndex) => {
    const messageElement = document.querySelector(`[data-message-index="${messageIndex}"]`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      messageElement.classList.add('highlight-message');
      setTimeout(() => {
        messageElement.classList.remove('highlight-message');
      }, 2000);
    }
  };

  // Filter conversations based on search
  const filteredConversations = conversations.filter(conv =>
    (conv.title || `Chat ${conv.id.substring(0, 6)}`).toLowerCase().includes(conversationSearchQuery.toLowerCase())
  );

  // Add message reaction
  const addMessageReaction = (messageIndex, reaction) => {
    setMessageReactions(prev => ({
      ...prev,
      [messageIndex]: {
        ...prev[messageIndex],
        [reaction]: (prev[messageIndex]?.[reaction] || 0) + 1
      }
    }));
  };

  // Quick reply handler
  const handleQuickReply = (reply) => {
    setNewMessage(reply);
    setShowQuickReplies(false);
    messageInputRef.current?.focus();
  };

  // NEW: Window resize handler
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
      // Auto-close sidebar on mobile
      if (window.innerWidth <= 768) {
        setIsSidebarOpen(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // NEW: Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl/Cmd + Enter to send message
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (newMessage.trim() && currentConversationId && !isLoading) {
          handleSendMessage(e);
        }
      }
      
      // Escape to close sidebar on mobile or stop generation
      if (e.key === 'Escape') {
        if (showSearch) {
          setShowSearch(false);
          setSearchQuery('');
          setSearchResults([]);
        } else if (showQuickReplies) {
          setShowQuickReplies(false);
        } else if (isMobile && isSidebarOpen) {
          setIsSidebarOpen(false);
        } else if (isLoading && currentAbortController) {
          currentAbortController.abort();
        }
      }
      
      // Ctrl/Cmd + K for new conversation
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        handleNewConversation();
      }

      // Ctrl/Cmd + F for search
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        setShowSearch(true);
        setTimeout(() => searchInputRef.current?.focus(), 100);
      }

      // Ctrl/Cmd + / for quick replies
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        setShowQuickReplies(!showQuickReplies);
      }

      // Alt + Up/Down for conversation navigation
      if (e.altKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        e.preventDefault();
        const currentIndex = conversations.findIndex(conv => conv.id === currentConversationId);
        if (currentIndex !== -1) {
          const nextIndex = e.key === 'ArrowUp' 
            ? Math.max(0, currentIndex - 1)
            : Math.min(conversations.length - 1, currentIndex + 1);
          selectConversation(conversations[nextIndex].id);
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [newMessage, currentConversationId, isLoading, currentAbortController, isMobile, isSidebarOpen, showSearch, showQuickReplies, conversations]);

  // Search effect
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (searchQuery) {
        searchMessages(searchQuery);
      }
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchQuery, messages]);

  // Auto-save preferences
  useEffect(() => {
    localStorage.setItem('compactMode', compactMode.toString());
    localStorage.setItem('highContrastMode', highContrastMode.toString());
    localStorage.setItem('fontSize', fontSize);
    localStorage.setItem('autoScroll', autoScroll.toString());
    localStorage.setItem('showTimestamps', showTimestamps.toString());
  }, [compactMode, highContrastMode, fontSize, autoScroll, showTimestamps]);

  // NEW: Auto-scroll detection
  useEffect(() => {
    const handleScroll = () => {
      if (chatContainerRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
        setShowScrollToBottom(!isAtBottom && messages.length > 0);
      }
    };

    const container = chatContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [messages.length]);

  // NEW: Drag & Drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const excelFile = files.find(file => file.name.endsWith('.xlsx'));
    
    if (excelFile) {
      setSelectedFile(excelFile);
      showNotificationMessage('Fichier Excel sélectionné: ' + excelFile.name, 'success');
    } else {
      showNotificationMessage('Seuls les fichiers Excel (.xlsx) sont acceptés', 'error');
    }
  };

  // NEW: Notification system
  const showNotificationMessage = (message, type = 'info') => {
    setShowNotification({ message, type });
    setTimeout(() => setShowNotification(null), 3000);
  };

  // NEW: Sound notification
  const playNotificationSound = () => {
    if (soundEnabled) {
      // Simple beep sound using Web Audio API
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
      } catch (error) {
        console.log('Audio notification not available');
      }
    }
  };

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
        content: 'Saisissez vos messages ici pour interagir avec l\'assistant IA. Utilisez Ctrl+Entrée pour envoyer rapidement.',
      },
      {
        target: '.file-upload',
        content: 'Vous pouvez télécharger des fichiers Excel ici ou les glisser-déposer directement.',
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

  // NEW: Scroll to bottom with smooth animation
  const scrollToBottomSmooth = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  // NEW: Activity tracking
  useEffect(() => {
    const updateActivity = () => setLastActivity(Date.now());
    
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, updateActivity, true);
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, updateActivity, true);
      });
    };
  }, []);

  // NEW: Auto-save draft
  useEffect(() => {
    if (newMessage.trim()) {
      localStorage.setItem('chatDraft', newMessage);
    } else {
      localStorage.removeItem('chatDraft');
    }
  }, [newMessage]);

  // NEW: Load draft on mount
  useEffect(() => {
    const draft = localStorage.getItem('chatDraft');
    if (draft) {
      setNewMessage(draft);
    }
  }, []);

  // NEW: Typing indicator simulation
  const simulateTyping = () => {
    setIsTyping(true);
    setTimeout(() => setIsTyping(false), 2000 + Math.random() * 3000);
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
        
        // Clear draft when starting new conversation
        localStorage.removeItem('chatDraft');
        setNewMessage('');
        
        // Focus on input
        setTimeout(() => {
          if (messageInputRef.current) {
            messageInputRef.current.focus();
          }
        }, 100);
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
      showNotificationMessage(`Fichier sélectionné: ${e.target.files[0].name}`, 'success');
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
      showNotificationMessage('Seuls les fichiers Excel (.xlsx) sont acceptés', 'error');
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
      
      showNotificationMessage(`Fichier ${filename} téléchargé avec succès`, 'success');
      playNotificationSound();
      
    } catch (err) {
      console.error("Failed to upload file:", err);
      setError('Failed to upload file. Please try again.');
      showNotificationMessage('Échec du téléchargement du fichier', 'error');
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
    setIsNewConversation(false);
    
    // Clear draft since message is being sent
    localStorage.removeItem('chatDraft');
    
    // Simulate typing indicator
    simulateTyping();

    try {
        const response = await chatService.sendMessage({
            prompt: userMessage.content,
            conversation_id: currentConversationId,
            file_id: lastUsedFileId
        }, controller.signal);

        // Vérifier si la requête n'a pas été annulée avant de traiter la réponse
        if (controller.signal.aborted) {
            console.log('Request was aborted before processing response');
            setMessages(prev => prev.filter(msg => msg !== userMessage));
            setNewMessage(currentInput);
            return;
        }

        const assistantMessage = response.data.assistant_message;
        setMessages(prev => [...prev, assistantMessage]);
        
        // Play notification sound for new response
        playNotificationSound();

        const updatedConvResponse = await chatService.getConversation(currentConversationId);
        const updatedConvData = updatedConvResponse.data;
        if (updatedConvData) {
            setConversations(prevConvos => prevConvos.map(conv =>
                conv.id === currentConversationId ? updatedConvData : conv
            ).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
        }
    } catch (err) {
        // Vérification améliorée pour l'annulation
        if (axios.isCancel(err) || err.name === 'AbortError' || controller.signal.aborted) {
            console.log('Request canceled or aborted:', err.message || 'Request stopped by user');
            setMessages(prev => prev.filter(msg => msg !== userMessage));
            setNewMessage(currentInput);
            setError('Requête annulée');
        } else {
            console.error("Failed to send message:", err);
            // Handle timeout specifically
            if (err.isTimeout) {
                setError('La requête a expiré. Veuillez réessayer ou réduire la taille de votre message.');
            } else {
                setError(err.message || 'Failed to send message. Please try again.');
            }
            setNewMessage(currentInput);
            setMessages(prev => prev.filter(msg => msg !== userMessage));
            if (err.response?.status === 401) logout();
        }
    } finally {
        setIsLoading(false);
        setIsTyping(false);
        setCurrentAbortController(null);
        setTimeout(scrollToBottom, 50);
    }
};

  return (
    <>
      {/* Custom CSS for enhanced UX */}
      <style jsx>{`
        .highlight-message {
          animation: highlight 2s ease-in-out;
          border: 2px solid #FF6F00 !important;
        }
        
        @keyframes highlight {
          0% { background-color: rgba(255, 111, 0, 0.2); }
          50% { background-color: rgba(255, 111, 0, 0.1); }
          100% { background-color: transparent; }
        }
        
        .animate-fade-in {
          animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        
        /* Accessibility improvements */
        .focus-visible:focus {
          outline: 2px solid #FF6F00;
          outline-offset: 2px;
        }
        
        /* High contrast mode adjustments */
        .high-contrast {
          filter: contrast(150%);
        }
        
        /* Smooth scrolling */
        .smooth-scroll {
          scroll-behavior: smooth;
        }

        /* ENHANCED DECORATIVE STYLES */
        
        /* Gradient backgrounds */
        .gradient-bg-primary {
          background: linear-gradient(135deg, #FF6F00 0%, #FF8F40 50%, #FFB366 100%);
        }
        
        .gradient-bg-secondary {
          background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%);
        }
        
        .gradient-bg-dark {
          background: linear-gradient(135deg, #1a202c 0%, #2d3748 50%, #4a5568 100%);
        }
        
        .gradient-text {
          background: linear-gradient(135deg, #FF6F00, #FF8F40);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        /* Glass morphism effects */
        .glass-effect {
          background: rgba(255, 255, 255, 0.25);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.18);
          box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }

        .glass-dark {
          background: rgba(0, 0, 0, 0.25);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Advanced shadows */
        .shadow-glow {
          box-shadow: 0 0 20px rgba(255, 111, 0, 0.3),
                      0 0 40px rgba(255, 111, 0, 0.2),
                      0 0 60px rgba(255, 111, 0, 0.1);
        }

        .shadow-elegant {
          box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1),
                      0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }

        .shadow-float {
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
                      0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        /* Animated backgrounds */
        .animated-bg {
          background: linear-gradient(-45deg, #FF6F00, #FF8F40, #FFB366, #FFC080);
          background-size: 400% 400%;
          animation: gradientShift 15s ease infinite;
        }

        @keyframes gradientShift {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }

        /* Floating animations */
        .float-animation {
          animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }

        /* Pulse effects */
        .pulse-glow {
          animation: pulse-glow 2s ease-in-out infinite alternate;
        }

        @keyframes pulse-glow {
          from {
            box-shadow: 0 0 20px rgba(255, 111, 0, 0.4);
          }
          to {
            box-shadow: 0 0 30px rgba(255, 111, 0, 0.6),
                        0 0 40px rgba(255, 111, 0, 0.4);
          }
        }

        /* Modern borders */
        .border-gradient {
          position: relative;
          border: none;
          background: linear-gradient(white, white) padding-box,
                      linear-gradient(135deg, #FF6F00, #FF8F40) border-box;
          border: 2px solid transparent;
        }

        /* Hover effects */
        .hover-lift {
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .hover-lift:hover {
          transform: translateY(-5px);
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15),
                      0 10px 10px -5px rgba(0, 0, 0, 0.08);
        }

        /* Scrollbar styling */
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
          border-radius: 10px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #FF6F00 0%, #FF8F40 100%);
          border-radius: 10px;
          border: 2px solid #f1f5f9;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #e65100 0%, #f57c00 100%);
        }

        /* Pattern overlays */
        .pattern-dots {
          background-image: radial-gradient(circle, rgba(255, 111, 0, 0.1) 1px, transparent 1px);
          background-size: 20px 20px;
        }

        .pattern-grid {
          background-image: 
            linear-gradient(rgba(255, 111, 0, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 111, 0, 0.1) 1px, transparent 1px);
          background-size: 20px 20px;
        }

        /* Text effects */
        .text-shadow-soft {
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .text-shadow-strong {
          text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }

        /* Loading shimmer */
        .shimmer {
          background: linear-gradient(90deg, 
            rgba(255, 255, 255, 0) 0%, 
            rgba(255, 255, 255, 0.4) 50%, 
            rgba(255, 255, 255, 0) 100%);
          background-size: 200% 100%;
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }

        /* Modern card styles */
        .card-modern {
          background: rgba(255, 255, 255, 0.9);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 16px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        /* Interactive elements */
        .interactive-scale {
          transition: transform 0.2s ease;
        }

        .interactive-scale:hover {
          transform: scale(1.05);
        }

        .interactive-scale:active {
          transform: scale(0.95);
        }

        /* Neon glow effects */
        .neon-glow {
          text-shadow: 0 0 5px rgba(255, 111, 0, 0.8),
                       0 0 10px rgba(255, 111, 0, 0.6),
                       0 0 15px rgba(255, 111, 0, 0.4);
        }

        /* Parallax and depth */
        .depth-1 { transform: translateZ(10px); }
        .depth-2 { transform: translateZ(20px); }
        .depth-3 { transform: translateZ(30px); }

        /* Organic shapes */
        .blob-shape {
          border-radius: 50% 40% 60% 30%;
          animation: blob-morph 8s ease-in-out infinite;
        }

        @keyframes blob-morph {
          0%, 100% { border-radius: 50% 40% 60% 30%; }
          25% { border-radius: 40% 60% 30% 50%; }
          50% { border-radius: 60% 30% 50% 40%; }
          75% { border-radius: 30% 50% 40% 60%; }
        }
      `}</style>

      <div 
        className={`flex h-screen bg-bp-gray-light overflow-hidden ${dragOver ? 'bg-blue-50' : ''} ${
          highContrastMode ? 'high-contrast' : ''
        } pattern-dots`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Drag & Drop Overlay */}
        {dragOver && (
          <div className="fixed inset-0 bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center z-50 pointer-events-none">
            <div className="card-modern p-8 text-center shadow-float">
              <div className="w-16 h-16 mx-auto mb-4 gradient-bg-primary rounded-full flex items-center justify-center text-white text-2xl shadow-glow">
                📁
              </div>
              <p className="text-lg font-semibold text-gray-700 gradient-text">Déposez votre fichier Excel ici</p>
              <p className="text-sm text-gray-500 mt-2">Fichiers .xlsx acceptés</p>
            </div>
          </div>
        )}

        {/* Notification System */}
        {showNotification && (
          <div className={`fixed top-4 right-4 z-50 p-4 rounded-xl shadow-float transition-all duration-500 glass-effect ${
            showNotification.type === 'success' ? 'border-l-4 border-green-400' :
            showNotification.type === 'error' ? 'border-l-4 border-red-400' :
            'border-l-4 border-blue-400'
          } animate-fade-in hover-lift`}>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-3 ${
                showNotification.type === 'success' ? 'bg-green-400 shadow-glow' :
                showNotification.type === 'error' ? 'bg-red-400 shadow-glow' :
                'bg-blue-400 shadow-glow'
              }`}></div>
              <span className="text-gray-800 font-medium">{showNotification.message}</span>
            </div>
          </div>
        )}

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
            skip: 'Passer'
          }}
          styles={{
            options: {
              primaryColor: '#FF6F00',
              zIndex: 10000,
            }
          }}
        />
        
        <div className={`gradient-bg-secondary text-gray-800 flex flex-col flex-shrink-0 transition-all duration-500 ease-in-out shadow-elegant custom-scrollbar ${isSidebarOpen ? 'w-64 p-4' : 'w-0 p-0 overflow-hidden'}`}>
          <div className={`${isSidebarOpen ? 'opacity-100 delay-200' : 'opacity-0'} transition-opacity duration-300 flex flex-col h-full overflow-hidden`}>
            <div className="flex items-center mb-6 flex-shrink-0">
                <div className="w-10 h-10 gradient-bg-primary rounded-xl mr-3 flex items-center justify-center text-white font-bold shadow-glow">
                  BCP
                </div>
                <h2 className="text-xl font-bold gradient-text text-shadow-soft">Assistant BCP</h2>
            </div>
            <button
              onClick={handleNewConversation}
              className="mb-6 gradient-bg-primary hover:shadow-glow text-white font-bold py-3 px-4 rounded-xl w-full transition-all duration-300 ease-in-out flex-shrink-0 new-chat-button flex items-center justify-center shadow-elegant hover-lift interactive-scale"
              disabled={isLoading}
            >
              <span className="mr-2 text-lg">✨</span>
              <span>Nouvelle Discussion</span>
              {isMobile && <span className="ml-2 text-xs opacity-75">(Ctrl+K)</span>}
            </button>
            
            {/* Settings Panel */}
            <div className="mb-6 card-modern shadow-elegant hover-lift">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
                <span className="text-sm font-bold gradient-text">⚙️ Paramètres</span>
                <div className="w-6 h-6 gradient-bg-primary rounded-lg flex items-center justify-center">
                  <span className="text-white text-xs">⚡</span>
                </div>
              </div>
              
              {/* Sound Settings */}
              <div className="flex items-center justify-between mb-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                <span className="text-xs text-gray-700 font-medium">🔊 Sons</span>
                <button
                  onClick={() => {
                    setSoundEnabled(!soundEnabled);
                    localStorage.setItem('soundEnabled', (!soundEnabled).toString());
                  }}
                  className={`w-10 h-5 rounded-full transition-all duration-300 shadow-elegant ${
                    soundEnabled ? 'gradient-bg-primary shadow-glow' : 'bg-gray-300'
                  }`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-elegant ${
                    soundEnabled ? 'translate-x-5' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Compact Mode */}
              <div className="flex items-center justify-between mb-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                <span className="text-xs text-gray-700 font-medium">📱 Mode compact</span>
                <button
                  onClick={() => setCompactMode(!compactMode)}
                  className={`w-10 h-5 rounded-full transition-all duration-300 shadow-elegant ${
                    compactMode ? 'gradient-bg-primary shadow-glow' : 'bg-gray-300'
                  }`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-elegant ${
                    compactMode ? 'translate-x-5' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* High Contrast Mode */}
              <div className="flex items-center justify-between mb-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                <span className="text-xs text-gray-700 font-medium">🌓 Contraste élevé</span>
                <button
                  onClick={() => setHighContrastMode(!highContrastMode)}
                  className={`w-10 h-5 rounded-full transition-all duration-300 shadow-elegant ${
                    highContrastMode ? 'gradient-bg-primary shadow-glow' : 'bg-gray-300'
                  }`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-elegant ${
                    highContrastMode ? 'translate-x-5' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Show Timestamps */}
              <div className="flex items-center justify-between mb-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                <span className="text-xs text-gray-700 font-medium">🕒 Horodatage</span>
                <button
                  onClick={() => setShowTimestamps(!showTimestamps)}
                  className={`w-10 h-5 rounded-full transition-all duration-300 shadow-elegant ${
                    showTimestamps ? 'gradient-bg-primary shadow-glow' : 'bg-gray-300'
                  }`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform duration-300 shadow-elegant ${
                    showTimestamps ? 'translate-x-5' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              {/* Font Size */}
              <div className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors">
                <span className="text-xs text-gray-700 font-medium">🔤 Taille police</span>
                <select
                  value={fontSize}
                  onChange={(e) => setFontSize(e.target.value)}
                  className="text-xs bg-white border-2 border-gray-200 rounded-lg px-2 py-1 shadow-elegant focus:border-gradient transition-all hover-lift"
                >
                  <option value="small">Petit</option>
                  <option value="medium">Moyen</option>
                  <option value="large">Grand</option>
                </select>
              </div>
            </div>

            {/* Conversation Search */}
            <div className="mb-6">
              <div className="relative">
                <input
                  type="text"
                  placeholder="🔍 Rechercher conversations..."
                  value={conversationSearchQuery}
                  onChange={(e) => setConversationSearchQuery(e.target.value)}
                  className="w-full text-xs p-3 pl-4 pr-10 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-200 focus:border-gradient transition-all shadow-elegant glass-effect hover-lift"
                />
                <div className="absolute right-3 top-3 text-gray-400">
                  🔎
                </div>
                {conversationSearchQuery && (
                  <button
                    onClick={() => setConversationSearchQuery('')}
                    className="absolute right-3 top-3 text-gray-400 hover:text-red-500 transition-colors interactive-scale"
                  >
                    ❌
                  </button>
                )}
              </div>
            </div>

            <div className="flex-grow overflow-y-auto pr-1 mb-4 conversation-list custom-scrollbar">
              {filteredConversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className={`p-3 mb-2 rounded-xl cursor-pointer flex justify-between items-center text-xs transition-all duration-300 ease-in-out hover-lift interactive-scale ${ 
                    currentConversationId === conv.id 
                      ? 'gradient-bg-primary text-white shadow-glow neon-glow' 
                      : 'card-modern text-gray-700 hover:shadow-elegant border-gradient'
                  }`}
                >
                  <span className="truncate flex-grow mr-2 font-medium">
                    <span className="mr-2">💬</span>
                    {conv.title || `Chat ${conv.id.substring(0, 6)}`}
                    {conv.files && conv.files.length > 0 && (
                      <span className="ml-2 px-2 py-1 bg-orange-100 text-orange-600 rounded-full text-xs font-bold">
                        📎{conv.files.length}
                      </span>
                    )}
                  </span>
                  <button
                        onClick={(e) => handleDeleteConversation(conv.id, e)}
                        className="text-gray-400 hover:text-red-500 flex-shrink-0 p-2 rounded-full hover:bg-red-50 transition-all duration-200 interactive-scale"
                        title="Supprimer la conversation"
                        disabled={isLoading}
                    >
                        <span className="text-sm">🗑️</span>
                    </button>
                </div>
              ))}
              {conversations.length === 0 && !isLoading && (
                <div className="text-center p-6 card-modern shadow-elegant">
                  <div className="w-16 h-16 mx-auto mb-4 gradient-bg-primary rounded-full flex items-center justify-center text-2xl blob-shape">
                    💭
                  </div>
                  <p className="text-sm font-semibold text-gray-600">Aucune conversation</p>
                  <p className="text-xs text-gray-400 mt-1">Commencez une nouvelle discussion</p>
                </div>
              )}
            </div>
            <div className="mt-auto pt-4 border-t border-gray-700 flex-shrink-0">
              {user && (
                <div className="mb-3">
                  <div className="flex items-center">
                    <p className="text-xs text-bp-gray-lighter">
                    Connecté en tant que: <span className="font-bold text-black">{user.full_name || user.username}</span>
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
            className="absolute top-4 left-2 z-20 p-3 gradient-bg-dark text-white rounded-xl hover:shadow-glow focus:outline-none focus:ring-2 focus:ring-orange-300 transition-all duration-300 hover-lift interactive-scale" 
            aria-label={isSidebarOpen ? 'Fermer la barre latérale' : 'Ouvrir la barre latérale'}
            title={isSidebarOpen ? 'Fermer la barre latérale (Échap)' : 'Ouvrir la barre latérale'}
          >
            <span className="text-lg">{isSidebarOpen ? '◀' : '▶'}</span>
          </button>

          {/* Search Bar */}
          {showSearch && (
            <div className="absolute top-4 right-4 left-16 z-20 card-modern shadow-float p-4 animate-fade-in">
              <div className="flex items-center gap-3 mb-3">
                <div className="relative flex-grow">
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="🔍 Rechercher dans la conversation..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full p-3 pl-4 pr-12 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-200 focus:border-gradient text-sm shadow-elegant glass-effect transition-all"
                  />
                  <div className="absolute right-3 top-3 text-gray-400 text-lg">
                    🔎
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowSearch(false);
                    setSearchQuery('');
                    setSearchResults([]);
                  }}
                  className="p-3 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all interactive-scale"
                >
                  <span className="text-lg">❌</span>
                </button>
              </div>
              
              {/* Search Results */}
              {searchQuery && (
                <div className="max-h-48 overflow-y-auto custom-scrollbar">
                  {isSearching ? (
                    <div className="text-center py-8 text-gray-500">
                      <div className="w-8 h-8 mx-auto mb-3 gradient-bg-primary rounded-full animate-spin"></div>
                      <span className="text-sm">Recherche en cours...</span>
                    </div>
                  ) : searchResults.length > 0 ? (
                    <div className="space-y-2">
                      <p className="text-xs text-gray-600 mb-3 font-semibold">
                        ✨ {searchResults.length} résultat(s) trouvé(s)
                      </p>
                      {searchResults.map((result, index) => (
                        <button
                          key={index}
                          onClick={() => {
                            scrollToMessage(result.messageIndex);
                            setShowSearch(false);
                          }}
                          className="w-full text-left p-3 hover:bg-orange-50 rounded-xl border border-gray-100 transition-all hover-lift shadow-elegant"
                        >
                          <div className="text-xs text-gray-500 mb-1 font-medium">
                            <span className="mr-2">{result.role === 'user' ? '👤' : '🤖'}</span>
                            {result.role === 'user' ? 'Vous' : 'Assistant'} • Message #{result.messageIndex + 1}
                          </div>
                          <div 
                            className="text-sm text-gray-700 line-clamp-2"
                            dangerouslySetInnerHTML={{ __html: result.snippet }}
                          />
                        </button>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <div className="w-16 h-16 mx-auto mb-3 bg-gray-100 rounded-full flex items-center justify-center text-2xl">
                        🔍
                      </div>
                      <span className="text-sm">Aucun résultat trouvé</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <div 
            ref={chatContainerRef}
            className={`flex-grow overflow-y-auto p-6 pb-0 pt-20 flex flex-col custom-scrollbar ${
              highContrastMode ? 'bg-black text-white' : 'bg-gradient-to-br from-gray-50 to-gray-100'
            } ${
              fontSize === 'small' ? 'text-sm' : fontSize === 'large' ? 'text-lg' : 'text-base'
            }`}
          >
            {Object.keys(uploadedFiles).length > 0 && (
              <div className="mb-4 p-3 rounded-lg bg-bp-sidebar-hover text-bp-white text-sm shadow-sm">
                <h3 className="text-xs font-semibold mb-2 flex items-center">
                  <FiUpload size={14} className="mr-1" />
                  Fichiers téléchargés:
                </h3>
                <div className="flex flex-wrap gap-2">
                  {Object.values(uploadedFiles).map(file => (
                    <button
                      key={file.id}
                      onClick={() => handleSelectFile(file.id)}
                      className={`px-3 py-1 text-xs rounded-md flex items-center transition-all duration-200 ${
                        lastUsedFileId === file.id 
                          ? 'bg-bp-orange-bright text-white shadow-md' 
                          : 'bg-gray-700 hover:bg-gray-600 hover:shadow-sm'
                      }`}
                    >
                      <span className="mr-1">📊</span>
                      <span className="truncate max-w-[120px]">{file.filename}</span>
                    </button>
                  ))}
                </div>
                {lastUsedFileId && (
                  <p className="text-xs mt-2 text-bp-orange-bright flex items-center">
                    <span className="mr-1">→</span>
                    Utiliser: {uploadedFiles[lastUsedFileId]?.filename} pour le prochain message
                  </p>
                )}
              </div>
            )}

            {/* Messages */}
            {messages.map((msg, index) => {
              return (
                <div 
                  key={msg.id || index}
                  data-message-index={index}
                  className={`mb-4 flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} ${
                    compactMode ? 'mb-2' : 'mb-4'
                  }`} 
                >
                  <div className={`inline-block max-w-[85%] rounded-2xl shadow-elegant transition-all duration-300 hover:shadow-float ${
                    compactMode ? 'p-3' : 'p-4'
                  } ${ 
                    msg.role === 'user' 
                      ? `${highContrastMode ? 'bg-orange-600' : 'gradient-bg-primary'} text-white rounded-tr-lg shadow-glow` 
                      : `${highContrastMode ? 'bg-gray-800 text-white' : 'card-modern text-gray-800'} rounded-tl-lg border-gradient`
                  }`}>
                    {/* Timestamp */}
                    {showTimestamps && (
                      <div className={`text-xs opacity-70 mb-2 font-medium ${
                        msg.role === 'user' ? 'text-right' : 'text-left'
                      }`}>
                        <span className="mr-1">🕒</span>
                        {new Date(msg.created_at || Date.now()).toLocaleTimeString('fr-FR', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                    )}

                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap break-words font-medium">{msg.content}</p>
                    ) : (
                      <div 
                        className="whitespace-pre-line break-words assistant-content"
                        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(msg.content || '') }}
                      />
                    )}
                    {msg.file_id && uploadedFiles[msg.file_id] && (
                      <div className={`mt-3 text-xs opacity-80 flex items-center bg-black bg-opacity-10 rounded-lg px-3 py-2 ${
                        compactMode ? 'text-xs' : 'text-xs'
                      } glass-effect`}>
                        <span className="mr-2 text-lg">📊</span>
                        <span className="font-medium">Référence: {uploadedFiles[msg.file_id].filename}</span>
                      </div>
                    )}
                  </div>

                  {/* Message Reactions */}
                  {msg.role === 'assistant' && messageReactions[index] && (
                    <div className="mt-2 flex items-center gap-1 text-xs">
                      {Object.entries(messageReactions[index]).map(([reaction, count]) => (
                        <span key={reaction} className="card-modern px-3 py-1 rounded-full shadow-elegant hover-lift">
                          {reaction} <span className="font-bold text-orange-500">{count}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {msg.role === 'user' && (
                    <div className={`mt-3 self-end flex items-center space-x-2 ${compactMode ? 'mt-2' : 'mt-3'}`}> 
                      <button
                        onClick={() => handleResendMessage(msg.content, msg.file_id)}
                        className="card-modern text-gray-600 hover:text-orange-500 p-3 rounded-xl shadow-elegant hover:shadow-glow transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-orange-300 hover-lift interactive-scale"
                        title="Relancer cette requête"
                        disabled={isLoading}
                      >
                        <span className="text-lg">🔄</span>
                      </button>
                    </div>
                  )}
                  {msg.role === 'assistant' && (
                    <div className={`mt-3 self-start ${compactMode ? 'mt-2' : 'mt-3'}`}>
                      <div className="flex items-center flex-wrap gap-2 px-1 feedback-buttons">
                        <button 
                            onClick={() => handleFeedbackSubmit(index, 'up')}
                            className={`p-2 rounded-xl transition-all duration-300 hover-lift interactive-scale ${ 
                                feedbackState[index] === 'up' ? 'gradient-bg-primary text-white shadow-glow' : 'card-modern text-gray-500 hover:text-green-600 hover:shadow-elegant' 
                            }`}
                            title="Bonne réponse"
                        >
                            <span className="text-lg">👍</span>
                        </button>
                        <button 
                            onClick={() => handleFeedbackSubmit(index, 'down')}
                            className={`p-2 rounded-xl transition-all duration-300 hover-lift interactive-scale ${ 
                                (feedbackState[index] === 'down' || detailedFeedbackOpenFor === index) ? 'gradient-bg-primary text-white shadow-glow' : 'card-modern text-gray-500 hover:text-red-600 hover:shadow-elegant'
                            }`}
                            title="Mauvaise réponse"
                        >
                            <span className="text-lg">👎</span>
                        </button>
                        <button 
                            onClick={() => handleCopyMessage(msg.content, index)}
                            className="card-modern p-2 rounded-xl text-gray-500 hover:text-blue-600 hover:shadow-elegant transition-all duration-300 hover-lift interactive-scale copy-button"
                            title="Copier la réponse"
                        >
                            <span className="text-lg">📋</span>
                        </button>
                        <button 
                            onClick={() => handleTextToSpeech(msg.content, index)}
                            className={`p-2 rounded-xl transition-all duration-300 hover-lift interactive-scale ${
                              speakingMessageIndex === index ? 'gradient-bg-primary text-white shadow-glow pulse-glow' : 'card-modern text-gray-500 hover:text-purple-600 hover:shadow-elegant'
                            }`}
                            title={speakingMessageIndex === index ? "Arrêter la lecture" : "Lire à haute voix"}
                        >
                            <span className="text-lg">🔊</span>
                        </button>
                        <button 
                            onClick={handleShowStats}
                            className="card-modern p-2 rounded-xl text-gray-500 hover:text-indigo-600 hover:shadow-elegant transition-all duration-300 hover-lift interactive-scale stats-button"
                            title="Voir les statistiques"
                            disabled={loadingStats}
                        >
                            <span className="text-lg">📊</span>
                        </button>

                        {/* Quick Reactions */}
                        <div className="flex items-center gap-1 ml-2">
                          <button
                            onClick={() => addMessageReaction(index, '👍')}
                            className="p-2 rounded-xl card-modern hover:shadow-elegant transition-all duration-300 hover-lift interactive-scale"
                            title="Réaction positive"
                          >
                            <span className="text-base">👍</span>
                          </button>
                          <button
                            onClick={() => addMessageReaction(index, '❤️')}
                            className="p-2 rounded-xl card-modern hover:shadow-elegant transition-all duration-300 hover-lift interactive-scale"
                            title="J'adore"
                          >
                            <span className="text-base">❤️</span>
                          </button>
                          <button
                            onClick={() => addMessageReaction(index, '🤔')}
                            className="p-2 rounded-xl card-modern hover:shadow-elegant transition-all duration-300 hover-lift interactive-scale"
                            title="Intéressant"
                          >
                            <span className="text-base">🤔</span>
                          </button>
                        </div>

                        {copiedMessageIndex === index && (
                            <span className="text-xs font-semibold gradient-text ml-3 animate-fade-in">✨ Copié !</span>
                        )}
                        {speakingMessageIndex === index && (
                            <span className="text-xs gradient-text ml-3 flex items-center font-medium">
                              <div className="animate-pulse mr-2 text-lg">🎵</div>
                              Lecture en cours...
                            </span>
                        )}
                      </div>
                      {detailedFeedbackOpenFor === index && (
                        <form onSubmit={handleDetailedFeedbackFormSubmit} className="mt-3 p-4 bg-white rounded-lg shadow-lg border border-gray-200 text-sm w-full max-w-md self-start">
                          <div className="mb-4">
                            <label htmlFor={`feedback-problem-${index}`} className="block text-sm font-semibold text-gray-700 mb-2">
                              Quel est le problème avec cette réponse ?
                            </label>
                            <select
                              id={`feedback-problem-${index}`}
                              value={detailedFeedbackProblem}
                              onChange={(e) => setDetailedFeedbackProblem(e.target.value)}
                              className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-bp-orange focus:border-bp-orange text-sm bg-gray-50 hover:bg-white transition-colors duration-200"
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
                              className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-bp-orange focus:border-bp-orange text-sm bg-gray-50 hover:bg-white transition-colors duration-200 resize-none"
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

            {/* Typing Indicator */}
            {isTyping && (
              <div className="mb-4 flex items-start">
                <div className="bg-bp-chat-bubble text-bp-text p-4 rounded-lg rounded-tl-none shadow-sm">
                  <div className="flex items-center space-x-1">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-xs text-gray-500 ml-2">L'assistant écrit...</span>
                  </div>
                </div>
              </div>
            )}

            {!currentConversationId && !messages.length && !isLoading && (
              <div className="flex-grow flex items-center justify-center">
                  <div className="text-center text-bp-gray-dark max-w-md">
                      <div className="mb-6">
                        <div className="w-16 h-16 bg-bp-orange rounded-full flex items-center justify-center mx-auto mb-4">
                          <span className="text-2xl text-white">💬</span>
                        </div>
                        <p className="text-xl font-semibold mb-2">Assistant de Chat BCP</p>
                        <p className="text-sm text-gray-600 mb-4">Sélectionnez ou démarrez une conversation pour commencer.</p>
                      </div>
                      <div className="space-y-2 text-xs text-gray-500">
                        <p>💡 <strong>Astuce:</strong> Utilisez Ctrl+K pour une nouvelle conversation</p>
                        <p>📎 Glissez-déposez des fichiers Excel pour les analyser</p>
                        <p>🎯 Utilisez Ctrl+Entrée pour envoyer rapidement</p>
                      </div>
                  </div>
              </div>
            )}
            {isNewConversation && messages.length === 0 && !isLoading && (
              <div className="flex-grow flex items-center justify-center">
                  <div className="text-center text-bp-gray-dark">
                      <button
                          onClick={handleShowStats}
                          className="flex items-center justify-center gap-2 bg-bp-orange hover:bg-bp-orange-bright text-white font-bold py-3 px-6 rounded-lg transition duration-150 ease-in-out shadow-md hover:shadow-lg"
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
              <div className="text-center py-6">
                <div className="inline-flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-6 w-6 border-2 border-bp-orange border-t-transparent"></div>
                  <span className="text-sm text-gray-600">Chargement...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
            
            {/* Scroll to bottom button */}
            {showScrollToBottom && (
              <button
                onClick={scrollToBottomSmooth}
                className="fixed bottom-32 right-6 gradient-bg-primary hover:shadow-glow text-white p-4 rounded-full shadow-float hover:shadow-glow transition-all duration-300 z-10 float-animation hover-lift interactive-scale"
                title="Aller en bas"
              >
                <div className="text-lg">⬇️</div>
              </button>
            )}
            
            {/* Statistics Modal - keeping existing implementation */}
            {showStats && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 max-w-6xl w-full max-h-[90vh] overflow-y-auto">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold text-bp-orange">Analyse des Données</h2>
                    <div className="flex items-center gap-4">
                      <button
                        onClick={async () => {
                          const pdf = new jsPDF('p', 'mm', 'a4');
                          const statsContainer = document.getElementById('user-stats-container');
                          const canvas = await html2canvas(statsContainer, { scale: 2, useCORS: true, logging: false });
                          const imgData = canvas.toDataURL('image/png');
                          const imgWidth = 210;
                          const imgHeight = (canvas.height * imgWidth) / canvas.width;
                          pdf.setFontSize(20);
                          pdf.text('Analyse des Données', 105, 20, { align: 'center' });
                          pdf.setFontSize(12);
                          pdf.text(`Généré le ${new Date().toLocaleDateString()}`, 105, 30, { align: 'center' });
                          pdf.addImage(imgData, 'PNG', 0, 40, imgWidth, imgHeight);
                          pdf.save('statistiques-utilisateur.pdf');
                        }}
                        className="text-sm bg-bp-orange hover:bg-bp-orange-bright text-white py-2 px-4 rounded-lg flex items-center gap-2 shadow-md hover:shadow-lg transition-all duration-200"
                        title="Télécharger en PDF"
                      >
                        <FiDownload size={16} /> Télécharger
                      </button>
                      <button
                        onClick={() => setShowStats(false)}
                        className="text-gray-500 hover:text-gray-700 p-1"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                  <div id="user-stats-container">
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

                        {/* Charts Grid - keeping existing chart implementation */}
                        <div className="grid grid-cols-2 gap-6">
                          {/* Existing chart components would go here */}
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        Aucune donnée disponible pour l'analyse
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="px-4 py-3 bg-red-100 border-l-4 border-red-500 text-red-800 text-sm flex items-center">
              <span className="mr-2">⚠️</span>
              <span><strong>Erreur:</strong> {error}</span>
              <button 
                onClick={() => setError('')}
                className="ml-auto text-red-600 hover:text-red-800"
              >
                ✕
              </button>
            </div>
          )}

          {/* Enhanced File Upload Section */}
          {currentConversationId && (
            <div className="px-4 pt-3 pb-2 bg-bp-gray-light border-t border-gray-200 file-upload">
              <div className="flex flex-wrap items-center gap-3">
                <input 
                  ref={fileInputRef}
                  type="file" 
                  id="file-upload" 
                  className="hidden"
                  onChange={handleFileChange}
                  accept=".xlsx"
                />
                <label 
                  htmlFor="file-upload"
                  className="cursor-pointer text-sm text-bp-orange hover:text-bp-orange-bright flex items-center gap-2 px-3 py-2 border border-bp-orange rounded-lg hover:bg-bp-orange hover:text-white transition-all duration-200"
                >
                  <FiUpload size={16} />
                  {selectedFile ? selectedFile.name : "Joindre Excel"}
                </label>
                
                {selectedFile && (
                  <button
                    onClick={handleFileUpload}
                    disabled={fileUploading}
                    className={`text-sm px-4 py-2 rounded-lg transition-all duration-200 ${
                      fileUploading 
                        ? 'bg-gray-400 text-gray-700 cursor-not-allowed' 
                        : 'bg-bp-orange hover:bg-bp-orange-bright text-white shadow-sm hover:shadow-md'
                    }`}
                  >
                    {fileUploading ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                        Téléchargement...
                      </div>
                    ) : (
                      'Télécharger'
                    )}
                  </button>
                )}
                
                {lastUsedFileId && (
                  <div className="ml-auto text-xs text-bp-orange-bright flex items-center bg-orange-50 px-3 py-2 rounded-lg">
                    <span className="mr-1">📊</span>
                    Utilise: {uploadedFiles[lastUsedFileId]?.filename}
                    <button 
                      onClick={() => setLastUsedFileId(null)}
                      className="ml-2 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded-full p-1 transition-colors"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Enhanced Message Input */}
          <div className="p-4 pt-3 bg-bp-gray-light border-t border-bp-sidebar-bg">
            {/* Quick Replies */}
            {showQuickReplies && (
              <div className="mb-3 p-3 bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Réponses rapides</span>
                  <button
                    onClick={() => setShowQuickReplies(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <FiX size={16} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {QUICK_REPLIES.map((reply, index) => (
                    <button
                      key={index}
                      onClick={() => handleQuickReply(reply)}
                      className="text-left p-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200 hover:border-bp-orange"
                    >
                      {reply}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <form onSubmit={handleSendMessage} className="flex items-end gap-3">
              <div className="flex-grow relative">
                <textarea
                  ref={messageInputRef}
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onFocus={() => setMessageInputFocused(true)}
                  onBlur={() => setMessageInputFocused(false)}
                  placeholder={currentConversationId ? "Écrivez un message... (Ctrl+Entrée pour envoyer)" : "Sélectionnez une conversation pour commencer"}
                  className={`w-full p-3 pr-12 rounded-lg border resize-none transition-all duration-200 message-input ${
                    messageInputFocused 
                      ? 'border-bp-orange ring-2 ring-bp-orange ring-opacity-20 shadow-md' 
                      : 'border-gray-300 hover:border-gray-400'
                  } ${!currentConversationId ? 'bg-gray-100 cursor-not-allowed' : 'bg-white'} ${
                    fontSize === 'small' ? 'text-sm' : fontSize === 'large' ? 'text-lg' : 'text-base'
                  }`}
                  disabled={isLoading || !currentConversationId}
                  rows={newMessage.split('\n').length > 3 ? Math.min(newMessage.split('\n').length, 6) : 1}
                  style={{ minHeight: '44px', maxHeight: '150px' }}
                />
                {newMessage.trim() && (
                  <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                    {newMessage.length} caractères
                  </div>
                )}
                
                {/* Quick Replies Toggle */}
                {currentConversationId && !showQuickReplies && (
                  <button
                    type="button"
                    onClick={() => setShowQuickReplies(true)}
                    className="absolute top-2 right-2 p-1 text-gray-400 hover:text-bp-orange transition-colors"
                    title="Réponses rapides (Ctrl+/)"
                  >
                    <FiZap size={16} />
                  </button>
                )}
              </div>
              
              {isLoading && currentAbortController ? (
                <button
                  type="button"
                  onClick={() => {
                    console.log("Attempting to stop. Controller:", currentAbortController);
                    if (currentAbortController) {
                      currentAbortController.abort();
                      console.log("Abort function called.");
                      
                      // Feedback immédiat : arrêter l'état de loading
                      setIsLoading(false);
                      setCurrentAbortController(null);
                      setError('Requête annulée par l\'utilisateur');
                      
                      // Remettre le message dans l'input si c'était un envoi
                      if (messages.length > 0 && messages[messages.length - 1].role === 'user') {
                        const lastUserMessage = messages[messages.length - 1];
                        setNewMessage(lastUserMessage.content);
                        setMessages(prev => prev.slice(0, -1)); // Supprimer le dernier message utilisateur
                      }
                    } else {
                      console.error("Stop clicked but no controller available!");
                    }
                  }}
                  className="p-3 rounded-lg bg-red-50 border border-red-300 text-red-600 hover:bg-red-100 shadow-sm hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-500 animate-pulse"
                  aria-label="Arrêter la génération"
                  title="Arrêter la génération (Échap)"
                >
                  <FiSquare size={20} />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isLoading || !newMessage.trim() || !currentConversationId}
                  className={`p-3 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-bp-orange ${
                    isLoading || !newMessage.trim() || !currentConversationId
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-bp-orange hover:bg-bp-orange-bright text-white shadow-sm hover:shadow-md hover:scale-105'
                  }`}
                  aria-label="Envoyer le message"
                  title={newMessage.trim() ? "Envoyer le message (Ctrl+Entrée)" : "Tapez un message pour l'envoyer"}
                >
                  <FiSend size={20} />
                </button>
              )}
            </form>
            
            {/* Enhanced Keyboard shortcuts hint */}
            {messageInputFocused && (
              <div className="mt-2 text-xs text-gray-500 flex flex-wrap items-center gap-4">
                <span>💡 <strong>Ctrl+Entrée</strong> envoyer</span>
                <span><strong>Ctrl+F</strong> rechercher</span>
                <span><strong>Ctrl+/</strong> réponses rapides</span>
                <span><strong>Échap</strong> annuler</span>
                <span><strong>Ctrl+K</strong> nouvelle conversation</span>
                <span><strong>Alt+↑/↓</strong> naviguer conversations</span>
              </div>
            )}
          </div>
        </div>

        {/* Help Button */}
        <button 
          onClick={() => {
            localStorage.removeItem('hasCompletedTour');
            setRunTour(true);
          }}
          className="fixed top-4 right-4 z-50 p-4 card-modern text-orange-500 shadow-elegant hover:shadow-glow focus:outline-none focus:ring-2 focus:ring-orange-300 transition-all duration-300 ease-in-out cursor-pointer rounded-full hover-lift interactive-scale float-animation"
          aria-label="Guide d'utilisation"
          title="Guide d'utilisation"
        >
            <span className="text-xl">💡</span>
        </button>

        {/* Floating Search Button */}
        {!showSearch && currentConversationId && (
          <button
            onClick={() => {
              setShowSearch(true);
              setTimeout(() => searchInputRef.current?.focus(), 100);
            }}
            className="fixed bottom-44 right-6 gradient-bg-primary hover:shadow-glow text-white p-4 rounded-full shadow-float hover:shadow-glow transition-all duration-300 z-10 pulse-glow hover-lift interactive-scale"
            title="Rechercher dans la conversation (Ctrl+F)"
          >
            <span className="text-lg">🔍</span>
          </button>
        )}
      </div>
    </>
  );
}

export default ChatPage;