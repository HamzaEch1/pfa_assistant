// src/pages/SignupPage.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

function SignupPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState(''); // Optional
    const [fullName, setFullName] = useState(''); // Optional
    const [error, setError] = useState('');
    const { signup } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        // Basic validation
        if (password.length < 6) {
             setError('Password must be at least 6 characters long.');
             return;
        }
        try {
            await signup({ username, password, email: email || null, full_name: fullName || null });
            // Optionally add a success message or auto-login
            navigate('/login'); // Redirect to login after successful signup
        } catch (err) {
            setError(err.response?.data?.detail || 'Signup failed. Please try again.');
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-bp-gray-light"> {/* Use theme gray */}
            <div className="p-8 bg-bp-white rounded shadow-md w-full max-w-sm"> {/* Use theme white */}
                 {/* Activated Logo */}
                 <img src="https://www.zonebourse.com/static/private-issuer-squared-9I42B.png" alt="Banque Populaire" className="mx-auto mb-4 h-10" />
                <h2 className="text-xl font-bold mb-6 text-center text-bp-brown">Inscription</h2> {/* Use theme brown */}
                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label className="block text-bp-gray-dark text-sm font-bold mb-2" htmlFor="username">
                            Username *
                        </label>
                        <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} required className="input-field" />
                    </div>
                    <div className="mb-4">
                        <label className="block text-bp-gray-dark text-sm font-bold mb-2" htmlFor="fullName">
                            Full Name
                        </label>
                        <input id="fullName" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-field" />
                    </div>
                    <div className="mb-4">
                        <label className="block text-bp-gray-dark text-sm font-bold mb-2" htmlFor="email">
                            Email
                        </label>
                        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field" />
                    </div>
                    <div className="mb-6">
                        <label className="block text-bp-gray-dark text-sm font-bold mb-2" htmlFor="password">
                            Password * (min. 6 chars)
                        </label>
                        <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="input-field" />
                    </div>
                    {error && <p className="text-red-500 text-xs italic mb-4">{error}</p>}
                    <div className="flex items-center justify-between">
                        <button type="submit" className="btn-primary w-full">
                            Sign Up
                        </button>
                    </div>
                     <p className="text-center text-bp-gray-dark text-sm mt-4">
                        Already have an account?{' '}
                        <button
                          type="button"
                          onClick={() => navigate('/login')}
                          className="text-bp-orange-bright hover:text-bp-orange font-bold" // Use theme colors
                         >
                            Login
                        </button>
                    </p>
                </form>
            </div>
            {/* Shared styling using theme colors */}
            <style jsx>{`
                .input-field {
                     box-shadow: appearance;
                     border: 1px solid #e2e8f0; /* Default border */
                     border-radius: 0.25rem;
                     width: 100%;
                     padding: 0.5rem 0.75rem;
                     color: #2c0c04; /* bp-brown */
                     line-height: 1.25;
                     transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
                }
                .input-field:focus {
                     outline: none;
                     box-shadow: 0 0 0 3px rgba(236, 100, 20, 0.5); /* Adjusted focus shadow based on bp-orange */
                     border-color: #ec6414; /* bp-orange */
                }
                .btn-primary {
                    background-color: #f0380c; /* bp-orange-bright */
                    color: #FFFFFF; /* bp-white */
                    font-weight: bold;
                    padding: 0.5rem 1rem;
                    border-radius: 0.25rem;
                    transition: background-color 0.15s ease-in-out;
                }
                .btn-primary:hover {
                    background-color: #ec6414; /* bp-orange */
                }

            `}</style>
        </div>
    );
}

export default SignupPage;