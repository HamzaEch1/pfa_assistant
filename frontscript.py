#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

echo "--- Setting up React Frontend Directory Structure and Files ---"

# Define the frontend directory name
FRONTEND_DIR="frontend"

# Create the main frontend directory
echo "Creating directory: ./${FRONTEND_DIR}"
mkdir -p "${FRONTEND_DIR}"

# Create source structure
echo "Creating source directories..."
mkdir -p "${FRONTEND_DIR}/src/services"
mkdir -p "${FRONTEND_DIR}/src/contexts"
mkdir -p "${FRONTEND_DIR}/src/pages"

# === Populate Files ===

# --- Basic Project Files ---

echo "Creating ./${FRONTEND_DIR}/package.json..."
cat << 'EOF' > "${FRONTEND_DIR}/package.json"
{
  "name": "frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.2", # Ensure latest or specific version
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.23.1" # Ensure latest or specific version
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "eslint-plugin-react": "^7.34.1",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.6",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "vite": "^5.2.0"
  }
}
EOF

echo "Creating ./${FRONTEND_DIR}/index.html..."
cat << 'EOF' > "${FRONTEND_DIR}/index.html"
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RAG Chat Frontend</title> 
 
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
EOF

echo "Creating ./${FRONTEND_DIR}/.env..."
cat << 'EOF' > "${FRONTEND_DIR}/.env"
# Frontend Environment Variables
VITE_API_BASE_URL=http://localhost:8000
EOF

# --- Tailwind CSS Config ---

echo "Creating ./${FRONTEND_DIR}/tailwind.config.js..."
cat << 'EOF' > "${FRONTEND_DIR}/tailwind.config.js"
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Covers files in src directory
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

echo "Creating ./${FRONTEND_DIR}/postcss.config.js..."
cat << 'EOF' > "${FRONTEND_DIR}/postcss.config.js"
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

echo "Creating ./${FRONTEND_DIR}/src/index.css..."
cat << 'EOF' > "${FRONTEND_DIR}/src/index.css"
/* ./src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Optional: Add some base body styling */
body {
  @apply font-sans antialiased text-gray-800 bg-gray-50;
}
EOF

# --- React Code Files ---

echo "Creating ./${FRONTEND_DIR}/src/main.jsx..."
cat << 'EOF' > "${FRONTEND_DIR}/src/main.jsx"
// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css' // Ensure Tailwind CSS is imported

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF

echo "Creating ./${FRONTEND_DIR}/src/App.jsx..."
cat << 'EOF' > "${FRONTEND_DIR}/src/App.jsx"
// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ChatPage from './pages/ChatPage';

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    // Optional: Add a loading spinner or message here
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  // If not loading and no user, redirect to login
  return user ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
   const { user, loading } = useAuth();

   if (loading) {
     return <div className="flex justify-center items-center h-screen">Loading...</div>; // Or a spinner
   }

  return (
      <Routes>
        {/* Redirect root to chat if logged in, otherwise to login */}
        <Route path="/" element={user ? <Navigate to="/chat" replace /> : <Navigate to="/login" replace />} />

        {/* Public Routes */}
        <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/chat" replace />} />
        <Route path="/signup" element={!user ? <SignupPage /> : <Navigate to="/chat" replace />} />

        {/* Protected Routes */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
         {/* Optional: Add a 404 Not Found route */}
         <Route path="*" element={<div className="flex justify-center items-center h-screen">404 Not Found</div>} />
      </Routes>
  );
}


function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
EOF

echo "Creating ./${FRONTEND_DIR}/src/services/api.js..."
cat << 'EOF' > "${FRONTEND_DIR}/src/services/api.js"
// src/services/api.js
import axios from 'axios';

// Get the API base URL from environment variables (defined in .env)
// Fallback to localhost:8000 for development if not set
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create an Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add the JWT token to requests if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken'); // Get token from local storage
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Define API functions
export const authService = {
  login: (username, password) => {
    // FastAPI OAuth2PasswordRequestForm expects form data
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    return apiClient.post('/api/v1/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
  signup: (userData) => {
    // userData should be an object like { username, password, email, full_name }
    return apiClient.post('/api/v1/auth/signup', userData);
  },
  getCurrentUser: () => {
    return apiClient.get('/api/v1/auth/me');
  },
};

export const chatService = {
  startConversation: () => {
    return apiClient.post('/api/v1/chat/conversations');
  },
  getConversations: (skip = 0, limit = 100) => {
    return apiClient.get(`/api/v1/chat/conversations?skip=${skip}&limit=${limit}`);
  },
  getConversation: (conversationId) => {
    return apiClient.get(`/api/v1/chat/conversations/${conversationId}`);
  },
  deleteConversation: (conversationId) => {
    return apiClient.delete(`/api/v1/chat/conversations/${conversationId}`);
  },
  sendMessage: (messageData) => {
    // messageData should be { prompt, conversation_id (optional) }
    return apiClient.post('/api/v1/chat/message', messageData);
  },
};

export default apiClient; // Export the configured instance if needed elsewhere
EOF

echo "Creating ./${FRONTEND_DIR}/src/contexts/AuthContext.jsx..."
cat << 'EOF' > "${FRONTEND_DIR}/src/contexts/AuthContext.jsx"
// src/contexts/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/api'; // Import your API service

// Create the context
const AuthContext = createContext(null);

// Create a provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null); // Store user info (null if not logged in)
  const [token, setToken] = useState(localStorage.getItem('authToken')); // Get initial token from storage
  const [loading, setLoading] = useState(true); // Loading state for initial check

  useEffect(() => {
    // Check if a token exists and try to validate it on initial load
    const validateToken = async () => {
      const storedToken = localStorage.getItem('authToken');
      if (storedToken) {
        try {
          // Set token for subsequent requests made by authService
          setToken(storedToken);
          // Fetch user data using the token
          const response = await authService.getCurrentUser();
          setUser(response.data); // Set user data if token is valid
          console.log("User validated:", response.data);
        } catch (error) {
          console.error("Token validation failed:", error);
          localStorage.removeItem('authToken'); // Clear invalid token
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false); // Finished initial check
    };

    validateToken();
  }, []); // Empty dependency array means run only once on mount

  const login = async (username, password) => {
    try {
      const response = await authService.login(username, password);
      const { access_token } = response.data;
      localStorage.setItem('authToken', access_token); // Store token
      setToken(access_token);
      // Fetch user data after successful login
      const userResponse = await authService.getCurrentUser();
      setUser(userResponse.data);
      console.log("Login successful, user set:", userResponse.data);
      return true; // Indicate success
    } catch (error) {
      console.error("Login failed:", error.response?.data || error.message);
      localStorage.removeItem('authToken');
      setToken(null);
      setUser(null);
      throw error; // Re-throw error for the component to handle
    }
  };

  const signup = async (userData) => {
     try {
       const response = await authService.signup(userData);
       console.log("Signup successful:", response.data);
       // Optionally log the user in automatically after signup
       // await login(userData.username, userData.password);
       return response.data; // Return created user data
     } catch (error) {
       console.error("Signup failed:", error.response?.data || error.message);
       throw error; // Re-throw error
     }
  };

  const logout = () => {
    console.log("Logging out...");
    localStorage.removeItem('authToken'); // Clear token from storage
    setToken(null);
    setUser(null);
    // Optionally redirect to login page or clear other state
  };

  // Value provided by the context
  const value = {
    user,
    token,
    loading, // Expose loading state
    login,
    signup,
    logout,
  };

  // Don't render children until initial token check is complete
  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
EOF

echo "Creating ./${FRONTEND_DIR}/src/pages/LoginPage.jsx..."
cat << 'EOF' > "${FRONTEND_DIR}/src/pages/LoginPage.jsx"
// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom'; // Import for redirection

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate(); // Hook for navigation

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Clear previous errors
    try {
      const success = await login(username, password);
      if (success) {
        navigate('/chat'); // Redirect to chat page on successful login
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check credentials.');
    }
  };

  // Basic form styling with Tailwind - customize as needed
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="p-8 bg-white rounded shadow-md w-full max-w-sm">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Login</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              autoComplete="username"
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              autoComplete="current-password"
            />
          </div>
          {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
          <div className="flex items-center justify-between">
            <button
              type="submit"
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
            >
              Sign In
            </button>
          </div>
          {/* Optional: Add link to Signup Page */}
          <p className="text-center text-gray-600 text-sm mt-4">
            Don't have an account?{' '}
            <button type="button" onClick={() => navigate('/signup')} className="text-blue-500 hover:text-blue-700 font-bold">
                Sign Up
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;
EOF

echo "Creating ./${FRONTEND_DIR}/src/pages/SignupPage.jsx..."
cat << 'EOF' > "${FRONTEND_DIR}/src/pages/SignupPage.jsx"
// src/pages/SignupPage.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function SignupPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState(''); // Optional
    const [fullName, setFullName] = useState(''); // Optional
    const [error, setError] = useState('');
    const { signup } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        // Basic validation
        if (password.length < 6) {
             setError('Password must be at least 6 characters long.');
             return;
        }
        try {
            await signup({ username, password, email: email || null, full_name: fullName || null });
            // Optionally add a success message or auto-login
            navigate('/login'); // Redirect to login after successful signup
        } catch (err) {
            setError(err.response?.data?.detail || 'Signup failed. Please try again.');
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            <div className="p-8 bg-white rounded shadow-md w-full max-w-sm">
                <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Sign Up</h2>
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
                            Username *
                        </label>
                        <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} required className="input-field" />
                    </div>
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="fullName">
                            Full Name
                        </label>
                        <input id="fullName" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-field" />
                    </div>
                    <div className="mb-4">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
                            Email
                        </label>
                        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" />
                    </div>
                    <div className="mb-6">
                        <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
                            Password * (min. 6 chars)
                        </label>
                        <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="input-field" />
                    </div>
                    {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
                    <div className="flex items-center justify-between">
                        <button type="submit" className="btn-primary w-full">
                            Sign Up
                        </button>
                    </div>
                     <p className="text-center text-gray-600 text-sm mt-4">
                        Already have an account?{' '}
                        <button type="button" onClick={() => navigate('/login')} className="text-blue-500 hover:text-blue-700 font-bold">
                            Login
                        </button>
                    </p>
                </form>
            </div>
            {/* Add shared styling for input-field and btn-primary in index.css if desired */}
            <style jsx>{`
                .input-field {
                     box-shadow: appearance;
                     border: 1px solid #e2e8f0; /* Added border for visibility */
                     border-radius: 0.25rem;
                     width: 100%;
                     padding: 0.5rem 0.75rem;
                     color: #4a5568;
                     line-height: 1.25;
                     transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
                }
                .input-field:focus {
                     outline: none;
                     box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
                     border-color: #4299e1;
                }
                .btn-primary {
                    background-color: #4299e1; /* bg-blue-500 */
                    color: white;
                    font-weight: bold;
                    padding: 0.5rem 1rem;
                    border-radius: 0.25rem;
                    transition: background-color 0.15s ease-in-out;
                }
                .btn-primary:hover {
                    background-color: #2b6cb0; /* hover:bg-blue-700 */
                }

            `}</style>
        </div>
    );
}

export default SignupPage;
EOF

echo "Creating ./${FRONTEND_DIR}/src/pages/ChatPage.jsx..."
cat << 'EOF' > "${FRONTEND_DIR}/src/pages/ChatPage.jsx"
// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { chatService } from '../services/api';

function ChatPage() {
  const { user, logout } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]); // Messages for the current conversation
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false); // For message sending/loading
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null); // Ref to scroll to bottom

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
    // Intentionally omitting currentConversationId from dependency array
    // to prevent re-fetching convos list every time a convo is selected.
    // Re-fetch only happens on mount or after logout.
  }, [logout]);


  // Fetch messages when a conversation is selected
  useEffect(() => {
    const fetchMessages = async () => {
      if (!currentConversationId) {
        setMessages([]); // Clear messages if no conversation selected
        return;
      }
      setIsLoading(true); // Indicate loading messages
      setError('');
      try {
        const response = await chatService.getConversation(currentConversationId);
        setMessages(response.data.messages || []);
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
    }
  };

  const handleNewConversation = async () => {
    setIsLoading(true);
    setError('');
    try {
       const response = await chatService.startConversation();
       const newConv = response.data;
       // Add new convo and select it
       setConversations(prev => [newConv, ...prev].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
       setCurrentConversationId(newConv.id);
       setMessages([]); // New conversation starts empty
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
          }
      } catch (err) {
          console.error("Failed to delete conversation:", err);
          setError('Could not delete conversation.');
          if (err.response?.status === 401) logout();
      }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || isLoading || !currentConversationId) return;

    const userMessage = { role: 'user', content: newMessage };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = newMessage; // Store current input before clearing
    setNewMessage(''); // Clear input field immediately
    setIsLoading(true);
    setError('');

    try {
      const response = await chatService.sendMessage({
        prompt: userMessage.content,
        conversation_id: currentConversationId,
      });

      const assistantMessage = response.data.assistant_message;
      setMessages(prev => [...prev, assistantMessage]);

      // Update conversation list timestamp/title (more robust approach)
      const updatedConvResponse = await chatService.getConversation(currentConversationId);
      const updatedConvData = updatedConvResponse.data;
      if (updatedConvData) {
            setConversations(prevConvos => prevConvos.map(conv =>
                conv.id === currentConversationId ? updatedConvData : conv
            ).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))); // Re-sort
       }

    } catch (err) {
      console.error("Failed to send message:", err);
      setError('Failed to send message. Please try again.');
      // Restore input and remove optimistic user message on error
      setNewMessage(currentInput);
      setMessages(prev => prev.filter(msg => msg !== userMessage));
       if (err.response?.status === 401) logout();
    } finally {
      setIsLoading(false);
      // Use timeout to ensure DOM has updated before scrolling
       setTimeout(scrollToBottom, 50);
    }
  };

  // Render basic structure - enhance with Tailwind styling
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 text-white p-4 flex flex-col flex-shrink-0">
        <h2 className="text-xl font-semibold mb-4">Conversations</h2>
        <button
          onClick={handleNewConversation}
          className="mb-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded w-full transition duration-150 ease-in-out"
          disabled={isLoading}
        >
          + New Chat
        </button>
        <div className="flex-grow overflow-y-auto pr-1"> {/* Added padding-right for scrollbar */}
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className={`p-2 mb-1 rounded cursor-pointer flex justify-between items-center text-sm transition duration-150 ease-in-out ${
                currentConversationId === conv.id ? 'bg-gray-600' : 'hover:bg-gray-700'
              }`}
            >
              <span className="truncate flex-grow mr-2">{conv.title || `Chat ${conv.id.substring(0, 6)}`}</span>
               <button
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    className="text-gray-400 hover:text-red-500 text-xs font-bold flex-shrink-0 px-1 py-0.5 rounded"
                    title="Delete Conversation"
                    disabled={isLoading}
                >
                    ✕
                </button>
            </div>
          ))}
        </div>
        <div className="mt-auto pt-4 border-t border-gray-700">
            <p className="text-sm mb-2 truncate" title={user?.username}>Logged in as: {user?.username || 'User'}</p>
            <button onClick={logout} className="bg-red-600 hover:bg-red-700 text-white font-bold py-1 px-3 rounded w-full text-sm transition duration-150 ease-in-out">
                Logout
            </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentConversationId ? (
          <>
            {/* Chat Messages Area */}
            <div className="flex-grow overflow-y-auto p-4 bg-white shadow-inner">
              {messages.map((msg, index) => (
                <div key={index} className={`mb-4 flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`py-2 px-4 rounded-lg max-w-xl shadow ${
                    msg.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}>
                    {/* Render newlines correctly */}
                    {msg.content.split('\n').map((line, i) => (
                      <span key={i} className="block whitespace-pre-wrap">{line}</span>
                    ))}
                  </div>
                </div>
              ))}
               {/* Loading indicator for assistant response */}
               {isLoading && messages[messages.length - 1]?.role === 'user' && (
                   <div className="mb-4 flex justify-start">
                       <div className="py-2 px-4 rounded-lg max-w-lg bg-gray-200 text-gray-500 italic shadow animate-pulse">
                           Thinking...
                       </div>
                   </div>
               )}
               {/* Invisible element to scroll to */}
               <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-gray-100 border-t border-gray-200">
                 {error && <p className="text-red-500 text-sm mb-2 text-center">{error}</p>}
                <form onSubmit={handleSendMessage} className="flex items-center">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-grow border rounded-l-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isLoading}
                    autoComplete="off"
                  />
                  <button
                    type="submit"
                    className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-r-md disabled:opacity-50 transition duration-150 ease-in-out"
                    disabled={isLoading || !newMessage.trim()}
                  >
                    Send
                  </button>
                </form>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500 bg-white">
            {isLoading ? 'Loading conversations...' : 'Select a conversation or start a new one.'}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatPage;
EOF


echo "--- Frontend Setup Script Finished ---"
echo ""
echo "Next steps:"
echo "1. Make this script executable: chmod +x setup_frontend.sh (if you saved it to a file)"
echo "2. Run the script: ./setup_frontend.sh"
echo "3. Navigate into the new directory: cd ${FRONTEND_DIR}"
echo "4. Install dependencies: npm install (or yarn install)"
echo "5. Start the development server: npm run dev (or yarn dev)"
echo "6. Open your browser to the specified URL (usually http://localhost:5173)"
echo ""
echo "Make sure your FastAPI backend (docker-compose up) is running on port 8000!"
echo ""
