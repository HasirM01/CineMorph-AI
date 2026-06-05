import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { DollarSign, Clock, AlertCircle, CheckCircle, Loader2, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const CostEstimateCard = ({ movieId, onApprove, onCancel }) => {
  const [loading, setLoading] = useState(true);
  const [estimate, setEstimate] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCostEstimate();
  }, [movieId]);

  const fetchCostEstimate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${API}/dubbing/estimate-cost`,
        { movie_id: movieId },
        { withCredentials: true }
      );
      setEstimate(response.data);
    } catch (err) {
      console.error('Error fetching cost estimate:', err);
      setError(err.response?.data?.detail || 'Failed to estimate cost');
      toast.error(err.response?.data?.detail || 'Failed to estimate cost');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gradient-to-br from-zinc-900 to-zinc-800 rounded-2xl p-8 border border-zinc-700"
      >
        <div className="flex items-center justify-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-400" />
          <p className="text-zinc-300" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Calculating processing cost...
          </p>
        </div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gradient-to-br from-red-900/20 to-zinc-900 rounded-2xl p-8 border border-red-500/30"
      >
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h3 className="text-lg font-bold text-red-300 mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Estimation Failed
            </h3>
            <p className="text-zinc-300 mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              {error}
            </p>
            <button
              onClick={onCancel}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-white transition-colors"
              style={{ fontFamily: 'Manrope, sans-serif' }}
            >
              Go Back
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  if (!estimate) return null;

  const { budget_exceeded, budget_warning, can_process } = estimate;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      data-testid="cost-estimate-card"
      className={`bg-gradient-to-br ${
        budget_exceeded ? 'from-red-900/20 to-zinc-900 border-red-500/30' : 'from-blue-900/20 to-zinc-900 border-blue-500/30'
      } rounded-2xl p-8 border`}
    >
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h3 className="text-2xl font-black text-white mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Processing Cost Estimate
          </h3>
          <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Review the estimated cost and time before proceeding
          </p>
        </div>

        {/* Cost Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700" data-testid="cost-card-total">
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

          <div className="bg-zinc-800/50 rounded-xl p-4 border border-zinc-700" data-testid="cost-card-time">
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

        {/* Detailed Breakdown */}
        <div className="bg-zinc-800/30 rounded-xl p-4 space-y-2" data-testid="cost-card-breakdown">
          <h4 className="text-sm font-bold text-zinc-300 mb-3" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Cost Breakdown
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between text-sm" data-testid="cost-whisper">
              <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>Whisper (Speech-to-Text)</span>
              <span className="text-white font-medium">${estimate.whisper_cost.toFixed(4)}</span>
            </div>
            <div className="flex justify-between text-sm" data-testid="cost-gpt">
              <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>GPT-4o (Translation)</span>
              <span className="text-white font-medium">${estimate.gpt_cost.toFixed(4)}</span>
            </div>
            <div className="flex justify-between text-sm" data-testid="cost-tts">
              <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>OpenAI TTS (Voice Gen)</span>
              <span className="text-white font-medium">${estimate.tts_cost.toFixed(4)}</span>
            </div>
          </div>
        </div>

        {/* Budget Status */}
        <div className="bg-zinc-800/30 rounded-xl p-4 space-y-3" data-testid="cost-card-budget">
          <h4 className="text-sm font-bold text-zinc-300 mb-3" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Budget Status
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>Monthly Remaining</span>
              <span className={`font-medium ${estimate.remaining_monthly_budget < 10 ? 'text-red-400' : 'text-green-400'}`}>
                ₹{estimate.remaining_monthly_budget.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>Daily Remaining</span>
              <span className={`font-medium ${estimate.remaining_daily_budget < 5 ? 'text-red-400' : 'text-green-400'}`}>
                ₹{estimate.remaining_daily_budget.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Warning */}
        {budget_warning && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            data-testid="cost-card-budget-warning"
            className="bg-red-900/20 border border-red-500/30 rounded-xl p-4"
          >
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-300" style={{ fontFamily: 'Manrope, sans-serif' }}>
                {budget_warning}
              </p>
            </div>
          </motion.div>
        )}

        {/* Actions */}
        <div className="flex space-x-3 pt-4">
          <button
            data-testid="cost-card-cancel-btn"
            onClick={onCancel}
            className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-white font-medium transition-all"
            style={{ fontFamily: 'Manrope, sans-serif' }}
          >
            Cancel
          </button>
          <button
            data-testid="cost-card-approve-btn"
            onClick={() => onApprove(estimate)}
            disabled={!can_process}
            className={`flex-1 px-6 py-3 rounded-xl font-medium transition-all ${
              can_process
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white'
                : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'
            }`}
            style={{ fontFamily: 'Manrope, sans-serif' }}
          >
            {can_process ? (
              <span className="flex items-center justify-center space-x-2">
                <CheckCircle className="w-5 h-5" />
                <span>Approve & Start</span>
              </span>
            ) : (
              'Budget Exceeded'
            )}
          </button>
        </div>
      </div>
    </motion.div>
  );
};
