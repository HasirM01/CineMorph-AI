import { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // If we just came from auth callback with user data, we're authenticated
  const hasJustLoggedIn = location.state?.user;

  // Show loading state while checking authentication
  if (loading && !hasJustLoggedIn) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  // If not authenticated and didn't just login, redirect to login
  if (!user && !hasJustLoggedIn && !loading) {
    return <Navigate to="/login" replace />;
  }

  return children;
};
