// src/components/AdminCatalogTab.jsx
import React, { useState, useEffect } from 'react';
import { adminService } from '../services/api';
import { FiBookOpen } from 'react-icons/fi';

function AdminCatalogTab() {
    const [catalogInfo, setCatalogInfo] = useState(null);
    const [isLoadingInfo, setIsLoadingInfo] = useState(false);
    const [infoError, setInfoError] = useState('');

    const fetchCatalogInfo = async () => {
        setIsLoadingInfo(true);
        setInfoError('');
        try {
            const response = await adminService.getCatalogInfo();
            setCatalogInfo(response.data);
        } catch (error) {
            console.error("Failed to fetch catalog info:", error);
            setInfoError(error.response?.data?.detail || 'Failed to fetch catalog info.');
        } finally {
            setIsLoadingInfo(false);
        }
    };

    // Fetch info on component mount
    useEffect(() => {
        fetchCatalogInfo();
    }, []);

    return (
        <div>
            <h2 className="text-xl font-semibold text-bp-orange mb-4"><FiBookOpen className="inline mr-2" /> Gestion du Catalogue de Données </h2>

            {/* Catalog Info Section */}
            <div className="mb-6 p-4 border border-bp-gray rounded-md bg-bp-gray-light">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-lg font-medium text-bp-brown">Informations Collection</h3>
                    <button
                        onClick={fetchCatalogInfo}
                        disabled={isLoadingInfo}
                        className="text-sm bg-bp-orange hover:bg-bp-orange-bright text-white py-1 px-3 rounded disabled:opacity-50"
                    >
                        {isLoadingInfo ? 'Chargement...' : 'Actualiser'}
                    </button>
                </div>
                {isLoadingInfo && <p className="text-bp-gray-dark">Chargement des informations...</p>}
                {infoError && <p className="text-red-600">{infoError}</p>}
                {catalogInfo && !isLoadingInfo && !infoError && (
                    <div className="grid grid-cols-2 gap-4">
                        <p><strong className="text-bp-brown">Nom:</strong> {catalogInfo.collection_name}</p>
                        <p><strong className="text-bp-brown">Points (Vecteurs):</strong> {catalogInfo.points_count ?? 'N/A'}</p>
                        <p><strong className="text-bp-brown">Dimension:</strong> {catalogInfo.vectors_dimension ?? 'N/A'}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AdminCatalogTab;