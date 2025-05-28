// src/components/AdminUserTab.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { adminService } from '../services/api';
import { useAuth } from '../contexts/AuthContext'; // To prevent self-delete
import { FiUsers } from 'react-icons/fi';

function AdminUserTab() {
    const { user: currentAdminUser } = useAuth(); // Get current admin user
    const [users, setUsers] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [actionStatus, setActionStatus] = useState({}); // To show status per user action

    const fetchUsers = useCallback(async () => {
        setIsLoading(true);
        setError('');
        setActionStatus({});
        try {
            const response = await adminService.getUsers();
            setUsers(response.data);
        } catch (error) {
            console.error("Failed to fetch users:", error);
            setError(error.response?.data?.detail || 'Failed to fetch users.');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleDeleteUser = async (username) => {
        if (username === currentAdminUser?.username) {
            setActionStatus(prev => ({ ...prev, [username]: { error: 'Cannot delete self.' } }));
            return;
        }
        if (!window.confirm(`Are you sure you want to delete user '${username}'? This cannot be undone.`)) {
            return;
        }

        setActionStatus(prev => ({ ...prev, [username]: { loading: true } }));
        try {
            await adminService.deleteUser(username);
            setActionStatus(prev => ({ ...prev, [username]: { success: 'Deleted!' } }));
            // Refresh users list after deletion
            fetchUsers();
        } catch (error) {
            console.error(`Failed to delete user ${username}:`, error);
            setActionStatus(prev => ({ ...prev, [username]: { error: error.response?.data?.detail || 'Deletion failed.' } }));
        }
        // Optionally clear status after a few seconds
        // setTimeout(() => setActionStatus(prev => ({...prev, [username]: null })), 3000);
    };

    // Add function for toggling admin status if needed
    const handleToggleAdmin = async (username, currentIsAdmin) => {
        // Add safety checks if needed (e.g., prevent demoting the last admin)
         if (username === 'admin' && currentIsAdmin) { // Example: prevent demoting 'admin'
             setActionStatus(prev => ({ ...prev, [username]: { error: "Cannot change primary admin status." } }));
             return;
         }
         const newAdminStatus = !currentIsAdmin;
         setActionStatus(prev => ({ ...prev, [username]: { loading: true } }));
         try {
             await adminService.setUserAdminStatus(username, newAdminStatus);
             setActionStatus(prev => ({ ...prev, [username]: { success: `Admin status set to ${newAdminStatus}.` } }));
             // Refresh users list
             fetchUsers();
         } catch (error) {
             console.error(`Failed to toggle admin for ${username}:`, error);
             setActionStatus(prev => ({ ...prev, [username]: { error: error.response?.data?.detail || 'Status update failed.' } }));
         }
    };


    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-bp-orange"><FiUsers className="inline mr-2" /> Gestion des Utilisateurs</h2>
                <button
                    onClick={fetchUsers}
                    disabled={isLoading}
                    className="text-sm bg-bp-orange hover:bg-bp-orange-bright text-white py-1 px-3 rounded disabled:opacity-50"
                >
                    {isLoading ? 'Chargement...' : 'Actualiser'}
                </button>
            </div>
            {error && <p className="text-red-600 mb-4">{error}</p>}
            {isLoading && users.length === 0 && <p className="text-bp-gray-dark">Chargement des utilisateurs...</p>}
            {!isLoading && users.length === 0 && !error && <p className="text-bp-gray-dark">Aucun utilisateur trouvé.</p>}

            {users.length > 0 && (
                <div className="overflow-x-auto bg-bp-white rounded shadow">
                    <table className="min-w-full divide-y divide-bp-gray">
                        <thead className="bg-bp-gray-light">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Username</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Nom Complet</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Email</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Admin</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Actif</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Créé le</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-bp-white divide-y divide-bp-gray">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-bp-gray-light/50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-bp-gray-dark">{u.id}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-bp-brown">{u.username}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-bp-gray-dark">{u.full_name || '-'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-bp-gray-dark">{u.email || '-'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-bp-gray-dark">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.is_admin ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                            {u.is_admin ? 'Oui' : 'Non'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-bp-gray-dark">
                                         <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {u.is_active ? 'Oui' : 'Non'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-bp-gray-dark">
                                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                        <button
                                            onClick={() => handleToggleAdmin(u.username, u.is_admin)}
                                            disabled={actionStatus[u.username]?.loading}
                                            className={`text-xs ${u.is_admin ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-green-500 hover:bg-green-600'} text-white py-1 px-2 rounded disabled:opacity-50`}
                                            title={u.is_admin ? 'Retirer Admin' : 'Promouvoir Admin'}
                                        >
                                            {actionStatus[u.username]?.loading ? '...' : (u.is_admin ? 'Rétrograder' : 'Admin')}
                                        </button>
                                        <button
                                            onClick={() => handleDeleteUser(u.username)}
                                            disabled={actionStatus[u.username]?.loading || u.username === currentAdminUser?.username}
                                            className="text-xs bg-red-600 hover:bg-red-700 text-white py-1 px-2 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                            title={u.username === currentAdminUser?.username ? 'Cannot delete self' : 'Supprimer Utilisateur'}
                                        >
                                           {actionStatus[u.username]?.loading ? '...' : 'Supprimer'}
                                        </button>
                                         {actionStatus[u.username]?.error && <p className="text-red-500 text-xs mt-1">{actionStatus[u.username].error}</p>}
                                         {actionStatus[u.username]?.success && <p className="text-green-500 text-xs mt-1">{actionStatus[u.username].success}</p>}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default AdminUserTab;