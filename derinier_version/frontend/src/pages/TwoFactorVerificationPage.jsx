import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

function TwoFactorVerificationPage() {
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { verifyTwoFactor, pendingTwoFactor } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Check if we have the necessary data for verification
  useEffect(() => {
    if (!pendingTwoFactor && !location.state?.username) {
      // No 2FA verification pending, redirect to login
      navigate('/login');
    }
  }, [pendingTwoFactor, navigate, location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    if (!verificationCode.trim()) {
      setError('Please enter the verification code');
      setIsLoading(false);
      return;
    }
    
    try {
      const user = await verifyTwoFactor(verificationCode);
      // Successful verification, user contains the logged in user data
      if (user.is_admin) {
        navigate('/admin');
      } else {
        navigate('/chat');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid verification code. Please try again.');
      console.error("2FA verification error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // If we don't have a pending verification, don't render the form
  if (!pendingTwoFactor && !location.state?.username) {
    return null; // Will be redirected by the useEffect
  }
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-bp-gray-light">
      <div className="p-8 bg-bp-white rounded shadow-md w-full max-w-sm">
        <img src="https://www.zonebourse.com/static/private-issuer-squared-9I42B.png" alt="Banque Populaire" className="mx-auto mb-4 h-10" />
        <h2 className="text-xl font-bold mb-6 text-center text-bp-brown">Double Authentification</h2>
        
        <p className="text-bp-gray-dark mb-6 text-center text-sm">
          Veuillez entrer le code de vérification depuis votre application d'authentification.
        </p>
        
        {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-bp-gray-dark text-sm font-bold mb-2" htmlFor="code">
              Code de vérification
            </label>
            <input
              id="code"
              name="code"
              type="text"
              autoComplete="one-time-code"
              required
              className="shadow appearance-none border rounded w-full py-2 px-3 text-bp-brown leading-tight focus:outline-none focus:ring-2 focus:ring-bp-orange focus:border-transparent"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value)}
              placeholder="Entrez le code à 6 chiffres"
              maxLength={6}
            />
          </div>
          
          <div className="flex items-center justify-between mb-4">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full transition duration-150 ease-in-out"
            >
              {isLoading ? 'Vérification...' : 'Vérifier'}
            </button>
          </div>
          
          <div className="text-center">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-bp-orange-bright hover:text-bp-orange text-sm font-medium"
            >
              Retour à la connexion
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TwoFactorVerificationPage; 