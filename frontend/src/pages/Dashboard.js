import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Upload, Film, Clock, CheckCircle, XCircle, TrendingUp, Globe } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { DashboardLayout } from '@/components/DashboardLayout';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Dashboard = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [analyticsRes, jobsRes] = await Promise.all([
        axios.get(`${API}/analytics/user`, { withCredentials: true }),
        axios.get(`${API}/dubbing/jobs`, { withCredentials: true })
      ]);
      setAnalytics(analyticsRes.data);
      setRecentJobs(jobsRes.data.slice(0, 5));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    {
      icon: <Film className="w-6 h-6" />,
      label: 'Total Uploads',
      value: analytics?.total_uploads || 0,
      color: 'from-red-500 to-pink-500'
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      label: 'Dubbing Jobs',
      value: analytics?.total_dubbing_jobs || 0,
      color: 'from-purple-500 to-indigo-500'
    },
    {
      icon: <CheckCircle className="w-6 h-6" />,
      label: 'Completed',
      value: analytics?.completed_jobs || 0,
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: <Clock className="w-6 h-6" />,
      label: 'In Progress',
      value: analytics?.in_progress_jobs || 0,
      color: 'from-blue-500 to-cyan-500'
    },
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-zinc-500" />;
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-white text-xl">Loading dashboard...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div data-testid="dashboard-container" className="space-y-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Welcome back, {user?.name?.split(' ')[0]}!
          </h1>
          <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Your AI movie dubbing dashboard
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              data-testid={`stat-card-${stat.label.toLowerCase().replace(' ', '-')}`}
              className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-purple-500/50 hover:shadow-[0_8px_32px_rgba(139,92,246,0.15)] transition-all duration-300"
            >
              <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${stat.color} mb-4`}>
                {stat.icon}
              </div>
              <div className="text-3xl font-bold mb-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
                {stat.value}
              </div>
              <div className="text-sm text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
          >
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <Globe className="w-5 h-5 text-purple-500" />
              Languages Used
            </h2>
            {analytics?.languages_used && Object.keys(analytics.languages_used).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(analytics.languages_used).map(([lang, count]) => (
                  <div key={lang} className="flex items-center justify-between">
                    <span className="text-zinc-300" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      {lang.toUpperCase()}
                    </span>
                    <span className="text-sm font-semibold text-purple-400">{count} jobs</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-500 text-sm">No dubbing jobs yet</p>
            )}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
          >
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <Clock className="w-5 h-5 text-blue-500" />
              Recent Activity
            </h2>
            {recentJobs.length > 0 ? (
              <div className="space-y-3">
                {recentJobs.map((job) => (
                  <div key={job.job_id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <div className="text-sm text-zinc-300" style={{ fontFamily: 'Manrope, sans-serif' }}>
                          {job.movie_title || 'Movie'}
                        </div>
                        <div className="text-xs text-zinc-500">{job.target_language.toUpperCase()}</div>
                      </div>
                    </div>
                    <span className="text-xs text-zinc-500">{job.progress}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-zinc-500 text-sm">No recent activity</p>
            )}
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          data-testid="quick-action-card"
          className="bg-gradient-to-r from-[#E50914]/20 via-[#8B5CF6]/20 to-[#3B82F6]/20 border border-white/10 rounded-2xl p-8 text-center backdrop-blur-xl"
        >
          <Upload className="w-12 h-12 text-purple-500 mx-auto mb-4" />
          <h3 className="text-2xl font-bold mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Ready to dub a movie?
          </h3>
          <p className="text-zinc-400 mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Upload your video and start AI-powered dubbing
          </p>
          <a
            href="/upload"
            data-testid="upload-new-movie-btn"
            className="inline-flex items-center gap-2 bg-[#E50914] hover:bg-[#c40812] text-white rounded-lg px-6 py-3 font-semibold shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all"
          >
            <Upload className="w-5 h-5" />
            Upload Movie
          </a>
        </motion.div>
      </div>
    </DashboardLayout>
  );
};
