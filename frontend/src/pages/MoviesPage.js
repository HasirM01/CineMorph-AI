import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { Film, Trash2, Upload, Play, Languages } from 'lucide-react';
import { DashboardLayout } from '@/components/DashboardLayout';
import { VideoPlayer } from '@/components/VideoPlayer';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { DubbingModal } from '@/components/DubbingModal';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const MoviesPage = () => {
  const navigate = useNavigate();
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, movieId: null, movieTitle: '' });
  const [dubbingModal, setDubbingModal] = useState({ isOpen: false, movie: null });

  useEffect(() => {
    fetchMovies();
  }, []);

  const fetchMovies = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/movies`, { withCredentials: true });
      setMovies(response.data);
    } catch (error) {
      console.error('Error fetching movies:', error);
      toast.error('Failed to load movies');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = (movie) => {
    setSelectedVideo({
      url: `${API}/movies/${movie.movie_id}/stream`,
      title: movie.title
    });
  };

  const handleDeleteClick = (movie) => {
    setDeleteDialog({
      isOpen: true,
      movieId: movie.movie_id,
      movieTitle: movie.title
    });
  };

  const handleDubClick = (movie) => {
    setDubbingModal({
      isOpen: true,
      movie: movie
    });
  };

  const handleDubbingSuccess = () => {
    toast.success('Redirecting to Jobs page...');
    setTimeout(() => {
      navigate('/jobs');
    }, 500);
  };

  const handleDeleteConfirm = async () => {
    try {
      await axios.delete(`${API}/movies/${deleteDialog.movieId}`, { withCredentials: true });
      toast.success('Movie and related dubbing jobs deleted successfully');
      setDeleteDialog({ isOpen: false, movieId: null, movieTitle: '' });
      fetchMovies();
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete movie');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-full">
          <div className="text-white text-xl">Loading movies...</div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div data-testid="movies-page-container" className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              My Uploaded Movies
            </h1>
            <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Manage your source video files
            </p>
          </div>
          <a
            href="/upload"
            data-testid="upload-new-btn"
            className="bg-[#E50914] hover:bg-[#c40812] text-white rounded-lg px-6 py-3 font-semibold shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all flex items-center gap-2"
          >
            <Upload className="w-5 h-5" />
            Upload New
          </a>
        </div>

        {movies.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center"
          >
            <Film className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              No movies uploaded yet
            </h3>
            <p className="text-zinc-500 mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Upload your first movie to start dubbing
            </p>
            <a
              href="/upload"
              data-testid="go-to-upload-from-movies-btn"
              className="inline-flex items-center gap-2 bg-[#E50914] hover:bg-[#c40812] text-white rounded-lg px-6 py-3 font-semibold shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all"
            >
              <Upload className="w-5 h-5" />
              Upload Movie
            </a>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {movies.map((movie, index) => (
              <motion.div
                key={movie.movie_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                data-testid={`movie-card-${movie.movie_id}`}
                className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:-translate-y-1 hover:border-purple-500/50 hover:shadow-[0_8px_32px_rgba(139,92,246,0.15)] transition-all duration-300"
              >
                <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl p-8 mb-4 flex items-center justify-center">
                  <Film className="w-12 h-12 text-blue-400" />
                </div>
                <h3 className="text-lg font-bold mb-2 truncate" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  {movie.title}
                </h3>
                <div className="space-y-1 mb-4 text-sm text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  <p>Format: {movie.format?.toUpperCase()}</p>
                  <p>Size: {formatFileSize(movie.file_size)}</p>
                  <p>Language: {movie.detected_language?.toUpperCase()}</p>
                </div>
                <div className="space-y-2">
                  <button
                    data-testid={`preview-movie-btn-${movie.movie_id}`}
                    onClick={() => handlePreview(movie)}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white rounded-lg px-4 py-3 font-semibold transition-all flex items-center justify-center gap-2"
                  >
                    <Play className="w-5 h-5" />
                    Preview
                  </button>
                  <button
                    data-testid={`dub-movie-btn-${movie.movie_id}`}
                    onClick={() => handleDubClick(movie)}
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-lg px-4 py-3 font-semibold transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(59,130,246,0.3)]"
                  >
                    <Languages className="w-5 h-5" />
                    Dub Movie
                  </button>
                  <button
                    data-testid={`delete-movie-btn-${movie.movie_id}`}
                    onClick={() => handleDeleteClick(movie)}
                    className="w-full bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/20 rounded-lg px-4 py-3 font-semibold transition-all flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-5 h-5" />
                    Delete
                  </button>
                </div>
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
        onClose={() => setDeleteDialog({ isOpen: false, movieId: null, movieTitle: '' })}
        onConfirm={handleDeleteConfirm}
        title="Delete Movie"
        message={`Are you sure you want to delete "${deleteDialog.movieTitle}"? This will also delete all related dubbing jobs and their outputs.`}
      />

      <AnimatePresence>
        {dubbingModal.isOpen && (
          <DubbingModal
            movie={dubbingModal.movie}
            onClose={() => setDubbingModal({ isOpen: false, movie: null })}
            onSuccess={handleDubbingSuccess}
          />
        )}
      </AnimatePresence>
    </DashboardLayout>
  );
};
