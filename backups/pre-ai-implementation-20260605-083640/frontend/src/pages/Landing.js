import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Film, Globe2, Sparkles, Zap, Languages, Clock } from 'lucide-react';

export const Landing = () => {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/login');
  };

  const features = [
    {
      icon: <Languages className="w-8 h-8" />,
      title: 'Natural Dubbing',
      description: 'AI-powered conversational dubbing that sounds authentic and native'
    },
    {
      icon: <Globe2 className="w-8 h-8" />,
      title: 'Multilingual Support',
      description: 'Support for Tamil, Telugu, Malayalam, Kannada, and 15+ global languages'
    },
    {
      icon: <Sparkles className="w-8 h-8" />,
      title: 'Emotional Accuracy',
      description: 'Preserve emotional tone and cultural context in every dialogue'
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: 'Fast Processing',
      description: 'Advanced AI pipeline for quick movie dubbing and localization'
    },
    {
      icon: <Clock className="w-8 h-8" />,
      title: 'Perfect Sync',
      description: 'Dialogue timing synchronized perfectly with original scenes'
    },
    {
      icon: <Film className="w-8 h-8" />,
      title: 'Cinema Quality',
      description: 'Theatre-grade dubbing quality for professional results'
    },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white">
      <div 
        className="relative overflow-hidden"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1689443111130-6e9c7dfd8f9e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NjZ8MHwxfHNlYXJjaHwxfHxkYXJrJTIwZnV0dXJpc3RpYyUyMGdsb3dpbmclMjBpbnRlcmZhY2V8ZW58MHx8fHwxNzgwNDgxMTk3fDA&ixlib=rb-4.1.0&q=85')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/70 to-[#0A0A0A]"></div>
        
        <nav className="relative z-10 max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Film className="w-8 h-8 text-[#E50914]" />
            <span className="text-2xl font-black tracking-tighter" style={{ fontFamily: 'Outfit, sans-serif' }}>
              CineMorph AI
            </span>
          </div>
          <button
            data-testid="nav-login-btn"
            onClick={handleGetStarted}
            className="bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-lg px-6 py-2.5 font-medium backdrop-blur-md transition-all"
          >
            Sign In
          </button>
        </nav>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-24 md:py-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-4xl mx-auto"
          >
            <h1 className="text-4xl sm:text-5xl lg:text-7xl font-black tracking-tighter mb-6" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Intelligent Multilingual
              <span className="block bg-gradient-to-r from-[#E50914] via-[#8B5CF6] to-[#3B82F6] bg-clip-text text-transparent">
                Movie Dubbing Platform
              </span>
            </h1>
            <p className="text-lg md:text-xl text-zinc-400 mb-10 max-w-2xl mx-auto" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Transform any movie into any language with natural, conversational AI dubbing. 
              Preserve emotions, timing, and authentic native speech.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                data-testid="get-started-btn"
                onClick={handleGetStarted}
                className="bg-[#E50914] hover:bg-[#c40812] text-white rounded-lg px-8 py-4 font-semibold text-lg shadow-[0_0_30px_rgba(229,9,20,0.4)] hover:shadow-[0_0_40px_rgba(229,9,20,0.6)] transition-all flex items-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                Get Started Free
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Cinematic AI Localization
          </h2>
          <p className="text-zinc-400 text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Professional movie dubbing powered by advanced AI
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-purple-500/50 hover:shadow-[0_8px_32px_rgba(139,92,246,0.15)] transition-all duration-300"
            >
              <div className="text-[#8B5CF6] mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                {feature.title}
              </h3>
              <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="bg-gradient-to-r from-[#E50914]/20 via-[#8B5CF6]/20 to-[#3B82F6]/20 border border-white/10 rounded-3xl p-12 text-center backdrop-blur-xl"
        >
          <h2 className="text-3xl md:text-5xl font-black mb-6" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Ready to Transform Your Movies?
          </h2>
          <p className="text-xl text-zinc-300 mb-8 max-w-2xl mx-auto" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Start dubbing movies in minutes with AI-powered localization
          </p>
          <button
            data-testid="cta-get-started-btn"
            onClick={handleGetStarted}
            className="bg-white text-black hover:bg-zinc-200 rounded-lg px-10 py-4 font-bold text-lg transition-all shadow-[0_0_20px_rgba(255,255,255,0.3)]"
          >
            Launch CineMorph AI
          </button>
        </motion.div>
      </div>

      <footer className="border-t border-white/10 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-zinc-500" style={{ fontFamily: 'Manrope, sans-serif' }}>
          <p>&copy; 2026 CineMorph AI. Intelligent Movie Dubbing Platform.</p>
        </div>
      </footer>
    </div>
  );
};
