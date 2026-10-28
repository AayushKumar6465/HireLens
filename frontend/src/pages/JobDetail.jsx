import { useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  UploadCloud,
  Sparkles,
  Download,
  AlertCircle,
  CheckCircle2,
  X,
  Loader2,
  RefreshCw,
  Search,
  Briefcase,
  MapPin,
  Calendar,
  FileText,
  SlidersHorizontal,
  Trophy,
  Info,
  Check,
  AlertTriangle,
  Scale,
  UserCheck,
  UserX,
} from 'lucide-react';
import api from '@/lib/api';

export default function JobDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const fileInputRef = useRef(null);

  const [activeTab, setActiveTab] = useState('ranking'); // 'ranking' | 'upload'
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadFeedback, setUploadFeedback] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // Filter & Selection states
  const [searchTerm, setSearchTerm] = useState('');
  const [minScore, setMinScore] = useState('');
  const [skillFilter, setSkillFilter] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState([]);

  // Modals & Dialogs
  const [compareModalOpen, setCompareModalOpen] = useState(false);
  const [compareData, setCompareData] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [confirmRejectOpen, setConfirmRejectOpen] = useState(false);
  const [candidateNotes, setCandidateNotes] = useState('');

  // 1. Fetch Job Details
  const {
    data: job,
    isLoading: jobLoading,
    isError: jobError,
  } = useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const res = await api.get(`/jobs/${id}`);
      return res.data;
    },
  });

  // 2. Fetch Candidate Rankings
  const {
    data: rankingData,
    isLoading: rankingLoading,
    refetch: refetchRanking,
  } = useQuery({
    queryKey: ['job-ranking', id, minScore, skillFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (minScore) params.append('min_score', minScore);
      if (skillFilter) params.append('skill', skillFilter);
      params.append('page', '1');
      params.append('page_size', '100');

      const res = await api.get(`/jobs/${id}/ranking?${params.toString()}`);
      return res.data;
    },
    enabled: !!id,
  });

  // 3. Trigger Candidate Scoring / Matching Mutation
  const scoreMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/jobs/${id}/match`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['job-ranking', id]);
      queryClient.invalidateQueries(['dashboard-analytics']);
    },
  });

  // 4. Update Candidate Status Mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({ candidateId, status, notes }) => {
      const res = await api.patch(`/candidates/${candidateId}/status`, {
        status,
        notes: notes !== undefined ? notes : null,
      });
      return res.data;
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries(['job-ranking', id]);
      queryClient.invalidateQueries(['dashboard-analytics']);
      if (selectedCandidate && selectedCandidate.candidate_id === updated.id) {
        setSelectedCandidate({
          ...selectedCandidate,
          candidate_status: updated.status,
          notes: updated.notes,
        });
      }
    },
  });

  // 5. Bulk Status Mutation
  const bulkStatusMutation = useMutation({
    mutationFn: async ({ candidateIds, status }) => {
      const res = await api.post('/candidates/bulk-status', {
        candidate_ids: candidateIds,
        status,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['job-ranking', id]);
      queryClient.invalidateQueries(['dashboard-analytics']);
      setSelectedCandidateIds([]);
      setConfirmRejectOpen(false);
    },
  });

  // File selection & dropzone handling
  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleRemoveStagedFile = (idx) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== idx));
  };

  const handleUploadSubmit = async () => {
    if (selectedFiles.length === 0) return;
    setIsUploading(true);
    setUploadFeedback(null);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('job_id', id);

    try {
      const res = await api.post('/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadFeedback(res.data);
      setSelectedFiles([]);
      if (fileInputRef.current) fileInputRef.current.value = '';

      // Auto-trigger scoring after background parsing settles
      setTimeout(() => {
        scoreMutation.mutate();
      }, 3500);
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Upload failed.';
      setUploadFeedback({ error: msg });
    } finally {
      setIsUploading(false);
    }
  };

  const handleExportCsv = async () => {
    try {
      const res = await api.get(`/jobs/${id}/export.csv`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `hirelens_job_${id}_ranking.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch {
      alert('Failed to export CSV ranking report.');
    }
  };

  const handleDownloadFile = async (resumeId) => {
    try {
      const res = await api.get(`/resumes/${resumeId}/file`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `candidate_resume_${resumeId.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch {
      alert('Unable to download resume file.');
    }
  };

  // Selection toggle handlers
  const handleToggleSelectCandidate = (candidateId) => {
    if (selectedCandidateIds.includes(candidateId)) {
      setSelectedCandidateIds(selectedCandidateIds.filter((cid) => cid !== candidateId));
    } else {
      setSelectedCandidateIds([...selectedCandidateIds, candidateId]);
    }
  };

  const handleSelectAll = (filtered) => {
    if (selectedCandidateIds.length === filtered.length) {
      setSelectedCandidateIds([]);
    } else {
      setSelectedCandidateIds(filtered.map((c) => c.candidate_id));
    }
  };

  const handleOpenCompare = async () => {
    if (selectedCandidateIds.length < 2 || selectedCandidateIds.length > 4) {
      alert('Please select 2 to 4 candidates to compare.');
      return;
    }

    setIsComparing(true);
    try {
      const res = await api.post(`/jobs/${id}/compare`, {
        candidate_ids: selectedCandidateIds,
      });
      setCompareData(res.data);
      setCompareModalOpen(true);
    } catch (err) {
      alert(err.response?.data?.error?.message || 'Failed to compare candidates.');
    } finally {
      setIsComparing(false);
    }
  };

  if (jobLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-32 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800" />
        <div className="h-96 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800" />
      </div>
    );
  }

  if (jobError || !job) {
    return (
      <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-rose-200 dark:border-rose-900 shadow-xs max-w-lg mx-auto">
        <AlertCircle className="mx-auto h-10 w-10 text-rose-500 mb-3" />
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">
          Job Opening Not Found
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          This job may have been removed or does not belong to your account.
        </p>
        <Link
          to="/jobs"
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Return to Jobs
        </Link>
      </div>
    );
  }

  // Filter rankings client-side by candidate name if entered
  const rawRankings = rankingData?.items || [];
  const filteredRankings = rawRankings.filter((c) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    const nameMatch = c.candidate_name?.toLowerCase().includes(term);
    const emailMatch = c.candidate_email?.toLowerCase().includes(term);
    return nameMatch || emailMatch;
  });

  const topCandidate = rawRankings.length > 0 ? rawRankings[0] : null;
  const reqCount = job.requirements?.length || 0;

  // Score threshold helper
  const getScoreTheme = (score) => {
    if (score >= 80) {
      return {
        badge: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
        dot: 'bg-emerald-500',
        label: 'Strong Match',
      };
    }
    if (score >= 60) {
      return {
        badge: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800',
        dot: 'bg-indigo-500',
        label: 'Good Match',
      };
    }
    if (score >= 40) {
      return {
        badge: 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800',
        dot: 'bg-amber-500',
        label: 'Moderate',
      };
    }
    return {
      badge: 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200 dark:border-rose-800',
      dot: 'bg-rose-500',
      label: 'Low Match',
    };
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'screening':
        return 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border-indigo-200';
      case 'interview':
        return 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200';
      case 'offer':
        return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200';
      case 'rejected':
        return 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Hero Header & Control Bar */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-start gap-3">
            <Link
              to="/jobs"
              className="p-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors mt-0.5"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {job.title}
                </h1>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                    job.status === 'open'
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                      : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                  }`}
                >
                  {job.status}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 mt-1 flex-wrap">
                {job.department && (
                  <span className="flex items-center gap-1 font-medium">
                    <Briefcase className="h-3.5 w-3.5 text-slate-400" />
                    {job.department}
                  </span>
                )}
                {job.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5 text-slate-400" />
                    {job.location}
                  </span>
                )}
                <span className="flex items-center gap-1 text-slate-400">
                  <Calendar className="h-3.5 w-3.5" />
                  Created {new Date(job.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 self-start md:self-auto flex-wrap">
            <button
              onClick={() => refetchRanking()}
              disabled={rankingLoading}
              title="Refresh ranking"
              className="p-2 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-xl transition-colors cursor-pointer"
            >
              <RefreshCw
                className={`h-4 w-4 ${rankingLoading ? 'animate-spin' : ''}`}
              />
            </button>
            <button
              onClick={() => scoreMutation.mutate()}
              disabled={scoreMutation.isPending}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs hover:shadow transition-all disabled:opacity-60 cursor-pointer"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>
                {scoreMutation.isPending ? 'Scoring Resumes...' : 'Run Match'}
              </span>
            </button>
            <button
              onClick={handleExportCsv}
              disabled={rawRankings.length === 0}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Real Summary Metrics Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-xs">
          <div className="p-3 bg-slate-50/80 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
            <span className="text-slate-500 dark:text-slate-400 block font-medium">
              Ranked Candidates
            </span>
            <span className="text-lg font-bold text-slate-900 dark:text-white font-mono mt-0.5 block">
              {rawRankings.length}
            </span>
          </div>

          <div className="p-3 bg-slate-50/80 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
            <span className="text-slate-500 dark:text-slate-400 block font-medium">
              Top Score
            </span>
            <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400 font-mono mt-0.5 block">
              {topCandidate ? `${topCandidate.total_score.toFixed(1)}%` : '—'}
            </span>
          </div>

          <div className="p-3 bg-slate-50/80 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
            <span className="text-slate-500 dark:text-slate-400 block font-medium">
              Min Experience
            </span>
            <span className="text-lg font-bold text-slate-900 dark:text-white font-mono mt-0.5 block">
              {job.min_experience_years !== null
                ? `${job.min_experience_years} yrs`
                : 'Any'}
            </span>
          </div>

          <div className="p-3 bg-slate-50/80 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
            <span className="text-slate-500 dark:text-slate-400 block font-medium">
              Target Skills
            </span>
            <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400 font-mono mt-0.5 block">
              {reqCount}
            </span>
          </div>
        </div>

        {/* Requirements Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px]">
          <span className="text-slate-400 font-semibold uppercase tracking-wider mr-1">
            Criteria:
          </span>
          {job.education_level && (
            <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 capitalize font-medium">
              Degree: {job.education_level}
            </span>
          )}
          {job.requirements?.map((req) => (
            <span
              key={req.id || req.skill}
              className={`px-2 py-0.5 rounded-md font-semibold ${
                req.importance === 'required'
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-300 border border-indigo-200/80 dark:border-indigo-800'
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              {req.skill}
              {req.importance === 'required' ? ' (req)' : ''}
            </span>
          ))}
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab('ranking')}
          className={`pb-3 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'ranking'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Trophy className="h-4 w-4" />
          <span>Candidate Rankings</span>
          <span
            className={`px-2 py-0.2 rounded-full text-[10px] font-bold ${
              activeTab === 'ranking'
                ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-800'
            }`}
          >
            {rawRankings.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('upload')}
          className={`pb-3 px-4 text-xs sm:text-sm font-semibold border-b-2 transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'upload'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <UploadCloud className="h-4 w-4" />
          <span>Resume Upload Hub</span>
        </button>
      </div>

      {/* TAB 1: CANDIDATE RANKINGS */}
      {activeTab === 'ranking' && (
        <div className="space-y-4">
          {/* Toolbar: Search, Filters & Bulk Actions */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
            <div className="flex items-center gap-2 flex-1">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search candidates by name or email..."
                  className="w-full pl-9 pr-8 py-2 bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
                />
                {searchTerm && (
                  <button
                    onClick={() => setSearchTerm('')}
                    className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              <div className="relative w-36 sm:w-40">
                <input
                  type="text"
                  value={skillFilter}
                  onChange={(e) => setSkillFilter(e.target.value)}
                  placeholder="Filter by skill..."
                  className="w-full px-3 py-2 bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-lg">
                <SlidersHorizontal className="h-3.5 w-3.5 text-slate-400" />
                <span className="text-[11px] font-medium text-slate-500 whitespace-nowrap">
                  Min Score:
                </span>
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={minScore}
                  onChange={(e) => setMinScore(e.target.value)}
                  placeholder="0"
                  className="w-10 px-1 text-center bg-transparent text-xs font-mono font-bold text-slate-900 dark:text-white focus:outline-none"
                />
              </div>
            </div>

            {/* Bulk Action Controls */}
            {selectedCandidateIds.length > 0 && (
              <div className="flex items-center gap-2 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100 dark:border-slate-800">
                <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400 font-mono">
                  {selectedCandidateIds.length} selected:
                </span>

                <button
                  onClick={() =>
                    bulkStatusMutation.mutate({
                      candidateIds: selectedCandidateIds,
                      status: 'screening',
                    })
                  }
                  title="Mark selected candidates as screening"
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 dark:bg-indigo-950/80 dark:text-indigo-300 rounded-lg text-xs font-semibold"
                >
                  <UserCheck className="h-3.5 w-3.5" />
                  <span>Shortlist</span>
                </button>

                <button
                  onClick={() => setConfirmRejectOpen(true)}
                  title="Mark selected candidates as rejected"
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 dark:bg-rose-950/80 dark:text-rose-300 rounded-lg text-xs font-semibold"
                >
                  <UserX className="h-3.5 w-3.5" />
                  <span>Reject</span>
                </button>

                {selectedCandidateIds.length >= 2 && selectedCandidateIds.length <= 4 && (
                  <button
                    onClick={handleOpenCompare}
                    disabled={isComparing}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200 rounded-lg text-xs font-semibold"
                  >
                    <Scale className="h-3.5 w-3.5" />
                    <span>{isComparing ? 'Comparing...' : 'Compare'}</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Ranking Table */}
          {rankingLoading ? (
            <div className="p-12 text-center text-xs text-slate-500 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 animate-pulse space-y-3">
              <Loader2 className="mx-auto h-6 w-6 animate-spin text-indigo-500" />
              <p>Computing deterministic hybrid scores...</p>
            </div>
          ) : filteredRankings.length === 0 ? (
            <div className="text-center py-16 px-4 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 space-y-3">
              <div className="mx-auto h-12 w-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                {rawRankings.length === 0
                  ? 'No candidate matches computed'
                  : 'No candidates match your current filter'}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto leading-relaxed">
                {rawRankings.length === 0
                  ? 'Upload PDF/DOCX resumes in the Resume Upload Hub, then run matching to calculate rankings.'
                  : 'Try lowering the minimum score or clearing the search keyword.'}
              </p>
              {rawRankings.length === 0 ? (
                <div className="pt-2">
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs"
                  >
                    <UploadCloud className="h-4 w-4" />
                    Open Upload Hub
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setSkillFilter('');
                    setMinScore('');
                  }}
                  className="px-3 py-1.5 bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold"
                >
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm">
                  <thead className="bg-slate-50/80 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 border-b border-slate-200/80 dark:border-slate-800 text-[11px] font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="px-3 py-3.5 w-10 text-center">
                        <input
                          type="checkbox"
                          checked={
                            selectedCandidateIds.length === filteredRankings.length &&
                            filteredRankings.length > 0
                          }
                          onChange={() => handleSelectAll(filteredRankings)}
                          className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                        />
                      </th>
                      <th className="px-3 py-3.5 w-14 text-center">Rank</th>
                      <th className="px-4 py-3.5">Candidate Name</th>
                      <th className="px-4 py-3.5 text-center">Match Score</th>
                      <th className="px-4 py-3.5">Stage</th>
                      <th className="px-4 py-3.5">Sub-Scores</th>
                      <th className="px-4 py-3.5">Matched Skills</th>
                      <th className="px-4 py-3.5">Missing Required</th>
                      <th className="px-4 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                    {filteredRankings.map((c, idx) => {
                      const total = c.total_score || 0;
                      const theme = getScoreTheme(total);
                      const isTopLeader = idx === 0 && !searchTerm && !minScore;
                      const isSelected = selectedCandidateIds.includes(c.candidate_id);

                      return (
                        <tr
                          key={c.match_id}
                          className={`transition-colors ${
                            isSelected
                              ? 'bg-indigo-50/50 dark:bg-indigo-950/30'
                              : 'hover:bg-slate-50/70 dark:hover:bg-slate-800/40'
                          }`}
                        >
                          {/* Row Checkbox */}
                          <td className="px-3 py-3 text-center">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleToggleSelectCandidate(c.candidate_id)}
                              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                            />
                          </td>

                          {/* Rank # */}
                          <td className="px-3 py-3 text-center">
                            {isTopLeader ? (
                              <div className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-amber-100 dark:bg-amber-950/80 text-amber-700 dark:text-amber-300 font-bold text-xs mx-auto">
                                <Trophy className="h-3.5 w-3.5" />
                              </div>
                            ) : (
                              <span className="font-mono font-bold text-slate-400">
                                #{idx + 1}
                              </span>
                            )}
                          </td>

                          {/* Candidate info */}
                          <td className="px-4 py-3">
                            <p className="font-semibold text-slate-900 dark:text-white">
                              {c.candidate_name}
                            </p>
                            <p className="text-[11px] text-slate-400 truncate max-w-xs">
                              {c.candidate_email || 'No email detected'}
                            </p>
                          </td>

                          {/* Total Score Badge */}
                          <td className="px-4 py-3 text-center">
                            <div className="inline-flex flex-col items-center">
                              <span
                                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border font-mono ${theme.badge}`}
                              >
                                <span
                                  className={`h-1.5 w-1.5 rounded-full ${theme.dot}`}
                                />
                                {total.toFixed(1)}%
                              </span>
                              <span className="text-[9px] uppercase font-semibold text-slate-400 mt-0.5">
                                {theme.label}
                              </span>
                            </div>
                          </td>

                          {/* Pipeline Stage Select */}
                          <td className="px-4 py-3">
                            <select
                              value={c.candidate_status || 'new'}
                              onChange={(e) =>
                                updateStatusMutation.mutate({
                                  candidateId: c.candidate_id,
                                  status: e.target.value,
                                })
                              }
                              className={`text-[11px] font-bold px-2 py-1 rounded-md border appearance-none cursor-pointer focus:outline-none ${getStatusBadge(
                                c.candidate_status || 'new'
                              )}`}
                            >
                              <option value="new">New</option>
                              <option value="screening">Screening</option>
                              <option value="interview">Interview</option>
                              <option value="offer">Offer</option>
                              <option value="rejected">Rejected</option>
                            </select>
                          </td>

                          {/* Sub-Scores */}
                          <td className="px-4 py-3">
                            <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px] font-mono text-slate-500 max-w-xs">
                              <span>
                                Skills:{' '}
                                <strong className="text-slate-700 dark:text-slate-300">
                                  {c.skill_score !== null
                                    ? `${c.skill_score.toFixed(0)}%`
                                    : '—'}
                                </strong>
                              </span>
                              <span>
                                Sem:{' '}
                                <strong className="text-slate-700 dark:text-slate-300">
                                  {c.semantic_score !== null
                                    ? `${c.semantic_score.toFixed(0)}%`
                                    : '—'}
                                </strong>
                              </span>
                              <span>
                                Exp:{' '}
                                <strong className="text-slate-700 dark:text-slate-300">
                                  {c.experience_score !== null
                                    ? `${c.experience_score.toFixed(0)}%`
                                    : '—'}
                                </strong>
                              </span>
                              <span>
                                Edu:{' '}
                                <strong className="text-slate-700 dark:text-slate-300">
                                  {c.education_score !== null
                                    ? `${c.education_score.toFixed(0)}%`
                                    : '—'}
                                </strong>
                              </span>
                            </div>
                          </td>

                          {/* Matched Skills */}
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {c.breakdown?.matched_skills?.slice(0, 3).map((s) => (
                                <span
                                  key={s.skill}
                                  className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-semibold border border-emerald-100 dark:border-emerald-900"
                                >
                                  {s.skill}
                                </span>
                              ))}
                              {c.breakdown?.matched_skills?.length > 3 && (
                                <span className="text-[10px] px-1 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono">
                                  +{c.breakdown.matched_skills.length - 3}
                                </span>
                              )}
                              {!c.breakdown?.matched_skills?.length && (
                                <span className="text-[11px] text-slate-400 italic">
                                  None matched
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Missing Required Skills */}
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {c.breakdown?.missing_required?.slice(0, 2).map((s) => (
                                <span
                                  key={s}
                                  className="text-[10px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 font-semibold border border-rose-100 dark:border-rose-900"
                                >
                                  {s}
                                </span>
                              ))}
                              {c.breakdown?.missing_required?.length > 2 && (
                                <span className="text-[10px] px-1 py-0.5 rounded bg-rose-50 text-rose-600 font-mono">
                                  +{c.breakdown.missing_required.length - 2}
                                </span>
                              )}
                              {!c.breakdown?.missing_required?.length && (
                                <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 font-medium">
                                  <Check className="h-3 w-3" /> All satisfied
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => {
                                setSelectedCandidate(c);
                                setCandidateNotes(c.notes || '');
                              }}
                              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/50 dark:hover:bg-indigo-900 text-indigo-700 dark:text-indigo-300 transition-colors cursor-pointer"
                            >
                              Details
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: RESUME UPLOAD HUB */}
      {activeTab === 'upload' && (
        <div className="space-y-5">
          {/* Dropzone Card */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-8 sm:p-12 text-center bg-white dark:bg-slate-900 hover:border-indigo-500 dark:hover:border-indigo-400 transition-all cursor-pointer group"
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="hidden"
            />
            <div className="mx-auto h-14 w-14 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400 mb-3 group-hover:scale-105 transition-transform">
              <UploadCloud className="h-7 w-7" />
            </div>
            <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white">
              Drag &amp; drop resumes here or click to browse
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              Accepts PDF and DOCX documents. Batch limit: 20 files. Max size: 5 MB per file.
            </p>
            <div className="mt-4 flex items-center justify-center gap-2 text-[11px] text-slate-400">
              <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono">
                .PDF
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono">
                .DOCX
              </span>
              <span>• Private isolated storage</span>
            </div>
          </div>

          {/* Staged Files List */}
          {selectedFiles.length > 0 && (
            <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                  Staged for Upload ({selectedFiles.length})
                </span>
                <button
                  onClick={() => setSelectedFiles([])}
                  className="text-xs text-rose-600 hover:text-rose-700 font-semibold"
                >
                  Clear all
                </button>
              </div>

              <div className="max-h-52 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                {selectedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="py-2.5 flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="h-4 w-4 text-indigo-500 shrink-0" />
                      <span className="font-medium text-slate-700 dark:text-slate-300 truncate">
                        {file.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-slate-400 font-mono text-[11px]">
                        {(file.size / 1024).toFixed(1)} KB
                      </span>
                      <button
                        onClick={() => handleRemoveStagedFile(idx)}
                        className="text-slate-400 hover:text-rose-600"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={handleUploadSubmit}
                disabled={isUploading}
                className="w-full flex justify-center items-center py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-xs disabled:opacity-60 transition-all cursor-pointer"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="animate-spin h-4 w-4 mr-2" />
                    Uploading &amp; Parsing Subprocess...
                  </>
                ) : (
                  `Upload & Parse ${selectedFiles.length} Resume(s)`
                )}
              </button>
            </div>
          )}

          {/* Upload Feedback */}
          {uploadFeedback && (
            <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white">
                Upload &amp; Validation Result
              </h4>
              {uploadFeedback.uploaded?.length > 0 && (
                <div className="p-3.5 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs rounded-xl flex items-center gap-2.5">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                  <span>
                    Successfully uploaded {uploadFeedback.uploaded.length} resume(s). Parsing pipeline dispatched in background. Matching will recalculate automatically.
                  </span>
                </div>
              )}
              {uploadFeedback.duplicates?.length > 0 && (
                <div className="p-3.5 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 text-xs rounded-xl space-y-1">
                  <div className="flex items-center gap-1.5 font-bold">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <span>Duplicates Ignored ({uploadFeedback.duplicates.length}):</span>
                  </div>
                  {uploadFeedback.duplicates.map((d, i) => (
                    <p key={i} className="pl-5 text-[11px]">
                      • {d.original_filename} (SHA-256 match found)
                    </p>
                  ))}
                </div>
              )}
              {uploadFeedback.failed?.length > 0 && (
                <div className="p-3.5 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs rounded-xl space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-rose-700">
                    <AlertCircle className="h-4 w-4" />
                    <span>Rejected Files ({uploadFeedback.failed.length}):</span>
                  </div>
                  {uploadFeedback.failed.map((f, i) => (
                    <p key={i} className="pl-5 text-[11px]">
                      • {f.original_filename}: {f.message}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* CANDIDATE SLIDE-OVER DRAWER (PHASE 5 ACCORDANCE) */}
      {selectedCandidate && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-xl bg-white dark:bg-slate-900 h-full overflow-y-auto shadow-2xl border-l border-slate-200 dark:border-slate-800 p-6 space-y-6 animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="flex items-start justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    {selectedCandidate.candidate_name}
                  </h3>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-bold border font-mono ${
                      getScoreTheme(selectedCandidate.total_score).badge
                    }`}
                  >
                    {selectedCandidate.total_score.toFixed(1)}% Match
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  {selectedCandidate.candidate_email || 'No email'} • {selectedCandidate.candidate_phone || 'No phone'}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownloadFile(selectedCandidate.resume_id)}
                  title="Download Original Resume File"
                  className="p-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
                >
                  <Download className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setSelectedCandidate(null)}
                  className="p-2 text-slate-400 hover:text-slate-600 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Stage Selector & Notes Section */}
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-200/60 dark:border-slate-700/60 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300">
                  Pipeline Stage
                </span>
                <select
                  value={selectedCandidate.candidate_status || 'new'}
                  onChange={(e) =>
                    updateStatusMutation.mutate({
                      candidateId: selectedCandidate.candidate_id,
                      status: e.target.value,
                    })
                  }
                  className={`text-xs font-bold px-3 py-1.5 rounded-lg border appearance-none cursor-pointer focus:outline-none ${getStatusBadge(
                    selectedCandidate.candidate_status || 'new'
                  )}`}
                >
                  <option value="new">New</option>
                  <option value="screening">Screening</option>
                  <option value="interview">Interview</option>
                  <option value="offer">Offer</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                  Recruiter Evaluation Notes
                </label>
                <textarea
                  rows={2}
                  value={candidateNotes}
                  onChange={(e) => setCandidateNotes(e.target.value)}
                  placeholder="Add private evaluation notes for this candidate..."
                  className="w-full p-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
                <button
                  type="button"
                  onClick={() =>
                    updateStatusMutation.mutate({
                      candidateId: selectedCandidate.candidate_id,
                      status: selectedCandidate.candidate_status || 'new',
                      notes: candidateNotes,
                    })
                  }
                  disabled={updateStatusMutation.isPending}
                  className="mt-1 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  {updateStatusMutation.isPending ? 'Saving notes...' : 'Save Notes'}
                </button>
              </div>
            </div>

            {/* Sub-Score Bars with Weights */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Scoring Pillars &amp; Weights
              </h4>
              <div className="space-y-3">
                {/* Skills */}
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-slate-700 dark:text-slate-300">
                      Skills Match (45% weight)
                    </span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {selectedCandidate.skill_score !== null
                        ? `${selectedCandidate.skill_score.toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full transition-all"
                      style={{ width: `${selectedCandidate.skill_score || 0}%` }}
                    />
                  </div>
                </div>

                {/* Semantic */}
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-slate-700 dark:text-slate-300">
                      Semantic Similarity (25% weight)
                    </span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {selectedCandidate.semantic_score !== null
                        ? `${selectedCandidate.semantic_score.toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-500 h-full rounded-full transition-all"
                      style={{ width: `${selectedCandidate.semantic_score || 0}%` }}
                    />
                  </div>
                </div>

                {/* Experience */}
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-slate-700 dark:text-slate-300">
                      Experience (15% weight)
                    </span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {selectedCandidate.experience_score !== null
                        ? `${selectedCandidate.experience_score.toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all"
                      style={{ width: `${selectedCandidate.experience_score || 0}%` }}
                    />
                  </div>
                </div>

                {/* Education */}
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span className="text-slate-700 dark:text-slate-300">
                      Education (15% weight)
                    </span>
                    <span className="font-mono font-bold text-slate-900 dark:text-white">
                      {selectedCandidate.education_score !== null
                        ? `${selectedCandidate.education_score.toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-amber-500 h-full rounded-full transition-all"
                      style={{ width: `${selectedCandidate.education_score || 0}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Matched Skills with Verifiable Evidence */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white mb-2">
                Matched Skills &amp; Text Evidence Snippets
              </h4>
              {selectedCandidate.breakdown?.matched_skills?.length > 0 ? (
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {selectedCandidate.breakdown.matched_skills.map((item, i) => (
                    <div
                      key={i}
                      className="p-3 bg-slate-50/80 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1.5">
                          <Check className="h-3.5 w-3.5 text-emerald-500" />
                          {item.skill}
                          <span className="text-[10px] uppercase font-normal text-slate-400">
                            ({item.importance})
                          </span>
                        </span>
                        <span className="text-[10px] text-slate-400 capitalize">
                          Section: {item.found_in || 'body'}
                        </span>
                      </div>
                      {item.snippet ? (
                        <p className="text-slate-600 dark:text-slate-300 italic bg-white dark:bg-slate-900/60 p-2 rounded-lg border border-slate-100 dark:border-slate-800 text-[11px] leading-relaxed">
                          &ldquo;{item.snippet}&rdquo;
                        </p>
                      ) : (
                        <p className="text-slate-400 text-[10px] italic">Exact keyword match confirmed.</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No skills matched the criteria.</p>
              )}
            </div>

            {/* Missing Required Skills */}
            {selectedCandidate.breakdown?.missing_required?.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-rose-600 mb-1.5 flex items-center gap-1">
                  <AlertCircle className="h-3.5 w-3.5" />
                  Missing Required Skills
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedCandidate.breakdown.missing_required.map((s) => (
                    <span
                      key={s}
                      className="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 text-xs font-semibold border border-rose-200 dark:border-rose-900"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Explanation Notes */}
            {selectedCandidate.breakdown?.notes?.length > 0 && (
              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/60 dark:border-slate-800 text-xs text-slate-500 space-y-1">
                <p className="font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                  <Info className="h-3.5 w-3.5 text-indigo-500" />
                  Algorithm Explanation Notes:
                </p>
                {selectedCandidate.breakdown.notes.map((note, idx) => (
                  <p key={idx} className="pl-4 text-[11px]">• {note}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* REJECTION CONFIRMATION DIALOG (PHASE 5 COMPLIANCE: NEVER AUTO-REJECT) */}
      {confirmRejectOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center gap-3 text-rose-600">
              <div className="h-10 w-10 rounded-xl bg-rose-50 dark:bg-rose-950/60 flex items-center justify-center">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Confirm Candidate Rejection
              </h3>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Are you sure you want to mark <strong>{selectedCandidateIds.length} candidate(s)</strong> as rejected?
              HireLens operates as a decision-support system: candidates are never automatically rejected by algorithm scores alone.
            </p>
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                onClick={() => setConfirmRejectOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white rounded-xl border border-slate-200 dark:border-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  bulkStatusMutation.mutate({
                    candidateIds: selectedCandidateIds,
                    status: 'rejected',
                  })
                }
                disabled={bulkStatusMutation.isPending}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl shadow-xs disabled:opacity-50"
              >
                {bulkStatusMutation.isPending ? 'Rejecting...' : 'Yes, Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* COMPARE VIEW MODAL (PHASE 5 REQUIREMENT: 2-4 CANDIDATES SIDE-BY-SIDE) */}
      {compareModalOpen && compareData && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="h-9 w-9 rounded-xl bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-indigo-600">
                  <Scale className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    Candidate Comparison
                  </h3>
                  <p className="text-xs text-slate-400">
                    Job: {compareData.job_title} • {compareData.candidates.length} candidates
                  </p>
                </div>
              </div>
              <button
                onClick={() => setCompareModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-xl"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Candidate Cards Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {compareData.candidates.map((c) => {
                const theme = getScoreTheme(c.total_score);
                return (
                  <div
                    key={c.candidate_id}
                    className="p-4 bg-slate-50/80 dark:bg-slate-800/60 rounded-2xl border border-slate-200/80 dark:border-slate-700 text-center space-y-2"
                  >
                    <p className="font-bold text-xs sm:text-sm text-slate-900 dark:text-white truncate">
                      {c.candidate_name}
                    </p>
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold border font-mono ${theme.badge}`}
                    >
                      {c.total_score.toFixed(1)}%
                    </span>
                    <div className="text-[11px] text-slate-500 font-mono space-y-0.5 pt-1 border-t border-slate-200/60 dark:border-slate-700">
                      <p>Exp: {c.total_experience_years !== null ? `${c.total_experience_years} yrs` : 'N/A'}</p>
                      <p className="capitalize">Edu: {c.highest_degree || 'N/A'}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Unified Skill Matrix */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-white mb-3">
                Unified Skill Matrix
              </h4>
              <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-500 text-[10px] font-semibold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="px-4 py-2.5">Skill</th>
                      <th className="px-3 py-2.5">Priority</th>
                      {compareData.candidates.map((c) => (
                        <th key={c.candidate_id} className="px-3 py-2.5 text-center truncate max-w-[120px]">
                          {c.candidate_name.split(' ')[0]}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {compareData.skill_matrix.map((row) => (
                      <tr key={row.skill} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/30">
                        <td className="px-4 py-2.5 font-semibold text-slate-800 dark:text-slate-200">
                          {row.skill}
                        </td>
                        <td className="px-3 py-2.5">
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider ${
                              row.importance === 'required'
                                ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300'
                                : 'bg-slate-100 text-slate-600 dark:bg-slate-800'
                            }`}
                          >
                            {row.importance}
                          </span>
                        </td>
                        {compareData.candidates.map((c) => {
                          const hasSkill = row.candidate_status[c.candidate_id];
                          return (
                            <td key={c.candidate_id} className="px-3 py-2.5 text-center">
                              {hasSkill ? (
                                <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600">
                                  <Check className="h-3.5 w-3.5" />
                                </span>
                              ) : (
                                <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-rose-100 dark:bg-rose-950 text-rose-500">
                                  <X className="h-3 w-3" />
                                </span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setCompareModalOpen(false)}
                className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-semibold"
              >
                Close Comparison
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
