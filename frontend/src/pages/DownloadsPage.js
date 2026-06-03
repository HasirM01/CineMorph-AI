import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Download, Film, Loader2 } from 'lucide-react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const DownloadsPage = () => {
  const [completedJobs, setCompletedJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState({});

  useEffect(() => {
    fetchCompletedJobs();
  }, []);

  const fetchCompletedJobs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/dubbing/jobs`, { withCredentials: true });
      const completed = response.data.filter((job) => job.status === 'completed');
      setCompletedJobs(completed);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      toast.error('Failed to load downloads');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (job) => {
    setDownloading((prev) => ({ ...prev, [job.job_id]: true }));
    try {
      const response = await axios.get(`${API}/dubbing/${job.job_id}/download`, {
        withCredentials: true,
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `dubbed_${job.movie_title || job.job_id}.mp4`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Download started!');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download movie');
    } finally {
      setDownloading((prev) => ({ ...prev, [job.job_id]: false }));
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-white text-xl">Loading downloads...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div data-testid="downloads-page-container" className="space-y-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Downloads
          </h1>
          <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Download your completed dubbed movies
          </p>
        </div>

        {completedJobs.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center"
          >
            <Download className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              No downloads available
            </h3>
            <p className="text-zinc-500 mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Complete a dubbing job to download your movies
            </p>
            <a
              href="/upload"
              data-testid="go-to-upload-from-downloads-btn"
              className="inline-flex items-center gap-2 bg-[#E50914] hover:bg-[#c40812] text-white rounded-lg px-6 py-3 font-semibold shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all"
            >
              Start Dubbing
            </a>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {completedJobs.map((job, index) => (
              <motion.div
                key={job.job_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                data-testid={`download-card-${job.job_id}`}
                className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-purple-500/50 hover:shadow-[0_8px_32px_rgba(139,92,246,0.15)] transition-all duration-300"
              >
                <div className="bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-xl p-8 mb-4 flex items-center justify-center">
                  <Film className="w-12 h-12 text-purple-400" />
                </div>
                <h3 className="text-lg font-bold mb-2 truncate" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  {job.movie_title || 'Untitled Movie'}
                </h3>
                <p className="text-sm text-zinc-400 mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  {job.source_language?.toUpperCase()} → {job.target_language?.toUpperCase()}
                </p>
                <button
                  data-testid={`download-btn-${job.job_id}`}
                  onClick={() => handleDownload(job)}
                  disabled={downloading[job.job_id]}
                  className="w-full bg-[#E50914] hover:bg-[#c40812] disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg px-4 py-3 font-semibold shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all flex items-center justify-center gap-2"
                >
                  {downloading[job.job_id] ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Downloading...
                    </>
                  ) : (
                    <>
                      <Download className="w-5 h-5" />
                      Download
                    </>
                  )}
                </button>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
