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
  const [pendingTwoFactor, setPendingTwoFactor] = useState(null); // Store pending 2FA info

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
      const { access_token, requires_second_factor, user_id } = response.data;
      
      // Check if 2FA is required
      if (requires_second_factor) {
        console.log("2FA required for login");
        // Store the username for the 2FA verification step
        setPendingTwoFactor({ username, user_id });
        return { requiresTwoFactor: true, user_id };
      }
      
      // No 2FA required, proceed with normal login
      localStorage.setItem('authToken', access_token); // Store token
      setToken(access_token);
      // Fetch user data after successful login
      const userResponse = await authService.getCurrentUser();
      const loggedInUser = userResponse.data; // Get user data
      setUser(loggedInUser); // Set user state in context
      console.log("Login successful, user set:", loggedInUser);
      return loggedInUser;
    } catch (error) {
      console.error("Login failed:", error.response?.data || error.message);
      localStorage.removeItem('authToken');
      setToken(null);
      setUser(null);
      throw error; // Re-throw error for the component to handle
    }
  };

  const verifyTwoFactor = async (code) => {
    if (!pendingTwoFactor) {
      console.error("No pending 2FA verification");
      throw new Error("No pending 2FA verification");
    }

    try {
      const { username } = pendingTwoFactor;
      const response = await authService.verifyTwoFactor(username, code);
      const { access_token } = response.data;
      
      localStorage.setItem('authToken', access_token); // Store token
      setToken(access_token);
      
      // Fetch user data after successful 2FA verification
      const userResponse = await authService.getCurrentUser();
      const loggedInUser = userResponse.data;
      setUser(loggedInUser);
      
      // Clear pending 2FA state
      setPendingTwoFactor(null);
      
      console.log("2FA verification successful, user set:", loggedInUser);
      return loggedInUser;
    } catch (error) {
      console.error("2FA verification failed:", error.response?.data || error.message);
      throw error;
    }
  };

  const setupTwoFactor = async () => {
    try {
      const response = await authService.setupTwoFactor();
      console.log("2FA setup API response:", response);
      
      // Check if we have the required fields in the response
      if (response.data && !response.data.qr_code) {
        console.error("QR code missing from API response");
      }
      
      // Return the response data directly to improve handling in the component
      return response;
    } catch (error) {
      console.error("2FA setup failed:", error.response?.data || error.message);
      console.error("Full error object:", error);
      throw error;
    }
  };

  const confirmTwoFactor = async (code) => {
    try {
      const response = await authService.confirmTwoFactor(code);
      // Refresh user data to get updated 2FA status
      const userResponse = await authService.getCurrentUser();
      setUser(userResponse.data);
      return response.data;
    } catch (error) {
      console.error("2FA confirmation failed:", error.response?.data || error.message);
      throw error;
    }
  };

  const disableTwoFactor = async () => {
    try {
      const response = await authService.disableTwoFactor();
      // Refresh user data to get updated 2FA status
      const userResponse = await authService.getCurrentUser();
      setUser(userResponse.data);
      return response.data;
    } catch (error) {
      console.error("2FA disable failed:", error.response?.data || error.message);
      throw error;
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
    setPendingTwoFactor(null);
    // Optionally redirect to login page or clear other state
    // No navigate() here, let the component handle redirection if needed
  };

  // Value provided by the context
  const value = {
    user,
    token,
    loading, // Expose loading state
    pendingTwoFactor,
    login,
    verifyTwoFactor,
    signup,
    logout,
    setupTwoFactor,
    confirmTwoFactor,
    disableTwoFactor
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