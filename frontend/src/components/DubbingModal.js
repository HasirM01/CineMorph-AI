import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { X, Globe, Loader2, DollarSign, Clock, AlertCircle, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const DubbingModal = ({ movie, onClose, onSuccess }) => {
  const [languages, setLanguages] = useState([]);
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [loading, setLoading] = useState(true);
  const [showCostEstimate, setShowCostEstimate] = useState(false);
  const [estimate, setEstimate] = useState(null);
  const [estimating, setEstimating] = useState(false);
  const [creatingJob, setCreatingJob] = useState(false);
  const [aiConfig, setAiConfig] = useState(null);

  useEffect(() => {
    fetchLanguages();
    fetchAiConfig();
  }, []);

  const fetchLanguages = async () => {
    try {
      const response = await axios.get(`${API}/languages`);
      setLanguages(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching languages:', error);
      toast.error('Failed to load languages');
      setLoading(false);
    }
  };

  const fetchAiConfig = async () => {
    try {
      const response = await axios.get(`${API}/config/ai`);
      setAiConfig(response.data);
    } catch (error) {
      console.error('Error fetching AI config:', error);
    }
  };

  const handleGetEstimate = async () => {
    if (!selectedLanguage) {
      toast.error('Please select a target language');
      return;
    }

    // For mock mode, skip estimate and create job directly
    if (aiConfig?.ai_mode !== 'real') {
      createDubbingJob(false);
      return;
    }

    setEstimating(true);
    try {
      const response = await axios.post(
        `${API}/dubbing/estimate-cost`,
        { movie_id: movie.movie_id },
        { withCredentials: true }
      );
      setEstimate(response.data);
      setShowCostEstimate(true);
    } catch (err) {
      console.error('Error fetching cost estimate:', err);
      toast.error(err.response?.data?.detail || 'Failed to estimate cost');
    } finally {
      setEstimating(false);
    }
  };

  const createDubbingJob = async (costApproved = false) => {
    setCreatingJob(true);
    try {
      const response = await axios.post(
        `${API}/dubbing/create`,
        {
          movie_id: movie.movie_id,
          target_language: selectedLanguage,
          cost_approved: costApproved,
        },
        { withCredentials: true }
      );

      toast.success('Dubbing job started successfully!');
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error creating job:', error);
      toast.error(error.response?.data?.detail || 'Failed to start dubbing');
    } finally {
      setCreatingJob(false);
    }
  };

  const handleApprove = () => {
    setShowCostEstimate(false);
    createDubbingJob(true);
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-2xl p-8 max-w-2xl w-full border border-zinc-700"
        >
          <div className="flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
          </div>
        </motion.div>
      </motion.div>
    );
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          data-testid="dubbing-modal"
          className="bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-2xl p-8 max-w-2xl w-full border border-zinc-700 max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-2xl font-black text-white mb-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Dub Movie
              </h2>
              <p className="text-zinc-400 text-sm" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {movie.title}
              </p>
            </div>
            <button
              onClick={onClose}
              data-testid="dubbing-modal-close-btn"
              className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-zinc-400" />
            </button>
          </div>

          {!showCostEstimate ? (
            <>
              {/* Language Selection */}
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    <Globe className="w-4 h-4 inline mr-2" />
                    Target Language
                  </label>
                  <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                    <SelectTrigger
                      data-testid="dubbing-modal-language-select"
                      className="w-full bg-zinc-800 border-zinc-700 text-white"
                    >
                      <SelectValue placeholder="Select target language" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-800 border-zinc-700">
                      {languages
                        .filter(lang => lang.code !== movie.detected_language)
                        .map(lang => (
                          <SelectItem
                            key={lang.code}
                            value={lang.code}
                            className="text-white hover:bg-zinc-700"
                          >
                            {lang.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Movie Info */}
                <div className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700">
                  <h4 className="text-sm font-semibold text-zinc-300 mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    Movie Details
                  </h4>
                  <div className="space-y-1 text-sm text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    <p>Source Language: <span className="text-white">{movie.detected_language?.toUpperCase()}</span></p>
                    <p>Format: <span className="text-white">{movie.format?.toUpperCase()}</span></p>
                    <p>Size: <span className="text-white">{(movie.file_size / (1024 * 1024)).toFixed(2)} MB</span></p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={onClose}
                  data-testid="dubbing-modal-cancel-btn"
                  className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-white font-medium transition-all"
                  style={{ fontFamily: 'Manrope, sans-serif' }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleGetEstimate}
                  disabled={!selectedLanguage || estimating || creatingJob}
                  data-testid="dubbing-modal-proceed-btn"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  style={{ fontFamily: 'Manrope, sans-serif' }}
                >
                  {estimating || creatingJob ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      {estimating ? 'Estimating...' : 'Starting...'}
                    </>
                  ) : (
                    'Get Cost Estimate'
                  )}
                </button>
              </div>
            </>
          ) : (
            /* Cost Estimate Section */
            <div className="space-y-6">
              {/* Cost Overview */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700" data-testid="modal-cost-total">
                  <div className="flex items-center space-x-2 mb-2">
                    <DollarSign className="w-5 h-5 text-blue-400" />
                    <span className="text-sm text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      Total Cost
                    </span>
                  </div>
                  <p className="text-3xl font-black text-white" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    ${estimate.total_cost.toFixed(4)}
                  </p>
                  <p className="text-xs text-zinc-500 mt-1" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    ~₹{(estimate.total_cost * 80).toFixed(2)}
                  </p>
                </div>

                <div className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700" data-testid="modal-cost-time">
                  <div className="flex items-center space-x-2 mb-2">
                    <Clock className="w-5 h-5 text-purple-400" />
                    <span className="text-sm text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      Estimated Time
                    </span>
                  </div>
                  <p className="text-3xl font-black text-white" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    ~{estimate.estimated_processing_time}m
                  </p>
                  <p className="text-xs text-zinc-500 mt-1" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    {estimate.duration_seconds.toFixed(0)}s video
                  </p>
                </div>
              </div>

              {/* Breakdown */}
              <div className="bg-zinc-800/30 rounded-xl p-4 space-y-2" data-testid="modal-cost-breakdown">
                <h4 className="text-sm font-bold text-zinc-300 mb-3" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  Cost Breakdown
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>Whisper (STT)</span>
                    <span className="text-white font-medium">${estimate.whisper_cost.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>GPT-4o (Translation)</span>
                    <span className="text-white font-medium">${estimate.gpt_cost.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>OpenAI TTS (Voice)</span>
                    <span className="text-white font-medium">${estimate.tts_cost.toFixed(4)}</span>
                  </div>
                </div>
              </div>

              {/* Budget Warning */}
              {estimate.budget_warning && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  data-testid="modal-budget-warning"
                  className="bg-red-900/20 border border-red-500/30 rounded-xl p-4"
                >
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-300" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      {estimate.budget_warning}
                    </p>
                  </div>
                </motion.div>
              )}

              {/* Actions */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowCostEstimate(false)}
                  data-testid="modal-cost-back-btn"
                  className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-white font-medium transition-all"
                  style={{ fontFamily: 'Manrope, sans-serif' }}
                >
                  Back
                </button>
                <button
                  onClick={handleApprove}
                  disabled={!estimate.can_process || creatingJob}
                  data-testid="modal-cost-approve-btn"
                  className={`flex-1 px-6 py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${
                    estimate.can_process
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white'
                      : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
                  }`}
                  style={{ fontFamily: 'Manrope, sans-serif' }}
                >
                  {creatingJob ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Starting...
                    </>
                  ) : estimate.can_process ? (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Approve & Start
                    </>
                  ) : (
                    'Budget Exceeded'
                  )}
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
