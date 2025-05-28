// src/components/AdminCatalogTab.jsx
import React, { useState, useEffect } from 'react';
import { adminService } from '../services/api';
import { FiBookOpen } from 'react-icons/fi';

function AdminCatalogTab() {
    const [catalogInfo, setCatalogInfo] = useState(null);
    const [isLoadingInfo, setIsLoadingInfo] = useState(false);
    const [infoError, setInfoError] = useState('');

    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(''); // '', 'success', 'error'
    const [uploadMessage, setUploadMessage] = useState('');

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

    const handleFileChange = (event) => {
        setSelectedFile(event.target.files[0]);
        setUploadStatus('');
        setUploadMessage('');
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setUploadMessage('Please select a file first.');
            setUploadStatus('error');
            return;
        }

        setIsUploading(true);
        setUploadStatus('');
        setUploadMessage('Uploading and starting background processing...');

        try {
            const response = await adminService.uploadCatalogFile(selectedFile);
            setUploadMessage(response.data.message || 'Upload initiated successfully.');
            setUploadStatus('success');
            setSelectedFile(null); // Clear file input after success
            // Optionally refresh catalog info after a delay
            setTimeout(fetchCatalogInfo, 5000); // Refresh info after 5s
        } catch (error) {
            console.error("Upload failed:", error);
            setUploadMessage(error.response?.data?.detail || 'Upload failed.');
            setUploadStatus('error');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div>
            <h2 className="text-xl font-semibold text-bp-orange mb-4"><FiBookOpen className="inline mr-2" /> Gestion du Catalogue de Données (Qdrant)</h2>

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

            {/* Upload Section */}
            <div className="mb-6">
                 <h3 className="text-lg font-medium text-bp-brown mb-2">Ajouter des données depuis Excel</h3>
                 <div className="flex items-center space-x-4">
                     <input
                         type="file"
                         accept=".xlsx"
                         onChange={handleFileChange}
                         className="block w-full text-sm text-bp-gray-dark file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-bp-orange-tint file:text-bp-orange hover:file:bg-bp-orange/20"
                         disabled={isUploading}
                     />
                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || isUploading}
                        className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-2 px-4 rounded disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                    >
                        {isUploading ? 'Traitement...' : '🚀 Ajouter à Qdrant'}
                    </button>
                 </div>
                 {uploadMessage && (
                     <p className={`mt-2 text-sm ${uploadStatus === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                         {uploadMessage}
                     </p>
                 )}
            </div>
        </div>
    );
}

export default AdminCatalogTab;