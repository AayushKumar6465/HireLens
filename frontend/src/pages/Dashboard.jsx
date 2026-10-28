import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Briefcase,
  Users,
  FileCheck2,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Filter,
  AlertCircle,
  PlusCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

export default function Dashboard() {
  const { user } = useAuth();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: async () => {
      const res = await api.get('/analytics/dashboard');
      return res.data;
    },
  });

  const getScoreColor = (label) => {
    if (label.includes('80-100%')) return '#10b981'; // emerald
    if (label.includes('60-79%')) return '#6366f1'; // indigo
    if (label.includes('40-59%')) return '#f59e0b'; // amber
    return '#f43f5e'; // rose
  };

  const funnelColors = {
    new: '#64748b',
    screening: '#6366f1',
    interview: '#3b82f6',
    offer: '#10b981',
    rejected: '#f43f5e',
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
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
            Recruitment Intelligence
          </span>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white mt-1">
            Welcome back, {user?.full_name?.split(' ')[0] || 'Recruiter'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Live overview of candidate screening accuracy, pipeline stages, and score distributions.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Link
            to="/jobs/new"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs hover:shadow transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Create Opening</span>
          </Link>
        </div>
      </div>

      {isError && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-2 text-rose-800 dark:text-rose-300 text-xs">
            <AlertCircle className="h-4 w-4" />
            <span>{error?.response?.data?.error?.message || 'Failed to load dashboard metrics.'}</span>
          </div>
          <button
            onClick={() => refetch()}
            className="text-xs font-semibold px-3 py-1 bg-rose-100 dark:bg-rose-900/40 text-rose-800 dark:text-rose-200 rounded-lg"
          >
            Retry
          </button>
        </div>
      )}

      {/* 4 Primary StatCards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Openings
            </span>
            <div className="h-8 w-8 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
              <Briefcase className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
              {isLoading ? '—' : data?.open_jobs ?? 0}
            </span>
            <span className="text-[11px] text-slate-400 block mt-0.5">
              Positions accepting resumes
            </span>
          </div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Candidates
            </span>
            <div className="h-8 w-8 rounded-xl bg-blue-50 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
              {isLoading ? '—' : data?.total_candidates ?? 0}
            </span>
            <span className="text-[11px] text-slate-400 block mt-0.5">
              Across all hiring funnels
            </span>
          </div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Processed Resumes
            </span>
            <div className="h-8 w-8 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <FileCheck2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-bold font-mono text-slate-900 dark:text-white">
              {isLoading ? '—' : data?.resumes_processed ?? 0}
            </span>
            <span className="text-[11px] text-slate-400 block mt-0.5">
              Parsed into structured data
            </span>
          </div>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Average Match
            </span>
            <div className="h-8 w-8 rounded-xl bg-amber-50 dark:bg-amber-950/60 flex items-center justify-center text-amber-600 dark:text-amber-400">
              <Sparkles className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl sm:text-3xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
              {isLoading ? '—' : `${data?.avg_match_score ?? 0}%`}
            </span>
            <span className="text-[11px] text-slate-400 block mt-0.5">
              Across scored applications
            </span>
          </div>
        </div>
      </div>

      {/* Two Interactive Recharts Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Score Distribution Chart */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4 text-indigo-500" />
                Score Distribution
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Candidates grouped by hybrid match score brackets
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400 animate-pulse">
                Loading distribution metrics...
              </div>
            ) : data?.score_distribution?.every((b) => b.count === 0) ? (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-400 space-y-2">
                <Sparkles className="h-6 w-6 text-slate-300" />
                <span>No scored candidate resumes yet</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.score_distribution || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
                  <XAxis dataKey="range_label" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderColor: '#334155',
                      borderRadius: '0.75rem',
                      color: '#fff',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {data?.score_distribution?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getScoreColor(entry.range_label)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Recruitment Pipeline Funnel */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                <Filter className="h-4 w-4 text-indigo-500" />
                Pipeline Funnel
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Current candidate progression stages
              </p>
            </div>
          </div>

          <div className="h-64 w-full">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400 animate-pulse">
                Loading pipeline stages...
              </div>
            ) : data?.status_funnel?.every((s) => s.count === 0) ? (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-400 space-y-2">
                <Users className="h-6 w-6 text-slate-300" />
                <span>No candidates in pipeline yet</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data?.status_funnel || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
                  <XAxis dataKey="status" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 10 }} stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderColor: '#334155',
                      borderRadius: '0.75rem',
                      color: '#fff',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {data?.status_funnel?.map((entry, index) => (
                      <Cell key={`funnel-${index}`} fill={funnelColors[entry.status] || '#6366f1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Recent Candidates Activity Table */}
      <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Recent Candidate Screenings
            </h2>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Latest candidate matches scored across your openings
            </p>
          </div>
          <Link
            to="/jobs"
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 flex items-center gap-1"
          >
            <span>All Pipelines</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-400 animate-pulse">
            Loading recent matches...
          </div>
        ) : !data?.recent_candidates?.length ? (
          <div className="text-center py-10 text-xs text-slate-400 space-y-2">
            <Users className="mx-auto h-8 w-8 text-slate-300" />
            <p>No candidate resumes scored yet. Create a job opening and upload resumes to start screening.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/70 dark:bg-slate-800/40 text-slate-400 text-[10px] font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-2.5">Candidate</th>
                  <th className="px-4 py-2.5">Job Opening</th>
                  <th className="px-4 py-2.5 text-center">Score</th>
                  <th className="px-4 py-2.5">Stage</th>
                  <th className="px-4 py-2.5 text-right">Scored On</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {data.recent_candidates.map((cand) => (
                  <tr key={cand.candidate_id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                      {cand.candidate_name}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/jobs/${cand.job_id}`}
                        className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-medium hover:underline"
                      >
                        {cand.job_title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="font-mono font-bold px-2 py-0.5 rounded-full text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200">
                        {cand.total_score.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusBadge(cand.status)}`}>
                        {cand.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-slate-400 font-mono text-[11px]">
                      {cand.created_at ? new Date(cand.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
