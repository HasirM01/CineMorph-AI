import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Film, LayoutDashboard, Upload, Download, Settings, LogOut, Menu, X, BarChart3, Video } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { motion, AnimatePresence } from 'framer-motion';

export const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', icon: <LayoutDashboard className="w-5 h-5" />, label: 'Dashboard', testId: 'nav-dashboard' },
    { path: '/upload', icon: <Upload className="w-5 h-5" />, label: 'Upload', testId: 'nav-upload' },
    { path: '/movies', icon: <Video className="w-5 h-5" />, label: 'My Movies', testId: 'nav-movies' },
    { path: '/jobs', icon: <BarChart3 className="w-5 h-5" />, label: 'My Jobs', testId: 'nav-jobs' },
    { path: '/downloads', icon: <Download className="w-5 h-5" />, label: 'Downloads', testId: 'nav-downloads' },
    { path: '/settings', icon: <Settings className="w-5 h-5" />, label: 'Settings', testId: 'nav-settings' },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white">
      <div className="lg:hidden sticky top-0 z-50 bg-black/60 backdrop-blur-2xl border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Film className="w-6 h-6 text-[#E50914]" />
          <span className="text-xl font-black" style={{ fontFamily: 'Outfit, sans-serif' }}>CineMorph AI</span>
        </div>
        <button
          data-testid="mobile-menu-btn"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="text-white hover:text-purple-400 transition-colors"
        >
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      <div className="flex">
        <AnimatePresence>
          {(sidebarOpen || window.innerWidth >= 1024) && (
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 25 }}
              className="fixed lg:sticky top-0 left-0 h-screen w-72 bg-[#121212] border-r border-white/10 flex flex-col z-40"
            >
              <div className="p-6 border-b border-white/10">
                <div className="flex items-center gap-3 mb-6">
                  <Film className="w-8 h-8 text-[#E50914]" />
                  <span className="text-2xl font-black tracking-tighter" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    CineMorph AI
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarImage src={user?.picture} />
                    <AvatarFallback className="bg-purple-600 text-white">
                      {user?.name?.charAt(0) || 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold truncate" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      {user?.name}
                    </div>
                    <div className="text-xs text-zinc-500 truncate">{user?.email}</div>
                  </div>
                </div>
              </div>

              <nav className="flex-1 p-4 space-y-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    data-testid={item.testId}
                    onClick={() => setSidebarOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                        isActive
                          ? 'bg-purple-600 text-white shadow-[0_0_20px_rgba(139,92,246,0.3)]'
                          : 'text-zinc-400 hover:text-white hover:bg-white/5'
                      }`
                    }
                  >
                    {item.icon}
                    <span className="font-medium" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      {item.label}
                    </span>
                  </NavLink>
                ))}
              </nav>

              <div className="p-4 border-t border-white/10">
                <button
                  data-testid="logout-btn"
                  onClick={handleLogout}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-red-400 hover:bg-red-500/10 transition-all w-full"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="font-medium" style={{ fontFamily: 'Manrope, sans-serif' }}>Logout</span>
                </button>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        <main className="flex-1 p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
};
