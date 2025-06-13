import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';

function TwoFactorSetupPage() {
  const [setupData, setSetupData] = useState(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState('setup'); // 'setup' or 'verify'
  const [useClientQR, setUseClientQR] = useState(false);
  
  const { setupTwoFactor, confirmTwoFactor, disableTwoFactor, user } = useAuth();
  const navigate = useNavigate();
  
  // Check if user is logged in
  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);
  
  // Fetch 2FA setup data when the component mounts
  useEffect(() => {
    if (user && user.two_factor_enabled && user.two_factor_confirmed) {
      // 2FA is already enabled and confirmed
      setStep('disable');
    } else if (step === 'setup') {
      fetchSetupData();
    }
  }, [user, step]);
  
  const fetchSetupData = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await setupTwoFactor();
      console.log("2FA setup response:", response);
      
      // Extract data correctly from response
      const data = response.data ? response.data : response;
      console.log("2FA setup data:", data);
      
      setSetupData(data);
      
      // Debug QR code data
      if (data && data.qr_code) {
        console.log("QR code exists, length:", data.qr_code.length);
        console.log("QR code preview:", data.qr_code.substring(0, 50) + "...");
      } else {
        console.error("QR code is missing from response data");
        setUseClientQR(true);
      }
    } catch (err) {
      console.error("2FA setup error:", err);
      console.error("Error response data:", err.response?.data);
      console.error("Error message:", err.message);
      setError(err.response?.data?.detail || 'Failed to set up two-factor authentication.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleVerifySubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      await confirmTwoFactor(verificationCode);
      setSuccess('Two-factor authentication has been successfully set up!');
      setStep('success');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid verification code. Please try again.');
      console.error("2FA verification error:", err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDisable = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      await disableTwoFactor();
      setSuccess('Two-factor authentication has been disabled.');
      setStep('setup');
      // Refetch setup data for re-enabling
      fetchSetupData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to disable two-factor authentication.');
      console.error("2FA disable error:", err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle QR code loading error and switch to client-side rendering
  const handleQRCodeError = () => {
    console.error("QR code image failed to load from server");
    setUseClientQR(true);
  };
  
  if (!user) {
    return null; // Will be redirected by the useEffect
  }
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-bp-gray-light">
      <div className="p-8 bg-bp-white rounded shadow-md w-full max-w-md">
        <img src="https://www.zonebourse.com/static/private-issuer-squared-9I42B.png" alt="Banque Populaire" className="mx-auto mb-4 h-10" />
        <h2 className="text-xl font-bold mb-6 text-center text-bp-brown">
          {step === 'disable' ? 'Gestion Double Authentification' : 'Configuration Double Authentification'}
        </h2>
        
        {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
        
        {success && (
          <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 mb-4">
            <p>{success}</p>
          </div>
        )}
        
        {step === 'setup' && (
          <div className="mb-6">
            <p className="text-bp-gray-dark mb-4 text-sm">
              Scannez le code QR ci-dessous avec votre application d'authentification (comme Google Authenticator, Authy ou Microsoft Authenticator).
            </p>
            
            {setupData && (
              <div className="flex justify-center mb-6">
                {!useClientQR && setupData.qr_code ? (
                  <img 
                    src={`data:image/png;base64,${setupData.qr_code}`} 
                    alt="QR Code pour 2FA" 
                    className="border border-bp-gray-light p-2 rounded"
                    onError={handleQRCodeError}
                  />
                ) : setupData.provisioning_uri ? (
                  <div className="border border-bp-gray-light p-4 rounded bg-white">
                    <QRCodeSVG 
                      value={setupData.provisioning_uri}
                      size={200}
                      level="L"
                      includeMargin={true}
                    />
                    <p className="text-xs text-center mt-2 text-bp-gray-dark">Code QR généré côté client</p>
                  </div>
                ) : (
                  <div className="bg-red-100 text-red-700 p-4 rounded">
                    Impossible de générer le code QR. Veuillez utiliser le code secret ci-dessous.
                  </div>
                )}
              </div>
            )}
            
            <div className="text-center">
              {setupData && (
                <div className="mb-4">
                  <p className="text-sm text-bp-gray-dark mb-1">Si vous ne pouvez pas scanner le code QR, entrez ce code manuellement:</p>
                  <p className="font-mono bg-bp-gray-light p-2 rounded select-all text-sm">{setupData.secret}</p>
                </div>
              )}
              
              <button
                type="button"
                onClick={() => setStep('verify')}
                disabled={isLoading || !setupData}
                className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full transition duration-150 ease-in-out"
              >
                {isLoading ? 'Chargement...' : 'Continuer'}
              </button>
            </div>
          </div>
        )}
        
        {step === 'verify' && (
          <form onSubmit={handleVerifySubmit}>
            <p className="text-bp-gray-dark mb-4 text-sm">
              Entrez le code de vérification de votre application d'authentification pour confirmer la configuration.
            </p>
            
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
            
            <div className="flex space-x-4 mb-4">
              <button
                type="button"
                onClick={() => setStep('setup')}
                className="flex-1 bg-bp-gray-light text-bp-gray-dark font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out"
              >
                Retour
              </button>
              
              <button
                type="submit"
                disabled={isLoading}
                className="flex-1 bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out"
              >
                {isLoading ? 'Vérification...' : 'Vérifier et Activer'}
              </button>
            </div>
          </form>
        )}
        
        {step === 'success' && (
          <div className="text-center">
            <p className="text-bp-gray-dark mb-6 text-sm">
              La double authentification a été configurée avec succès. Votre compte est maintenant plus sécurisé.
            </p>
            
            <button
              type="button"
              onClick={() => navigate('/profile')}
              className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full transition duration-150 ease-in-out"
            >
              Aller au profil
            </button>
          </div>
        )}
        
        {step === 'disable' && (
          <div>
            <p className="text-bp-gray-dark mb-4 text-sm">
              La double authentification est actuellement activée pour votre compte.
            </p>
            
            <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
              <div className="flex">
                <svg className="h-5 w-5 text-yellow-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <p className="text-sm">
                  La désactivation de la double authentification rendra votre compte moins sécurisé.
                </p>
              </div>
            </div>
            
            <button
              type="button"
              onClick={handleDisable}
              disabled={isLoading}
              className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 mb-4 rounded focus:outline-none focus:shadow-outline w-full transition duration-150 ease-in-out"
            >
              {isLoading ? 'Désactivation...' : 'Désactiver la double authentification'}
            </button>
            
            <div className="text-center">
              <button
                type="button"
                onClick={() => navigate('/profile')}
                className="text-bp-orange-bright hover:text-bp-orange text-sm font-medium"
              >
                Retour au profil
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default TwoFactorSetupPage; 