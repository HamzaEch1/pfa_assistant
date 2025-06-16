import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

// Configuration de Mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'arial',
});

const MermaidDiagram = ({ chart }) => {
  const mermaidRef = useRef(null);

  useEffect(() => {
    if (chart && mermaidRef.current) {
      mermaid.render('mermaid-diagram', chart).then(({ svg }) => {
        mermaidRef.current.innerHTML = svg;
      }).catch(error => {
        console.error('Erreur lors du rendu du diagramme Mermaid:', error);
        mermaidRef.current.innerHTML = 'Erreur lors du rendu du diagramme';
      });
    }
  }, [chart]);

  return (
    <div className="mermaid-diagram-container my-4 p-4 bg-white rounded-lg shadow">
      <div ref={mermaidRef} className="mermaid-diagram"></div>
    </div>
  );
};

export default MermaidDiagram; 