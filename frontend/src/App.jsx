// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ChatPage from './pages/ChatPage';
import HomePage from './pages/HomePage';
import AdminPage from './pages/AdminPage';
import TwoFactorVerificationPage from './pages/TwoFactorVerificationPage';
import TwoFactorSetupPage from './pages/TwoFactorSetupPage';
import ProfilePage from './pages/ProfilePage';

// --- Standard Protected Route Component ---
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return user ? children : <Navigate to="/login" replace />;
}

// --- Admin Protected Route Component ---
function AdminProtectedRoute({ children }) {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="flex justify-center items-center h-screen">Loading...</div>;
    }

    // Check if user exists AND is an admin
    if (user && user.is_admin) {
        return children; // Allow access
    } else if (user && !user.is_admin) {
        // Logged in but not admin, redirect to chat (or home)
        return <Navigate to="/chat" replace />;
    } else {
        // Not logged in at all, redirect to login
        return <Navigate to="/login" replace />;
    }
}

// Component to handle redirection for already logged-in users from public pages
function PublicRoute({ children }) {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className="flex justify-center items-center h-screen">Loading...</div>;
    }

    // If user is logged in, redirect from public-only routes (login/signup) to chat
    return !user ? children : <Navigate to="/chat" replace />;
}

function AppRoutes() {
   const { loading } = useAuth(); // Only need loading here

   if (loading) {
     return <div className="flex justify-center items-center h-screen">Loading...</div>; // Or a spinner
   }

  return (
      <Routes>
        {/* Root path now always shows HomePage */}
        <Route path="/" element={<HomePage />} />

        {/* Public Routes (Login/Signup) - Redirect if already logged in */}
        <Route path="/login" element={
            <PublicRoute>
                <LoginPage />
            </PublicRoute>
        } />
        <Route path="/signup" element={
             <PublicRoute>
                <SignupPage />
             </PublicRoute>
        } />
        <Route path="/verify-2fa" element={<TwoFactorVerificationPage />} />

        {/* Protected Routes (Chat - for any logged-in user) */}
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />

        {/* Admin Route (protected) */}
        <Route
          path="/admin"
          element={
            <AdminProtectedRoute>
              <AdminPage />
            </AdminProtectedRoute>
          }
        />

        {/* User Profile Route */}
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />

        {/* 2FA Setup Route (protected) */}
        <Route
          path="/setup-2fa"
          element={
            <ProtectedRoute>
              <TwoFactorSetupPage />
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