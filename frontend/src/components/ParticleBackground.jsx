// src/components/ParticleBackground.jsx
import React, { useCallback } from "react";
import Particles from "react-tsparticles";
import { loadSlim } from "tsparticles-slim"; // loads the slim engine

const ParticleBackground = () => {
    // Memoized init function to load the engine
    const particlesInit = useCallback(async (engine) => {
        // console.log(engine); // Log engine if needed for debugging
        // Load the slim engine, you can load the full engine (loadFull) if needed
        await loadSlim(engine);
    }, []);

    // Memoized callback for when the container is loaded (optional)
    const particlesLoaded = useCallback(async (container) => {
        // await console.log(container); // Log container if needed
    }, []);

    // Particle configuration using your theme colors
    const particleOptions = {
        background: {
            color: {
                value: "transparent", // Make background transparent so HomePage background shows
            },
        },
        fpsLimit: 120, // Optional: Limit FPS
        interactivity: {
            events: {
                onHover: {
                    enable: true,
                    mode: "grab", // Change to "repulse" or other modes if desired
                },
                onClick: {
                    enable: false, // Disable click events unless needed
                    mode: "push",
                },
                resize: true,
            },
            modes: {
                grab: {
                    distance: 140,
                    line_linked: { // Correct property name is links
                        opacity: 1,
                    },
                    links: { // Use this instead of line_linked inside modes
                         opacity: 0.8, // Make grab lines slightly more opaque
                    }
                },
                push: {
                    particles_nb: 4,
                },
                repulse: { // Example settings if using repulse on hover
                     distance: 100,
                     duration: 0.4,
                }
                // Add other modes like bubble if needed
            },
        },
        particles: {
            color: {
                value: "#2c0c04", // bp-brown for particles
            },
            links: {
                color: "#ec6414", // bp-orange for links
                distance: 150,
                enable: true,
                opacity: 0.4, // Make lines semi-transparent
                width: 1,
            },
            collisions: {
                 enable: false, // Disable collisions for smoother flow
            },
            move: {
                direction: "none",
                enable: true,
                outModes: { // Changed from out_mode
                    default: "bounce", // Keep particles bouncing off edges
                },
                random: true, // Random direction
                speed: 1, // Slow movement speed
                straight: false,
            },
            number: {
                density: {
                    enable: true,
                    area: 800, // Changed from value_area
                },
                value: 60, // Number of particles
            },
            opacity: {
                value: 0.6, // Particle opacity
            },
            shape: {
                type: "circle",
            },
            size: {
                value: { min: 1, max: 3 }, // Random size between 1 and 3
            },
        },
        detectRetina: true,
    };


    return (
        <Particles
            id="tsparticles"
            init={particlesInit}
            loaded={particlesLoaded}
            options={particleOptions}
            // Style to position it behind other content
            className="absolute top-0 left-0 w-full h-full z-0" // Use z-0 to place behind relative z-10 content
        />
    );
};

export default React.memo(ParticleBackground); // Memoize for performance