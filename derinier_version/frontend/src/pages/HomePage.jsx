// src/pages/HomePage.jsx
import React, { useState, useEffect, useRef } from 'react'; // Import hooks
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
// Removed: import ParticleBackground from '../components/ParticleBackground';

// Icônes SVG (Keep as before)
const ChatIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-bp-orange-bright" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
);
const SecureIcon = () => (
     <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-bp-orange-bright" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
);
const HistoryIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-bp-orange-bright" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);


function HomePage() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [vantaEffect, setVantaEffect] = useState(null); // State to hold the VANTA instance
    const vantaRef = useRef(null); // Ref for the container element
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Initialize VANTA effect on component mount
    useEffect(() => {
        // Check if VANTA is loaded (from script tag) and effect not already initialized
        if (!vantaEffect && window.VANTA) {
            const effect = window.VANTA.GLOBE({
                el: vantaRef.current, // Target the div using the ref
                mouseControls: true,
                touchControls: true,
                gyroControls: false,
                minHeight: 200.00,
                minWidth: 200.00,
                scale: 1.00,
                scaleMobile: 1.00,
                // --- Theme Colors ---
                // VANTA uses decimal representation of hex codes (0x prefix)
                color: 0xf0380c,       // bp-orange-bright
                color2: 0xec6414,      // bp-orange
                backgroundColor: 0x2c0c04, // bp-brown
                // --- End Theme Colors ---
                size: 1.00 // Adjust globe size (0.5 to 1.5 are good ranges)
            });
            setVantaEffect(effect); // Store the instance in state
        }

        // Cleanup function: Destroy the effect when the component unmounts
        return () => {
            if (vantaEffect) {
                vantaEffect.destroy();
                // console.log("VANTA effect destroyed");
            }
        };
    }, [vantaEffect]); // Re-run effect only if vantaEffect state changes (prevents re-init on every render)


    return (
        // Main container needs overflow-hidden if VANTA element is absolute
         // A fallback background color is good practice
        <div className="min-h-screen text-bp-brown relative overflow-hidden bg-bp-brown">

            {/* VANTA Container: Positioned absolutely behind content */}
            <div ref={vantaRef} className="absolute top-0 left-0 w-full h-full z-0"></div>

            {/* Content Sections: Must have relative positioning and z-index higher than VANTA */}

            {/* Header/Navbar Placeholder - Ensure solid background and high z-index */}
            <header className="p-4 shadow-md bg-bp-white relative z-10">
                 <div className="container mx-auto flex justify-between items-center">
                     <div className="flex items-center">
                         <img src="https://www.zonebourse.com/static/private-issuer-squared-9I42B.png" alt="Logo Banque Populaire" className="h-8 w-auto mr-3" />
                         <span className="text-xl font-bold text-bp-orange-bright">Chat Banque Populaire</span>
                     </div>
                     <div>
                         {user ? ( // Si l'utilisateur est connecté
                             <button
                                 onClick={() => navigate('/chat')}
                                 className="bg-bp-orange hover:bg-bp-orange-bright text-bp-white font-semibold py-2 px-5 rounded-md transition duration-200"
                             >
                                 Aller au Chat
                             </button>
                         ) : ( // Si l'utilisateur n'est pas connecté
                             <>
                                 <button
                                     onClick={() => navigate('/login')}
                                     className="text-bp-brown hover:text-bp-orange font-semibold mr-4"
                                 >
                                     Connexion
                                 </button>
                                 <button
                                     onClick={() => navigate('/signup')}
                                     className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-semibold py-2 px-5 rounded-md transition duration-200"
                                 >
                                     Inscription
                                 </button>
                             </>
                         )}
                     </div>
                 </div>
            </header>

            {/* Hero Section - Modified for Professionals / Data Catalog */}
            <section className="container mx-auto text-center py-20 lg:py-32 px-4 relative z-10">
                 {/* Optional: Add a subtle background overlay for readability */}
                 {/* <div className="absolute inset-0 bg-bp-white opacity-10 z-0"></div> */}
                 {/* Content needs relative positioning to appear above overlay */}
                 <div className="relative z-10">
                     {/* --- MODIFIED TEXT & SIZE --- */}
                     <h2 className="text-2xl lg:text-4xl font-bold mb-3 text-bp-white">
                         Assistant Catalogue de Données
                     </h2>
                     <p className="text-base lg:text-lg text-bp-gray-light mb-6 max-w-2xl mx-auto">
                     Interrogez le catalogue de données en langage naturel, avec simplicité et un accès rapide.
                     </p>
                     {/* --- END MODIFIED TEXT & SIZE --- */}
                     { !user && ( // Afficher le bouton principal si déconnecté
                         <button
                             onClick={() => navigate('/login')} // Point to login for professionals
                             className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-3 px-8 rounded-lg text-lg transition duration-200 shadow-lg"
                         >
                             Se Connecter {/* Changed button text */}
                         </button>
                      )}
                      { user && ( // Afficher un autre bouton si connecté
                          <button
                             onClick={() => navigate('/chat')}
                             className="bg-bp-orange-bright hover:bg-bp-orange text-bp-white font-bold py-3 px-8 rounded-lg text-lg transition duration-200 shadow-lg"
                         >
                             Démarrer le Chat
                         </button>
                      )}
                 </div>
            </section>
            {/* --- End Hero Section --- */}


            {/* Features Section - Give it a solid background */}
            <section className="bg-bp-white py-16 px-4 relative z-10">
                 <div className="container mx-auto text-center">
                     <h3 className="text-3xl font-bold mb-12 text-bp-brown">Pourquoi Choisir Notre Assistant ?</h3> {/* Slightly modified title */}
                     <div className="grid md:grid-cols-3 gap-8">
                         {/* Feature Cards remain the same... */}
                          {/* Feature 1 */}
                        <div className="bg-bp-gray-light p-8 rounded-lg shadow-md border border-bp-gray transform hover:scale-105 transition duration-300">
                            <div className="flex justify-center mb-4">
                                <ChatIcon />
                            </div>
                            <h4 className="text-xl font-semibold mb-3 text-bp-orange-bright">Réponses Contextuelles</h4> {/* Modified */}
                            <p className="text-bp-gray-dark">Utilise l'IA pour fournir des informations précises issues du catalogue de données de la banque.</p> {/* Modified */}
                        </div>
                        {/* Feature 2 */}
                        <div className="bg-bp-gray-light p-8 rounded-lg shadow-md border border-bp-gray transform hover:scale-105 transition duration-300">
                            <div className="flex justify-center mb-4">
                                <SecureIcon />
                            </div>
                            <h4 className="text-xl font-semibold mb-3 text-bp-orange-bright">Accès Sécurisé</h4>
                            <p className="text-bp-gray-dark">Nécessite une authentification pour accéder à l'assistant et à l'historique des conversations.</p> {/* Kept similar */}
                        </div>
                        {/* Feature 3 */}
                        <div className="bg-bp-gray-light p-8 rounded-lg shadow-md border border-bp-gray transform hover:scale-105 transition duration-300">
                            <div className="flex justify-center mb-4">
                                <HistoryIcon />
                            </div>
                            <h4 className="text-xl font-semibold mb-3 text-bp-orange-bright">Historique des Requêtes</h4> {/* Modified */}
                            <p className="text-bp-gray-dark">Accédez et consultez facilement vos requêtes et les réponses passées de l'assistant.</p> {/* Modified */}
                        </div>
                     </div>
                 </div>
            </section>

            {/* Footer Placeholder - Ensure it's above */}
            <footer className="bg-bp-brown text-bp-gray-light py-8 px-4 relative z-10">
                 <div className="container mx-auto text-center text-sm">
                     &copy; {new Date().getFullYear()} Banque Populaire. Tous droits réservés.
                 </div>
            </footer>

        </div>
    );
}

export default HomePage;