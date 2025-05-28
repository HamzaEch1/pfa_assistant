// src/components/AdminConfigTab.jsx
import React, { useState, useEffect } from 'react';
import { adminService } from '../services/api';
import { FiSettings } from 'react-icons/fi';

function AdminConfigTab() {
    const [adminEmail, setAdminEmail] = useState('');
    const [newEmail, setNewEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [updateStatus, setUpdateStatus] = useState('');
    const [updateMessage, setUpdateMessage] = useState('');

    const fetchConfig = async () => {
        setIsLoading(true);
        setError('');
        try {
            const response = await adminService.getAdminConfig();
            setAdminEmail(response.data.admin_email || 'Non défini');
            setNewEmail(response.data.admin_email || ''); // Pre-fill form
        } catch (error) {
            console.error("Failed to fetch admin config:", error);
            setError(error.response?.data?.detail || 'Failed to fetch admin config.');
            setAdminEmail('Erreur');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchConfig();
    }, []);

    const handleUpdateEmail = async (e) => {
        e.preventDefault();
        setUpdateStatus('');
        setUpdateMessage('Mise à jour...');
        if (!newEmail || !newEmail.includes('@')) {
             setUpdateStatus('error');
             setUpdateMessage('Veuillez entrer un email valide.');
             return;
        }
        try {
            await adminService.updateAdminEmail(newEmail);
            setUpdateStatus('success');
            setUpdateMessage('Email administrateur mis à jour avec succès.');
            fetchConfig(); // Refresh displayed email
        } catch (error) {
            console.error("Failed to update admin email:", error);
            setUpdateStatus('error');
            setUpdateMessage(error.response?.data?.detail || 'Échec de la mise à jour.');
        }
    };

    return (
        <div>
            <h2 className="text-xl font-semibold text-bp-orange mb-4"><FiSettings className="inline mr-2" /> Configuration Admin</h2>

            <div className="mb-6 p-4 border border-bp-gray rounded-md bg-bp-gray-light">
                <h3 className="text-lg font-medium text-bp-brown mb-2">Email Administrateur ('admin')</h3>
                 {isLoading && <p>Chargement...</p>}
                 {error && <p className="text-red-600">{error}</p>}
                 {!isLoading && !error && (
                     <p>Email actuel: <strong className="text-bp-brown">{adminEmail}</strong></p>
                 )}

                <form onSubmit={handleUpdateEmail} className="mt-4">
                     <label htmlFor="newAdminEmail" className="block text-sm font-medium text-bp-gray-dark mb-1">
                         Nouvel email pour l'utilisateur 'admin'
                     </label>
                     <div className="flex items-center space-x-2">
                         <input
                             type="email"
                             id="newAdminEmail"
                             value={newEmail}
                             onChange={(e) => setNewEmail(e.target.value)}
                             required
                             className="shadow-sm appearance-none border border-bp-gray rounded w-full py-2 px-3 text-bp-brown leading-tight focus:outline-none focus:ring-2 focus:ring-bp-orange"
                             placeholder="nouvel.email@example.com"
                         />
                         <button
                             type="submit"
                             className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded whitespace-nowrap disabled:opacity-50"
                             disabled={isLoading}
                         >
                             Mettre à jour
                         </button>
                     </div>
                     {updateMessage && (
                        <p className={`mt-2 text-sm ${updateStatus === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                            {updateMessage}
                        </p>
                     )}
                </form>
            </div>
             {/* Add sections for authorized emails or other config if needed */}
        </div>
    );
}

export default AdminConfigTab;