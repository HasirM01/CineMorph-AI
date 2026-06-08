import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AuthCallback = () => {
  const navigate = useNavigate();
  const { setUser, checkAuth } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      const hash = window.location.hash;
      const sessionId = new URLSearchParams(hash.substring(1)).get('session_id');

      if (!sessionId) {
        navigate('/login', { replace: true });
        return;
      }

      try {
        const response = await axios.post(
          `${API}/auth/session`,
          { session_id: sessionId },
          { withCredentials: true }
        );

        // Set user in context
        setUser(response.data);
        
        // Wait a moment to ensure cookie is set
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Verify authentication worked by checking /auth/me
        await checkAuth();
        
        // Navigate to dashboard with user data in state
        navigate('/dashboard', { 
          replace: true, 
          state: { user: response.data } 
        });
      } catch (error) {
        console.error('Auth error:', error);
        navigate('/login', { replace: true });
      }
    };

    processSession();
  }, [navigate, setUser, checkAuth]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-black">
      <div className="text-white text-xl">Authenticating...</div>
    </div>
  );
};
