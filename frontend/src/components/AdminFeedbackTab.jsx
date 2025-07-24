// src/components/AdminFeedbackTab.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { adminService } from '../services/api';
import { FiThumbsUp, FiThumbsDown, FiMessageSquare, FiBarChart2 } from "react-icons/fi";
import AdminFeedbackStats from './AdminFeedbackStats';

function AdminFeedbackTab() {
    const [feedback, setFeedback] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [showStats, setShowStats] = useState(false);

    const fetchFeedback = useCallback(async () => {
        setIsLoading(true);
        setError('');
        try {
            const response = await adminService.getFeedback();
            // Map field names if aliases didn't work perfectly or for display consistency
             const mappedData = response.data.map(item => ({
                 conversationId: item['ID Conversation'],
                 messageIndex: item['Index Message'],
                 user: item['Utilisateur'],
                 conversationDate: item['Date Conversation'],
                 rating: item['Feedback Note'],
                 category: item['Catégorie Problème'],
                 details: item['Détails Feedback'],
                 assistantMessage: item['Message Assistant'],
                 userQuestion: item['Question Utilisateur'],
                 // Keep original keys if needed for delete action
                 original_conv_id: item['ID Conversation'],
                 original_msg_idx: item['Index Message']
             }));
            setFeedback(mappedData);
        } catch (error) {
            console.error("Failed to fetch feedback:", error);
            setError(error.response?.data?.detail || 'Failed to fetch feedback.');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchFeedback();
    }, [fetchFeedback]);

    const toggleStats = () => {
        setShowStats(!showStats);
    };

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                 <h2 className="text-xl font-semibold text-bp-orange"><FiMessageSquare className="inline mr-2" /> Feedbacks Utilisateurs</h2>
                 <div className="flex space-x-2">
                     <button
                        onClick={toggleStats}
                        className="text-sm bg-bp-blue hover:bg-bp-blue-bright text-white p-2 rounded disabled:opacity-50 flex items-center"
                        title="Afficher/Masquer les statistiques"
                     >
                        {/* <FiBarChart2 className="mr-1" /> Statistiques */}
                        <img src="https://cdn-icons-png.flaticon.com/512/2920/2920326.png" alt="Statistiques" className="h-5 w-5" />
                     </button>
                 <button
                    onClick={fetchFeedback}
                    disabled={isLoading}
                    className="text-sm bg-bp-orange hover:bg-bp-orange-bright text-white py-1 px-3 rounded disabled:opacity-50"
                >
                    {isLoading ? 'Chargement...' : 'Actualiser'}
                </button>
                 </div>
            </div>
            {error && <p className="text-red-600 mb-4">{error}</p>}
            {isLoading && feedback.length === 0 && <p className="text-bp-gray-dark">Chargement des feedbacks...</p>}
             {!isLoading && feedback.length === 0 && !error && <p className="text-bp-gray-dark">Aucun feedback trouvé.</p>}

            {showStats && <AdminFeedbackStats feedbackData={feedback} onClose={toggleStats} />}

            {feedback.length > 0 && (
                 <div className="overflow-x-auto bg-bp-white rounded shadow">
                     <table className="min-w-full divide-y divide-bp-gray">
                         <thead className="bg-bp-gray-light">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Utilisateur</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Date</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Note</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Catégorie</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Détails</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Question</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-bp-brown uppercase tracking-wider">Réponse Assistant</th>
                             </tr>
                         </thead>
                         <tbody className="bg-bp-white divide-y divide-bp-gray">
                            {feedback.map((item, index) => {
                                return (
                                <tr key={`${item.original_conv_id}-${item.original_msg_idx}`} className="hover:bg-bp-gray-light/50">
                                     <td className="px-4 py-4 whitespace-nowrap text-sm text-bp-gray-dark">{item.user}</td>
                                     <td className="px-4 py-4 whitespace-nowrap text-sm text-bp-gray-dark">{new Date(item.conversationDate).toLocaleString()}</td>
                                     <td className="px-4 py-4 whitespace-nowrap text-sm">
                                        {item.rating === 'up' && <FiThumbsUp size={16} className="text-green-700" />}
                                        {item.rating === 'down' && <FiThumbsDown size={16} className="text-red-700" />}
                                        
                                     </td>
                                     <td className="px-4 py-4 whitespace-nowrap text-sm text-bp-gray-dark">{item.category || '-'}</td>
                                     <td className="px-4 py-4 text-sm text-bp-gray-dark min-w-[150px] max-w-[300px] overflow-hidden text-ellipsis whitespace-nowrap" title={item.details}>{item.details || '-'}</td>
                                     <td className="px-4 py-4 text-sm text-bp-gray-dark min-w-[150px] max-w-[300px] overflow-hidden text-ellipsis whitespace-nowrap" 
                                         title={item.userQuestion}>
                                         {item.userQuestion && item.userQuestion !== '-' 
                                            ? (item.userQuestion.length > 50 
                                                ? `${item.userQuestion.slice(0, 50)}...` 
                                                : item.userQuestion)
                                            : '-'}
                                     </td>
                                     <td className="px-4 py-4 text-sm text-bp-gray-dark min-w-[200px] max-w-[400px] overflow-hidden text-ellipsis whitespace-nowrap" 
                                         title={item.assistantMessage}>
                                         <div dangerouslySetInnerHTML={{ 
                                             __html: item.assistantMessage && item.assistantMessage.length > 60 
                                                ? `${item.assistantMessage.slice(0, 60)}...` 
                                                : item.assistantMessage 
                                         }} />
                                     </td>
                                 </tr>
                             );
                            })}
                         </tbody>
                     </table>
                 </div>
             )}
        </div>
    );
}

export default AdminFeedbackTab;