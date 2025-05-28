import React, { useState, useEffect, useMemo } from 'react';
import { FiPieChart, FiX } from "react-icons/fi";

function AdminFeedbackStats({ feedbackData, onClose }) {
    // Calculer les statistiques des feedbacks
    const stats = useMemo(() => {
        if (!feedbackData || feedbackData.length === 0) {
            return { total: 0, up: 0, down: 0, problemCategories: {} };
        }

        // Compter les likes et dislikes
        const up = feedbackData.filter(item => item.rating === 'up').length;
        const down = feedbackData.filter(item => item.rating === 'down').length;
        
        // Compter la distribution des catégories de problèmes
        const problemCategories = {};
        feedbackData
            .filter(item => item.rating === 'down' && item.category)
            .forEach(item => {
                const category = item.category || 'Non catégorisé';
                problemCategories[category] = (problemCategories[category] || 0) + 1;
            });

        return {
            total: feedbackData.length,
            up,
            down,
            problemCategories
        };
    }, [feedbackData]);

    // Créer les données pour le graphique circulaire principal
    const mainChartData = [
        { label: 'Likes', value: stats.up, color: '#CC5500' },  // green-500
        { label: 'Dislikes', value: stats.down, color: '#EF9B0F' }  // red-500
    ];

    // Couleurs inspirées de l'image fournie
    const chartColors = [
        '#D5C2A5',  
        '#F7E3B3',  // Beige clair
        '#E67E43',  // Orange
        '#8B4513',  // Marron
        '#F0D860',  // Jaune
        '#D3D3D3',  // Gris moyen
        '#FFB6C1',  // Rose clair
        '#6F8FAF'   // Bleu-gris
    ];

    // Créer les données pour le graphique circulaire des problèmes
    const problemChartData = Object.entries(stats.problemCategories).map(([category, count], index) => {
        return {
            label: category,
            value: count,
            color: chartColors[index % chartColors.length]
        };
    }).sort((a, b) => b.value - a.value); // Trier par nombre décroissant

    // Fonction pour dessiner un diagramme circulaire avec canvas - style standard
    const renderMainPieChart = (canvasRef, data) => {
        if (!canvasRef.current || data.length === 0 || data.every(item => item.value === 0)) return;
        
        const ctx = canvasRef.current.getContext('2d');
        const canvas = canvasRef.current;
        const totalValue = data.reduce((sum, item) => sum + item.value, 0);
        
        // Effacer le canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) * 0.8;
        
        let startAngle = 0;
        
        // Dessiner chaque segment
        data.forEach((item) => {
            if (item.value === 0) return;
            
            const sliceAngle = (item.value / totalValue) * 2 * Math.PI;
            const endAngle = startAngle + sliceAngle;
            
            // Dessiner le segment
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.fillStyle = item.color;
            ctx.fill();
            
            startAngle = endAngle;
        });

        // Ajouter des étiquettes si nécessaire
        if (data.length <= 5) {  // Limiter les étiquettes pour éviter l'encombrement
            startAngle = 0;
            data.forEach((item) => {
                if (item.value === 0) return;
                
                const sliceAngle = (item.value / totalValue) * 2 * Math.PI;
                const midAngle = startAngle + sliceAngle / 2;
                const textX = centerX + Math.cos(midAngle) * (radius * 0.7);
                const textY = centerY + Math.sin(midAngle) * (radius * 0.7);
                
                ctx.fillStyle = 'white';
                ctx.font = 'bold 14px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                
                // Calculer le pourcentage
                const percentage = Math.round((item.value / totalValue) * 100);
                if (percentage > 8) {  // N'afficher que si assez d'espace
                    ctx.fillText(`${percentage}%`, textX, textY);
                }
                
                startAngle += sliceAngle;
            });
        }
    };

    // Fonction pour dessiner un diagramme circulaire simplifié avec pourcentages à l'intérieur
    const renderSimplePieChart = (canvasRef, data) => {
        if (!canvasRef.current || data.length === 0 || data.every(item => item.value === 0)) return;
        
        const ctx = canvasRef.current.getContext('2d');
        const canvas = canvasRef.current;
        const totalValue = data.reduce((sum, item) => sum + item.value, 0);
        
        // Effacer le canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) * 0.7;
        
        let startAngle = 0;
        
        // Dessiner chaque segment
        data.forEach((item) => {
            if (item.value === 0) return;
            
            const sliceAngle = (item.value / totalValue) * 2 * Math.PI;
            const endAngle = startAngle + sliceAngle;
            
            // Dessiner le segment
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.fillStyle = item.color;
            ctx.fill();
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 1;
            ctx.stroke();
            
            // Calculer la position pour le pourcentage (à l'intérieur du segment)
            const midAngle = startAngle + sliceAngle / 2;
            const percentage = Math.round((item.value / totalValue) * 100);
            
            // Seulement pour les segments qui ont assez d'espace
            if (percentage >= 3) {
                // Position du texte à l'intérieur du segment
                const textRadius = radius * 0.65; // Position à environ 65% du rayon pour être à l'intérieur
                const textX = centerX + Math.cos(midAngle) * textRadius;
                const textY = centerY + Math.sin(midAngle) * textRadius;
                
                // Afficher le pourcentage
                ctx.font = 'bold 14px Arial';
                ctx.fillStyle = 'white'; // Texte blanc pour contraster avec le fond coloré
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`${percentage}%`, textX, textY);
            }
            
            startAngle = endAngle;
        });
    };

    // Créer des refs pour les canvas
    const mainChartRef = React.useRef(null);
    const problemChartRef = React.useRef(null);
    
    // Dessiner les graphiques quand les données changent
    useEffect(() => {
        renderMainPieChart(mainChartRef, mainChartData);
        
        if (stats.down > 0) {
            renderSimplePieChart(problemChartRef, problemChartData);
        }
    }, [stats, mainChartData, problemChartData]);

    return (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-bp-orange"><FiPieChart className="inline mr-2" /> Statistiques des Feedbacks</h2>
                    <button 
                        onClick={onClose}
                        className="text-gray-500 hover:text-gray-700"
                    >
                        <FiX size={24} />
                    </button>
                </div>

                <div className="flex flex-col md:flex-row gap-8">
                    {/* Diagramme principal */}
                    <div className="flex-1">
                        <h3 className="text-lg font-medium mb-4 text-center">Distribution des Feedbacks</h3>
                        <div className="flex flex-col items-center">
                            <div className="relative mb-4">
                                <canvas ref={mainChartRef} width={280} height={280} className="mb-4"></canvas>
                                {stats.total > 0 ? (
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <span className="text-2xl font-bold">{stats.total}</span>
                                        <span className="text-sm">Total</span>
                                    </div>
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <span className="text-lg text-gray-500">Aucun feedback</span>
                                    </div>
                                )}
                            </div>
                            
                            {/* Légende */}
                            <div className="flex justify-center gap-6 mt-2">
                                {mainChartData.map((item, index) => (
                                    <div key={index} className="flex items-center">
                                        <div className="w-4 h-4 mr-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                                        <span className="font-medium">{item.label}: {item.value}</span>
                                        <span className="ml-1 text-gray-500">
                                            ({stats.total > 0 ? Math.round((item.value / stats.total) * 100) : 0}%)
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Détails des problèmes - avec légende en dessous */}
                    {stats.down > 0 ? (
                        <div className="flex-1 border-t md:border-t-0 md:border-l border-gray-200 pt-6 md:pt-0 md:pl-8">
                            <h3 className="text-lg font-medium mb-4 text-center">Types de Problèmes Signalés</h3>
                            
                            <div className="flex flex-col items-center">
                                {/* Graphique au centre */}
                                <div className="w-full md:w-4/5 mx-auto">
                                    <canvas ref={problemChartRef} width={280} height={280} className="mx-auto"></canvas>
                                </div>
                                
                                {/* Légende en dessous */}
                                <div className="w-full mt-5">
                                    <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto">
                                        {problemChartData.map((item, index) => (
                                            <div key={index} className="flex items-center">
                                                <div className="w-4 h-4 mr-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                                                <div className="flex-1 mr-2">
                                                    <span className="font-medium text-sm">{item.label}</span>
                                                </div>
                                                <div className="text-sm text-gray-700 whitespace-nowrap">
                                                    {item.value} ({Math.round((item.value / stats.down) * 100)}%)
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 border-t md:border-t-0 md:border-l border-gray-200 pt-6 md:pt-0 md:pl-8 flex items-center justify-center">
                            <div className="text-center p-4 bg-gray-50 rounded-lg w-full">
                                <p>Aucun dislike n'a été enregistré pour l'instant.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default AdminFeedbackStats; 