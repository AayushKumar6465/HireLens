import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Sliders,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldCheck,
  User,
} from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';

function ScoringWeightsConfig({ initialWeights, onUpdated, onError, onOpenRescoreConfirm }) {
  const queryClient = useQueryClient();

  const [skillsWeight, setSkillsWeight] = useState(
    Math.round((initialWeights?.skills ?? 0.45) * 100)
  );
  const [semanticWeight, setSemanticWeight] = useState(
    Math.round((initialWeights?.semantic ?? 0.25) * 100)
  );
  const [experienceWeight, setExperienceWeight] = useState(
    Math.round((initialWeights?.experience ?? 0.15) * 100)
  );
  const [educationWeight, setEducationWeight] = useState(
    Math.round((initialWeights?.education ?? 0.15) * 100)
  );

  const currentSum =
    Number(skillsWeight) +
    Number(semanticWeight) +
    Number(experienceWeight) +
    Number(educationWeight);
  const isValidSum = currentSum === 100;

  // Mutation to update weights
  const updateWeightsMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        skills: Number(skillsWeight) / 100,
        semantic: Number(semanticWeight) / 100,
        experience: Number(experienceWeight) / 100,
        education: Number(educationWeight) / 100,
      };
      const res = await api.put('/settings/scoring-weights', payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['scoring-weights']);
      onUpdated('Scoring weights updated successfully.');
      onOpenRescoreConfirm();
    },
    onError: (err) => {
      onError(err.response?.data?.error?.message || 'Failed to update weights.');
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
            <Sliders className="h-4 w-4 text-indigo-500" />
            Scoring Weights Configuration
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Adjust how the 4 composite pillars contribute to candidate ranking. Sliders must sum to 100%.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold font-mono border ${
              isValidSum
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200'
                : 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200'
            }`}
          >
            Total: {currentSum}% {isValidSum ? '✓ Valid' : '(Must be 100%)'}
          </span>
        </div>
      </div>

      <div className="space-y-5">
        {/* 1. Skills Weight Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-medium">
            <span className="text-slate-700 dark:text-slate-300">
              Skills Match Weight (Keywords &amp; Evidence)
            </span>
            <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
              {skillsWeight}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={skillsWeight}
            onChange={(e) => setSkillsWeight(Number(e.target.value))}
            className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <p className="text-[11px] text-slate-400">
            Matches canonical skills and aliases against job criteria (required skills carry 2x weight).
          </p>
        </div>

        {/* 2. Semantic Weight Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-medium">
            <span className="text-slate-700 dark:text-slate-300">
              Semantic Similarity Weight (TF-IDF Cosine)
            </span>
            <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
              {semanticWeight}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={semanticWeight}
            onChange={(e) => setSemanticWeight(Number(e.target.value))}
            className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <p className="text-[11px] text-slate-400">
            Monotonically calibrated TF-IDF cosine comparison between full job description and resume text.
          </p>
        </div>

        {/* 3. Experience Weight Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-medium">
            <span className="text-slate-700 dark:text-slate-300">
              Experience Duration Weight
            </span>
            <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
              {experienceWeight}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={experienceWeight}
            onChange={(e) => setExperienceWeight(Number(e.target.value))}
            className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <p className="text-[11px] text-slate-400">
            Calculates ratio between candidate total years and required role experience.
          </p>
        </div>

        {/* 4. Education Weight Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-medium">
            <span className="text-slate-700 dark:text-slate-300">
              Education Hierarchy Weight
            </span>
            <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
              {educationWeight}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={educationWeight}
            onChange={(e) => setEducationWeight(Number(e.target.value))}
            className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
          />
          <p className="text-[11px] text-slate-400">
            Standardized rank comparison from High School to Doctorate degree levels.
          </p>
        </div>

        {/* Reset to Defaults */}
        <div className="pt-2 flex items-center justify-between">
          <button
            type="button"
            onClick={() => {
              setSkillsWeight(45);
              setSemanticWeight(25);
              setExperienceWeight(15);
              setEducationWeight(15);
            }}
            className="text-xs text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-semibold cursor-pointer"
          >
            Reset to Standard Defaults (45 / 25 / 15 / 15)
          </button>

          <button
            type="button"
            disabled={!isValidSum || updateWeightsMutation.isPending}
            onClick={() => updateWeightsMutation.mutate()}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs disabled:opacity-50 transition-all cursor-pointer"
          >
            {updateWeightsMutation.isPending ? (
              <>
                <Loader2 className="animate-spin h-4 w-4" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Save Weights &amp; Re-score</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const queryClient = useQueryClient();

  const [feedback, setFeedback] = useState(null);
  const [confirmRescoreOpen, setConfirmRescoreOpen] = useState(false);

  // Fetch current active weights
  const { data: weightsData, isLoading: weightsLoading } = useQuery({
    queryKey: ['scoring-weights'],
    queryFn: async () => {
      const res = await api.get('/settings/scoring-weights');
      return res.data;
    },
  });

  // Mutation to re-score all candidates
  const rescoreAllMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/settings/re-score-all');
      return res.data;
    },
    onSuccess: (data) => {
      setConfirmRescoreOpen(false);
      setFeedback({
        type: 'success',
        message: data.message || 'All candidate matches re-scored with new weights.',
      });
      queryClient.invalidateQueries(['dashboard-analytics']);
    },
    onError: (err) => {
      setFeedback({
        type: 'error',
        message: err.response?.data?.error?.message || 'Failed to re-score candidates.',
      });
    },
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Workspace Settings
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          Customize algorithm scoring weights, manage recruiter profile, and adjust workspace theme.
        </p>
      </div>

      {feedback && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center justify-between ${
            feedback.type === 'success'
              ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200'
              : 'bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
            )}
            <span>{feedback.message}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-xs font-semibold opacity-70 hover:opacity-100 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Section 1: Scoring Weights Sliders */}
      <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
        {weightsLoading ? (
          <div className="py-8 text-center text-xs text-slate-400 animate-pulse">
            Loading active weights...
          </div>
        ) : (
          <ScoringWeightsConfig
            key={weightsData?.updated_at || 'scoring-weights'}
            initialWeights={weightsData}
            onUpdated={(msg) => setFeedback({ type: 'success', message: msg })}
            onError={(msg) => setFeedback({ type: 'error', message: msg })}
            onOpenRescoreConfirm={() => setConfirmRescoreOpen(true)}
          />
        )}
      </div>

      {/* Section 2: Recruiter Profile & Appearance */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {/* Profile Card */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <User className="h-4 w-4 text-indigo-500" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Recruiter Account
            </h2>
          </div>
          <div className="space-y-2 text-xs">
            <div>
              <span className="text-slate-400 block font-medium">Full Name</span>
              <span className="font-semibold text-slate-900 dark:text-white text-sm">
                {user?.full_name || 'Recruiter'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-medium">Email Address</span>
              <span className="font-semibold text-slate-900 dark:text-white">
                {user?.email || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-medium">Role Permission</span>
              <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                {user?.role || 'recruiter'}
              </span>
            </div>
          </div>
        </div>

        {/* Appearance & Theme Card */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Workspace Appearance
            </h2>
          </div>
          <div className="space-y-3 text-xs">
            <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
              Toggle between high-contrast light mode and reduced eye-strain dark mode. Your preference is persisted automatically.
            </p>
            <div className="pt-1">
              <button
                type="button"
                onClick={toggleTheme}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs transition-colors cursor-pointer"
              >
                <span>Current Theme:</span>
                <span className="capitalize font-bold text-indigo-600 dark:text-indigo-400">
                  {theme} Mode
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Dialog for Re-score All */}
      {confirmRescoreOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center gap-3 text-indigo-600 dark:text-indigo-400">
              <div className="h-10 w-10 rounded-xl bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center">
                <RefreshCw className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Re-score All Active Pipelines?
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Weights have been saved. Would you like to recalculate match scores across all uploaded candidate resumes now? This operation is deterministic and re-uses existing parsed text.
            </p>
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                onClick={() => setConfirmRescoreOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white rounded-xl border border-slate-200 dark:border-slate-700 cursor-pointer"
              >
                No, Later
              </button>
              <button
                onClick={() => rescoreAllMutation.mutate()}
                disabled={rescoreAllMutation.isPending}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs disabled:opacity-50 cursor-pointer"
              >
                {rescoreAllMutation.isPending ? (
                  <>
                    <Loader2 className="animate-spin h-3.5 w-3.5" />
                    <span>Re-scoring...</span>
                  </>
                ) : (
                  'Yes, Re-score All'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}