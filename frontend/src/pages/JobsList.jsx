import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Briefcase,
  MapPin,
  Calendar,
  AlertCircle,
  GraduationCap,
  Clock,
  ArrowRight,
  Sparkles,
  Layers,
  CheckCircle2,
  XCircle,
  X,
  Filter,
} from 'lucide-react';
import api from '@/lib/api';

export default function JobsList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['jobs', searchTerm, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchTerm) params.append('q', searchTerm);
      if (statusFilter) params.append('status', statusFilter);
      params.append('page', '1');
      params.append('page_size', '50');

      const res = await api.get(`/jobs?${params.toString()}`);
      return res.data;
    },
  });

  const jobs = data?.items || [];

  // Genuine dashboard metrics calculated from actual persisted data
  const totalJobs = jobs.length;
  const activeJobs = jobs.filter((j) => j.status === 'open').length;
  const closedJobs = jobs.filter((j) => j.status === 'closed').length;
  const totalSkillsTracked = jobs.reduce(
    (acc, j) => acc + (j.requirements?.length || 0),
    0
  );

  return (
    <div className="space-y-6">
      {/* Top Header & Primary Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Recruitment Pipelines
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-900">
              {totalJobs} Openings
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage job requirements, resume uploads, and candidate match rankings.
          </p>
        </div>
        <Link
          to="/jobs/new"
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-xs hover:shadow transition-all shrink-0 cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          <span>New Job Opening</span>
        </Link>
      </div>

      {/* Genuine Summary Cards (Real Persisted Data) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
            <span>Total Openings</span>
            <Layers className="h-4 w-4 text-indigo-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2 font-mono">
            {totalJobs}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Across all departments</p>
        </div>

        <div className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
            <span>Active Openings</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </div>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-2 font-mono">
            {activeJobs}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Accepting resume uploads</p>
        </div>

        <div className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
            <span>Closed Openings</span>
            <XCircle className="h-4 w-4 text-slate-400" />
          </div>
          <p className="text-2xl font-bold text-slate-600 dark:text-slate-300 mt-2 font-mono">
            {closedJobs}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Hiring completed or archived</p>
        </div>

        <div className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
            <span>Tracked Skills</span>
            <Sparkles className="h-4 w-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2 font-mono">
            {totalSkillsTracked}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Explicit job requirements</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by title, department, or location..."
            className="w-full pl-10 pr-9 py-2 bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex-1 sm:w-44">
            <Filter className="absolute left-3 top-3 h-3.5 w-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full pl-8 pr-8 py-2 bg-slate-50/80 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs sm:text-sm text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 appearance-none cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="open">Active Openings</option>
              <option value="closed">Closed Openings</option>
            </select>
          </div>

          {(searchTerm || statusFilter) && (
            <button
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('');
              }}
              className="px-3 py-2 text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 font-medium whitespace-nowrap"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div
              key={n}
              className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 animate-pulse space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="h-5 bg-slate-200 dark:bg-slate-800 rounded w-1/2" />
                <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-16" />
              </div>
              <div className="h-3 bg-slate-100 dark:bg-slate-800/60 rounded w-3/4" />
              <div className="h-10 bg-slate-50 dark:bg-slate-800/30 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="p-5 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400 shrink-0" />
            <p className="text-xs sm:text-sm font-medium text-rose-800 dark:text-rose-300">
              {error?.response?.data?.error?.message || 'Failed to load jobs.'}
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="text-xs font-semibold px-3 py-1.5 bg-rose-100 dark:bg-rose-900/40 text-rose-800 dark:text-rose-300 rounded-lg hover:bg-rose-200 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && jobs.length === 0 && (
        <div className="text-center py-16 px-4 bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 space-y-3">
          <div className="mx-auto h-12 w-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <Briefcase className="h-6 w-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            {searchTerm || statusFilter ? 'No matching openings' : 'No job openings yet'}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto leading-relaxed">
            {searchTerm || statusFilter
              ? 'No jobs match your current search criteria. Try adjusting or resetting your filters.'
              : 'Create your first job opening to define role requirements, stage resumes, and run automated candidate matching.'}
          </p>
          <div className="pt-2">
            {searchTerm || statusFilter ? (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setStatusFilter('');
                }}
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold rounded-lg transition-colors"
              >
                Clear Filters
              </button>
            ) : (
              <Link
                to="/jobs/new"
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors"
              >
                <Plus className="h-4 w-4" />
                Create First Opening
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Jobs Cards Grid */}
      {!isLoading && !isError && jobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {jobs.map((job) => {
            const reqCount = job.requirements?.length || 0;
            const requiredCount =
              job.requirements?.filter((r) => r.importance === 'required')
                .length || 0;

            return (
              <Link
                key={job.id}
                to={`/jobs/${job.id}`}
                className="group relative p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-500/80 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Top Status & Title */}
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="font-bold text-sm sm:text-base text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-1">
                      {job.title}
                    </h3>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider shrink-0 ${
                        job.status === 'open'
                          ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900'
                          : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                      }`}
                    >
                      {job.status}
                    </span>
                  </div>

                  {/* Metadata Row */}
                  <div className="mt-2 flex flex-wrap gap-y-1.5 gap-x-3 text-xs text-slate-500 dark:text-slate-400">
                    {job.department && (
                      <span className="flex items-center gap-1">
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
                  </div>

                  {/* Description Excerpt */}
                  <p className="mt-3 text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                    {job.description}
                  </p>

                  {/* Requirements Chips */}
                  <div className="mt-4 flex flex-wrap gap-1.5 pt-3 border-t border-slate-100 dark:border-slate-800/80 text-[11px]">
                    {job.min_experience_years !== null && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 font-mono border border-slate-100 dark:border-slate-800">
                        <Clock className="h-3 w-3 text-slate-400" />
                        {job.min_experience_years}+ yrs
                      </span>
                    )}
                    {job.education_level && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 capitalize border border-slate-100 dark:border-slate-800">
                        <GraduationCap className="h-3 w-3 text-slate-400" />
                        {job.education_level}
                      </span>
                    )}
                    {reqCount > 0 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-semibold border border-indigo-100 dark:border-indigo-900/60">
                        {requiredCount} req • {reqCount} total skills
                      </span>
                    )}
                  </div>
                </div>

                {/* Footer Action */}
                <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {new Date(job.created_at).toLocaleDateString()}
                  </span>
                  <span className="font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                    Candidate Pipeline <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
