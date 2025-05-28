// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/api'; // Import authService if needed for direct call (but context handles it)

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth(); // login now returns the user object or 2FA info
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Clear previous errors
    setIsLoading(true);
    
    try {
      const result = await login(username, password);
      
      // Check if 2FA is required
      if (result && result.requiresTwoFactor) {
        // Navigate to 2FA verification page with username
        navigate('/verify-2fa', { state: { username } });
        return;
      }
      
      // Regular login success
      if (result) {
        // Check if the logged-in user is an admin
        if (result.is_admin) {
            console.log("Admin user detected, navigating to /admin");
            navigate('/admin'); // Redirect admin to admin page
        } else {
             console.log("Non-admin user detected, navigating to /chat");
            navigate('/chat'); // Redirect non-admin to chat page
        }
      }
      // If login fails, the catch block will handle it
    } catch (err) {
      // Error handling remains the same
      setError(err.response?.data?.detail || 'Login failed. Please check credentials.');
      console.error("Login handleSubmit error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Apply Banque Populaire Theme ---
  // Using the theme colors defined in tailwind.config.js

  return (
    <div className="flex items-center justify-center min-h-screen bg-bp-gray-light"> {/* Use theme gray */}
      <div className="p-8 bg-bp-white rounded shadow-md w-full max-w-sm"> {/* Use theme white */}
         {/* Updated Logo src to use URL */}
         <img src="https://www.zonebourse.com/static/private-issuer-squared-9I42B.png" alt="Banque Populaire" className="mx-auto mb-4 h-10" /> {/* Adjusted margin/height */}
        <h2 className="text-xl font-bold mb-6 text-center text-bp-brown">Connexion</h2> {/* Changed Title Text and Size */}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-bp-gray-dark text-sm font-bold mb-2" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="shadow appearance-none border rounded w-full py-2 px-3 text-bp-brown leading-tight focus:outline-none focus:ring-2 focus:ring-bp-orange focus:border-transparent" // Use theme colors for focus/text
              autoComplete="username"
            />
          </div>
          <div className="mb-6">
            <label className="block text-bp-gray-dark text-sm font-bold mb-2" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="shadow appearance-none border rounded w-full py-2 px-3 text-bp-brown mb-3 leading-tight focus:outline-none focus:ring-2 focus:ring-bp-orange focus:border-transparent" // Use theme colors for focus/text
              autoComplete="current-password"
            />
          </div>
          {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
          <div className="flex items-center justify-between">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full transition duration-150 ease-in-out" // Use theme colors
            >
              {isLoading ? 'Connexion en cours...' : 'Connexion'}
            </button>
          </div>
          {/* Link to Signup Page */}
          <p className="text-center text-bp-gray-dark text-sm mt-4">
            Don't have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/signup')}
              className="text-bp-orange-bright hover:text-bp-orange font-bold" // Use theme colors
            >
                Sign Up
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;