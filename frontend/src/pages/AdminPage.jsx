// src/pages/AdminPage.jsx
import React, { useState } from 'react';
// --- CORRECTED IMPORT ---
import { useAuth } from '../contexts/AuthContext'; // Correct path: Go up one level then into contexts
// --- END CORRECTION ---
import { useNavigate } from 'react-router-dom';
import { FiBookOpen, FiUsers, FiMessageSquare } from 'react-icons/fi';

// Import Tab Components
import AdminCatalogTab from '../components/AdminCatalogTab';
import AdminUserTab from '../components/AdminUserTab';
import AdminFeedbackTab from '../components/AdminFeedbackTab';


function AdminPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('catalog'); // 'catalog', 'users', 'feedback'

  const renderTabContent = () => {
    switch (activeTab) {
      case 'catalog':
        return <AdminCatalogTab />;
      case 'users':
        return <AdminUserTab />;
      case 'feedback':
        return <AdminFeedbackTab />;
      default:
        return <AdminCatalogTab />;
    }
  };

  const getTabClass = (tabName) => {
    return `py-2 px-4 rounded-t-lg cursor-pointer font-medium transition-colors duration-200 ${
      activeTab === tabName
        ? 'bg-bp-white text-bp-orange-bright border-b-2 border-bp-orange-bright' // Active tab style
        : 'text-bp-gray-dark hover:text-bp-brown hover:bg-bp-gray-light' // Inactive tab style
    }`;
  };

  return (
    <div className="min-h-screen bg-bp-gray-light p-4 md:p-6">
      {/* Header */}
      <header className="mb-6 flex flex-wrap justify-between items-center gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-bp-brown">Admin Dashboard</h1>
        <div className='flex items-center gap-2 flex-wrap'>
          <span className="text-sm text-bp-gray-dark hidden sm:inline">Admin: {user?.username || 'N/A'}</span>
          <button
            onClick={() => navigate('/chat')} // Button to go back to chat
            className="text-sm bg-bp-gray hover:bg-bp-orange hover:text-white text-bp-brown font-semibold py-2 px-4 rounded-md transition duration-200"
          >
            Go to Chat
          </button>
          <button
            onClick={logout}
            className="text-sm bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-md transition duration-200"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Tab Navigation */}
       <div className="mb-4 border-b border-bp-gray">
         <nav className="-mb-px flex space-x-6" aria-label="Tabs">
             <button onClick={() => setActiveTab('catalog')} className={getTabClass('catalog')}>
                 <FiBookOpen className="inline mr-2 mb-1" /> Catalogues Données
             </button>
             <button onClick={() => setActiveTab('users')} className={getTabClass('users')}>
                 <FiUsers className="inline mr-2 mb-1" /> Utilisateurs
             </button>
             <button onClick={() => setActiveTab('feedback')} className={getTabClass('feedback')}>
                 <FiMessageSquare className="inline mr-2 mb-1" /> Feedbacks
             </button>
         </nav>
       </div>

      {/* Tab Content Area */}
      <main className="bg-bp-white p-4 md:p-6 rounded-lg shadow-md">
        {renderTabContent()}
      </main>
    </div>
  );
}

export default AdminPage;