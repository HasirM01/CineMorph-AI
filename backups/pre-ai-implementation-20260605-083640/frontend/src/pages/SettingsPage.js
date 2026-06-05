import React from 'react';
import { motion } from 'framer-motion';
import { User, Mail, Globe, Film } from 'lucide-react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { useAuth } from '@/contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export const SettingsPage = () => {
  const { user } = useAuth();

  return (
    <DashboardLayout>
      <div data-testid="settings-page-container" className="space-y-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Settings
          </h1>
          <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Manage your account and preferences
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            <User className="w-6 h-6 text-purple-500" />
            Profile Information
          </h2>

          <div className="flex items-center gap-6 mb-8">
            <Avatar className="w-24 h-24">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-purple-600 text-white text-3xl">
                {user?.name?.charAt(0) || 'U'}
              </AvatarFallback>
            </Avatar>
            <div>
              <h3 className="text-2xl font-bold mb-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
                {user?.name}
              </h3>
              <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {user?.email}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-black/30 rounded-lg">
              <Mail className="w-5 h-5 text-purple-400" />
              <div>
                <p className="text-sm text-zinc-500" style={{ fontFamily: 'Manrope, sans-serif' }}>Email</p>
                <p className="font-medium" style={{ fontFamily: 'Manrope, sans-serif' }}>{user?.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 bg-black/30 rounded-lg">
              <User className="w-5 h-5 text-blue-400" />
              <div>
                <p className="text-sm text-zinc-500" style={{ fontFamily: 'Manrope, sans-serif' }}>Full Name</p>
                <p className="font-medium" style={{ fontFamily: 'Manrope, sans-serif' }}>{user?.name}</p>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            <Globe className="w-6 h-6 text-blue-500" />
            Language Preferences
          </h2>
          <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
            CineMorph AI supports Tamil, Telugu, Malayalam, Kannada, Hindi, English, Spanish, French, German, Japanese, Korean, Chinese, Arabic, Portuguese, and Russian for natural conversational dubbing.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
        >
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            <Film className="w-6 h-6 text-red-500" />
            About CineMorph AI
          </h2>
          <p className="text-zinc-400 mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
            CineMorph AI is an intelligent multilingual movie dubbing platform that uses advanced AI to transform any movie into any language with natural, conversational dubbing. 
          </p>
          <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Our platform preserves emotional impact, timing, and authentic native speech to deliver cinema-quality dubbing results.
          </p>
        </motion.div>
      </div>
    </DashboardLayout>
  );
};
