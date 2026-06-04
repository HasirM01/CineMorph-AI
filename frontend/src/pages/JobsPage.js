import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Clock, CheckCircle, XCircle, Loader2, Film, RefreshCw, Play, Trash2 } from 'lucide-react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { VideoPlayer } from '@/components/VideoPlayer';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { toast } from 'sonner';
import { Progress } from '@/components/ui/progress';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const JobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, jobId: null, jobTitle: '' });

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(() => {
      fetchJobs(true);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const response = await axios.get(`${API}/dubbing/jobs`, { withCredentials: true });
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      if (!silent) toast.error('Failed to load jobs');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchJobs();
  };

  const handlePreview = (job) => {
    setSelectedVideo({
      url: `${API}/dubbing/${job.job_id}/stream`,
      title: `${job.movie_title} (${job.source_language?.toUpperCase()} → ${job.target_language?.toUpperCase()})`
    });
  };

  const handleDeleteClick = (job) => {
    setDeleteDialog({
      isOpen: true,
      jobId: job.job_id,
      jobTitle: job.movie_title || 'Untitled Movie'
    });
  };

  const handleDeleteConfirm = async () => {
    try {
      await axios.delete(`${API}/dubbing/${deleteDialog.jobId}`, { withCredentials: true });
      toast.success('Dubbing job deleted successfully');
      setDeleteDialog({ isOpen: false, jobId: null, jobTitle: '' });
      fetchJobs();
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete job');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-500';
      case 'processing':
        return 'text-blue-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-zinc-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
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
          <div className="text-white text-xl">Loading jobs...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div data-testid="jobs-page-container" className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              My Dubbing Jobs
            </h1>
            <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Track all your AI dubbing projects
            </p>
          </div>
          <button
            data-testid="refresh-jobs-btn"
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-lg px-4 py-2 font-medium backdrop-blur-md transition-all flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {jobs.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center"
          >
            <Film className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              No dubbing jobs yet
            </h3>
            <p className="text-zinc-500 mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Upload a movie to get started with AI dubbing
            </p>
            <a
              href="/upload"
              data-testid="go-to-upload-btn"
              className="inline-flex items-center gap-2 bg-[#E50914] hover:bg-[#c40812] text-white rounded-lg px-6 py-3 font-semibold shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all"
            >
              Upload Movie
            </a>
          </motion.div>
        ) : (
          <div className="space-y-4">
            {jobs.map((job, index) => (
              <motion.div
                key={job.job_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                data-testid={`job-card-${job.job_id}`}
                className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-purple-500/50 hover:shadow-[0_8px_32px_rgba(139,92,246,0.15)] transition-all duration-300"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    {getStatusIcon(job.status)}
                    <div className="flex-1">
                      <h3 className="text-lg font-bold mb-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
                        {job.movie_title || 'Untitled Movie'}
                      </h3>
                      <div className="flex flex-wrap gap-3 text-sm text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        <span>{job.source_language?.toUpperCase()} → {job.target_language?.toUpperCase()}</span>
                        <span>•</span>
                        <span className={getStatusColor(job.status)}>
                          {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold" style={{ fontFamily: 'Outfit, sans-serif' }}>
                      {job.progress}%
                    </div>
                  </div>
                </div>

                {job.status === 'processing' && (
                  <div className="space-y-2">
                    <Progress value={job.progress} className="h-2" />
                    <p className="text-sm text-zinc-500" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      {job.current_stage}
                    </p>
                  </div>
                )}

                {job.status === 'completed' && (
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => handlePreview(job)}
                      data-testid={`preview-job-btn-${job.job_id}`}
                      className="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-2 text-sm font-semibold transition-all"
                    >
                      <Play className="w-4 h-4" />
                      Preview
                    </button>
                    <a
                      href={`/downloads`}
                      data-testid={`download-job-btn-${job.job_id}`}
                      className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white rounded-lg px-4 py-2 text-sm font-semibold transition-all"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Download
                    </a>
                    <button
                      onClick={() => handleDeleteClick(job)}
                      data-testid={`delete-job-btn-${job.job_id}`}
                      className="inline-flex items-center gap-2 bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 rounded-lg px-4 py-2 text-sm font-semibold transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                )}

                {job.status === 'failed' && (
                  <div className="mt-4">
                    <button
                      onClick={() => handleDeleteClick(job)}
                      data-testid={`delete-failed-job-btn-${job.job_id}`}
                      className="inline-flex items-center gap-2 bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 rounded-lg px-4 py-2 text-sm font-semibold transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {selectedVideo && (
          <VideoPlayer
            videoUrl={selectedVideo.url}
            title={selectedVideo.title}
            onClose={() => setSelectedVideo(null)}
          />
        )}
      </AnimatePresence>

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, jobId: null, jobTitle: '' })}
        onConfirm={handleDeleteConfirm}
        title="Delete Dubbing Job"
        message={`Are you sure you want to delete "${deleteDialog.jobTitle}"? This will permanently remove the dubbed output file.`}
      />
    </DashboardLayout>
  );
};
