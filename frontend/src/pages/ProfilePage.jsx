import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-bp-gray-light">
        <div className="p-8 bg-bp-white rounded shadow-md w-full max-w-md text-center">
          <p className="text-bp-gray-dark mb-4">Connectez-vous pour accéder à votre profil.</p>
          <button
            onClick={() => navigate('/login')}
            className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out"
          >
            Se connecter
          </button>
        </div>
      </div>
    );
  }

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-bp-gray-light">
      <div className="p-8 bg-bp-white rounded shadow-md w-full max-w-md">
        <img src="https://www.zonebourse.com/static/private-issuer-squared-9I42B.png" alt="Banque Populaire" className="mx-auto mb-4 h-10" />
        <h2 className="text-xl font-bold mb-6 text-center text-bp-brown">Profil Utilisateur</h2>

        <div className="mb-8">
          <div className="flex justify-between border-b pb-3 mb-3">
            <span className="text-bp-gray-dark font-bold">Nom d'utilisateur:</span>
            <span className="text-bp-brown">{user.username}</span>
          </div>
          
          {user.email && (
            <div className="flex justify-between border-b pb-3 mb-3">
              <span className="text-bp-gray-dark font-bold">Email:</span>
              <span className="text-bp-brown">{user.email}</span>
            </div>
          )}
          
          {user.full_name && (
            <div className="flex justify-between border-b pb-3 mb-3">
              <span className="text-bp-gray-dark font-bold">Nom complet:</span>
              <span className="text-bp-brown">{user.full_name}</span>
            </div>
          )}
          
          <div className="flex justify-between border-b pb-3 mb-3">
            <span className="text-bp-gray-dark font-bold">Rôle:</span>
            <span className="text-bp-brown">{user.is_admin ? 'Administrateur' : 'Utilisateur'}</span>
          </div>
          
          <div className="flex justify-between border-b pb-3 mb-3">
            <span className="text-bp-gray-dark font-bold">Double Authentification:</span>
            <span className={user.two_factor_enabled && user.two_factor_confirmed ? 'text-green-600' : 'text-red-600'}>
              {user.two_factor_enabled && user.two_factor_confirmed ? 'Activée' : 'Désactivée'}
            </span>
          </div>
        </div>

        <div className="mt-8 space-y-4">
          <h3 className="text-lg font-bold text-bp-brown mb-4">Sécurité</h3>
          
          <button 
            onClick={() => navigate('/setup-2fa')}
            className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full mb-3 transition duration-150 ease-in-out"
          >
            {user.two_factor_enabled && user.two_factor_confirmed 
              ? 'Gérer la Double Authentification' 
              : 'Activer la Double Authentification'}
          </button>
          
          {user.is_admin && (
            <button 
              onClick={() => navigate('/admin')}
              className="bg-bp-gray-dark hover:bg-bp-brown text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full mb-3 transition duration-150 ease-in-out"
            >
              Panneau d'Administration
            </button>
          )}
          
          <button
            onClick={() => navigate('/chat')}
            className="bg-bp-gray-light hover:bg-bp-gray text-bp-gray-dark font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full mb-3 transition duration-150 ease-in-out"
          >
            Retour au Chat
          </button>
          
          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="border border-bp-orange-bright text-bp-orange-bright hover:bg-bp-orange hover:text-bp-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full transition duration-150 ease-in-out"
          >
            {isLoggingOut ? 'Déconnexion...' : 'Se déconnecter'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage; 