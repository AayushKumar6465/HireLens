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

  // Filter states
  const [minScore, setMinScore] = useState('');
  const [skillFilter, setSkillFilter] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);

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

  // 3. Trigger Re-Score Mutation
  const scoreMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/jobs/${id}/match`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['job-ranking', id]);
    },
  });

  // Handle Drag & Drop / File Selection
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

      // Auto-trigger scoring after upload
      setTimeout(() => {
        scoreMutation.mutate();
      }, 3000);
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Upload failed.';
      setUploadFeedback({ error: msg });
    } finally {
      setIsUploading(false);
    }
  };

  const handleExportCsv = async () => {
    try {
      const res = await api.get(`/jobs/${id}/export.csv`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `job_${id}_ranking.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch {
      alert('Failed to export CSV.');
    }
  };

  if (jobLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-20 bg-white dark:bg-slate-900 rounded-xl" />
        <div className="h-96 bg-white dark:bg-slate-900 rounded-xl" />
      </div>
    );
  }

  if (jobError || !job) {
    return (
      <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-xl border border-rose-200">
        <AlertCircle className="mx-auto h-8 w-8 text-rose-500 mb-2" />
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Job opening not found</h3>
        <p className="text-sm text-slate-500 mt-1">This job may have been removed or does not exist.</p>
        <Link to="/jobs" className="mt-4 inline-flex items-center gap-2 text-sm text-indigo-600 font-semibold">
          <ArrowLeft className="h-4 w-4" /> Return to Jobs
        </Link>
      </div>
    );
  }

  const rankings = rankingData?.items || [];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              to="/jobs"
              className="p-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{job.title}</h1>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-medium uppercase tracking-wider ${
                    job.status === 'open'
                      ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400'
                      : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                  }`}
                >
                  {job.status}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                {job.department && <span>{job.department}</span>}
                {job.location && <span>• {job.location}</span>}
                <span>• Created on {new Date(job.created_at).toLocaleDateString()}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => refetchRanking()}
              disabled={rankingLoading}
              title="Refresh ranking"
              className="p-2 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg transition-colors"
            >
              <RefreshCw className={`h-4 w-4 ${rankingLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => scoreMutation.mutate()}
              disabled={scoreMutation.isPending}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 dark:hover:bg-indigo-900 text-indigo-700 dark:text-indigo-300 text-sm font-semibold rounded-lg transition-colors"
            >
              <Sparkles className="h-4 w-4" />
              {scoreMutation.isPending ? 'Scoring...' : 'Run Match'}
            </button>
            <button
              onClick={handleExportCsv}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm font-medium rounded-lg transition-colors"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Requirements Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
          <span className="text-slate-400 font-medium">Requirements:</span>
          {job.min_experience_years && (
            <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-mono">
              {job.min_experience_years}+ yrs
            </span>
          )}
          {job.education_level && (
            <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 capitalize">
              {job.education_level}
            </span>
          )}
          {job.requirements?.map((req) => (
            <span
              key={req.id || req.skill}
              className={`px-2 py-0.5 rounded font-medium ${
                req.importance === 'required'
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-900'
                  : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
              }`}
            >
              {req.skill}
              {req.importance === 'required' ? ' (req)' : ''}
            </span>
          ))}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab('ranking')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'ranking'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Candidate Ranking ({rankings.length})
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`pb-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'upload'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          Resume Upload Dropzone
        </button>
      </div>

      {/* Tab 1: Candidate Ranking */}
      {activeTab === 'ranking' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={skillFilter}
                onChange={(e) => setSkillFilter(e.target.value)}
                placeholder="Filter by matched skill (e.g. Python, Docker)..."
                className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-slate-500 whitespace-nowrap">Min Score:</label>
              <input
                type="number"
                min="0"
                max="100"
                value={minScore}
                onChange={(e) => setMinScore(e.target.value)}
                placeholder="0"
                className="w-20 px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Ranking Table */}
          {rankingLoading ? (
            <div className="p-8 text-center text-sm text-slate-500 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 animate-pulse">
              Loading ranked candidates...
            </div>
          ) : rankings.length === 0 ? (
            <div className="text-center py-16 px-4 bg-white dark:bg-slate-900 rounded-xl border border-dashed border-slate-300 dark:border-slate-800 space-y-3">
              <Sparkles className="mx-auto h-8 w-8 text-indigo-400" />
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                No candidate matches yet
              </h3>
              <p className="text-sm text-slate-500 max-w-sm mx-auto">
                Upload resumes in the Upload Dropzone tab, then click &ldquo;Run Match&rdquo; to calculate scores and rankings.
              </p>
              <button
                onClick={() => setActiveTab('upload')}
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm"
              >
                Go to Upload Dropzone
              </button>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3 w-12 text-center">Rank</th>
                      <th className="px-4 py-3">Candidate</th>
                      <th className="px-4 py-3 text-center">Total Score</th>
                      <th className="px-4 py-3">Sub-Scores</th>
                      <th className="px-4 py-3">Matched Skills</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {rankings.map((c, idx) => {
                      const total = c.total_score || 0;
                      const scoreColor =
                        total >= 80
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300'
                          : total >= 60
                          ? 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300'
                          : total >= 40
                          ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300'
                          : 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300';

                      return (
                        <tr
                          key={c.match_id}
                          className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors"
                        >
                          <td className="px-4 py-3 text-center font-bold text-slate-400">
                            #{idx + 1}
                          </td>
                          <td className="px-4 py-3">
                            <p className="font-semibold text-slate-900 dark:text-white">
                              {c.candidate_name}
                            </p>
                            <p className="text-xs text-slate-400">{c.candidate_email || 'No email'}</p>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span
                              className={`inline-block px-3 py-1 rounded-full text-xs font-bold border font-mono ${scoreColor}`}
                            >
                              {total.toFixed(1)}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-2 text-xs font-mono text-slate-500">
                              <span title="Skills">S: {c.skill_score ?? '-'}</span>
                              <span title="Semantic">Sem: {c.semantic_score ?? '-'}</span>
                              <span title="Experience">Exp: {c.experience_score ?? '-'}</span>
                              <span title="Education">Edu: {c.education_score ?? '-'}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {c.breakdown?.matched_skills?.slice(0, 3).map((s) => (
                                <span
                                  key={s.skill}
                                  className="text-xs px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 font-medium"
                                >
                                  {s.skill}
                                </span>
                              ))}
                              {c.breakdown?.matched_skills?.length > 3 && (
                                <span className="text-xs text-slate-400">
                                  +{c.breakdown.matched_skills.length - 3}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => setSelectedCandidate(c)}
                              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900 transition-colors"
                            >
                              View Breakdown
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

      {/* Tab 2: Resume Upload Dropzone */}
      {activeTab === 'upload' && (
        <div className="space-y-6">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-slate-300 dark:border-slate-800 rounded-xl p-8 text-center bg-white dark:bg-slate-900 hover:border-indigo-400 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="hidden"
            />
            <UploadCloud className="mx-auto h-12 w-12 text-slate-400 mb-3" />
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">
              Drag &amp; drop resumes here or click to browse
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Supports PDF and DOCX files. Maximum 20 files per batch, up to 5 MB per file.
            </p>
          </div>

          {/* Selected Files Staging List */}
          {selectedFiles.length > 0 && (
            <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  Selected Files ({selectedFiles.length})
                </span>
                <button
                  onClick={() => setSelectedFiles([])}
                  className="text-xs text-slate-400 hover:text-rose-600"
                >
                  Clear all
                </button>
              </div>

              <div className="max-h-48 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                {selectedFiles.map((file, idx) => (
                  <div key={idx} className="py-2 flex items-center justify-between">
                    <span className="font-medium text-slate-700 dark:text-slate-300 truncate max-w-sm">
                      {file.name}
                    </span>
                    <span className="text-slate-400 font-mono">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                ))}
              </div>

              <button
                onClick={handleUploadSubmit}
                disabled={isUploading}
                className="w-full flex justify-center items-center py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-lg shadow-sm disabled:opacity-60"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="animate-spin h-4 w-4 mr-2" />
                    Uploading and Validating...
                  </>
                ) : (
                  `Upload ${selectedFiles.length} Resume(s)`
                )}
              </button>
            </div>
          )}

          {/* Upload Feedback Summary */}
          {uploadFeedback && (
            <div className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 space-y-3">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white">Upload Summary</h4>
              {uploadFeedback.uploaded?.length > 0 && (
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 text-xs rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                  Successfully uploaded {uploadFeedback.uploaded.length} file(s). Processing in background.
                </div>
              )}
              {uploadFeedback.duplicates?.length > 0 && (
                <div className="p-3 bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 text-xs rounded-lg space-y-1">
                  <p className="font-semibold">Duplicates Detected ({uploadFeedback.duplicates.length}):</p>
                  {uploadFeedback.duplicates.map((d, i) => (
                    <p key={i}>• {d.original_filename} (SHA-256 match)</p>
                  ))}
                </div>
              )}
              {uploadFeedback.failed?.length > 0 && (
                <div className="p-3 bg-rose-50 dark:bg-rose-950/30 text-rose-800 dark:text-rose-300 text-xs rounded-lg space-y-1">
                  <p className="font-semibold">Rejected Files ({uploadFeedback.failed.length}):</p>
                  {uploadFeedback.failed.map((f, i) => (
                    <p key={i}>• {f.original_filename}: {f.message}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Candidate Score Breakdown Modal */}
      {selectedCandidate && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-5">
            <div className="flex items-start justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white">
                  {selectedCandidate.candidate_name}
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Match Breakdown &amp; Evidence • Total Score: {selectedCandidate.total_score}
                </p>
              </div>
              <button
                onClick={() => setSelectedCandidate(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Sub-Score Breakdown Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <p className="text-xs text-slate-500 font-medium">Skills (40%)</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white font-mono mt-1">
                  {selectedCandidate.skill_score ?? 'N/A'}
                </p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <p className="text-xs text-slate-500 font-medium">Semantic (30%)</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white font-mono mt-1">
                  {selectedCandidate.semantic_score ?? 'N/A'}
                </p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <p className="text-xs text-slate-500 font-medium">Experience (20%)</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white font-mono mt-1">
                  {selectedCandidate.experience_score ?? 'N/A'}
                </p>
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-xl">
                <p className="text-xs text-slate-500 font-medium">Education (10%)</p>
                <p className="text-lg font-bold text-slate-900 dark:text-white font-mono mt-1">
                  {selectedCandidate.education_score ?? 'N/A'}
                </p>
              </div>
            </div>

            {/* Matched Skills with Evidence */}
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-2">
                Matched Skills &amp; Text Evidence
              </h4>
              <div className="space-y-2">
                {selectedCandidate.breakdown?.matched_skills?.map((item, i) => (
                  <div
                    key={i}
                    className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-indigo-600 dark:text-indigo-400">
                        {item.skill} ({item.importance})
                      </span>
                      <span className="text-slate-400 capitalize">
                        Found in: {item.found_in} • {item.match_type}
                      </span>
                    </div>
                    {item.snippet && (
                      <p className="text-slate-600 dark:text-slate-300 italic">
                        &ldquo;{item.snippet}&rdquo;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Missing Skills */}
            {selectedCandidate.breakdown?.missing_required?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-rose-600 mb-1">Missing Required Skills</h4>
                <div className="flex flex-wrap gap-1.5">
                  {selectedCandidate.breakdown.missing_required.map((s) => (
                    <span
                      key={s}
                      className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 text-xs font-medium"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Calculation Notes */}
            {selectedCandidate.breakdown?.notes?.length > 0 && (
              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-lg text-xs text-slate-500 space-y-1">
                <p className="font-semibold text-slate-700 dark:text-slate-300">Explanation Notes:</p>
                {selectedCandidate.breakdown.notes.map((note, idx) => (
                  <p key={idx}>• {note}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
