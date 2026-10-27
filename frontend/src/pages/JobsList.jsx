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

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Job Openings
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage your hiring pipelines, uploaded resumes, and candidate match rankings.
          </p>
        </div>
        <Link
          to="/jobs/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors shrink-0"
        >
          <Plus className="h-4 w-4" />
          Create Opening
        </Link>
      </div>

      {/* Filters and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by title, department, or location..."
            className="w-full pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div
              key={n}
              className="p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 animate-pulse space-y-4"
            >
              <div className="h-5 bg-slate-200 dark:bg-slate-800 rounded w-3/4" />
              <div className="h-4 bg-slate-100 dark:bg-slate-800/60 rounded w-1/2" />
              <div className="h-12 bg-slate-50 dark:bg-slate-800/30 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="p-6 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900 rounded-xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400" />
            <p className="text-sm font-medium text-rose-800 dark:text-rose-300">
              {error?.response?.data?.error?.message || 'Failed to load jobs.'}
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="text-xs font-semibold px-3 py-1.5 bg-rose-100 dark:bg-rose-900/40 text-rose-800 dark:text-rose-300 rounded hover:bg-rose-200"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && jobs.length === 0 && (
        <div className="text-center py-16 px-4 bg-white dark:bg-slate-900 rounded-xl border border-dashed border-slate-300 dark:border-slate-800 space-y-3">
          <div className="mx-auto h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
            <Briefcase className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No job openings found
          </h3>
          <p className="text-sm text-slate-500 max-w-sm mx-auto">
            {searchTerm || statusFilter
              ? 'No jobs match your current search criteria. Try clearing the filters.'
              : 'Get started by creating your first job opening to screen and rank candidate resumes.'}
          </p>
          {!searchTerm && !statusFilter && (
            <div className="pt-2">
              <Link
                to="/jobs/new"
                className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm"
              >
                <Plus className="h-4 w-4" />
                Create First Opening
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Jobs Grid */}
      {!isLoading && !isError && jobs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {jobs.map((job) => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="group p-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-500 shadow-sm hover:shadow transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-1">
                    {job.title}
                  </h3>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium uppercase tracking-wider shrink-0 ${
                      job.status === 'open'
                        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                    }`}
                  >
                    {job.status}
                  </span>
                </div>

                <div className="mt-3 flex flex-wrap gap-y-2 gap-x-3 text-xs text-slate-500 dark:text-slate-400">
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

                <p className="mt-3 text-xs text-slate-600 dark:text-slate-400 line-clamp-2">
                  {job.description}
                </p>

                {/* Badges for Requirements */}
                <div className="mt-4 flex flex-wrap gap-2 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                  {job.min_experience_years !== null && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 font-mono">
                      <Clock className="h-3 w-3 text-slate-400" />
                      {job.min_experience_years}+ yrs
                    </span>
                  )}
                  {job.education_level && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 capitalize">
                      <GraduationCap className="h-3 w-3 text-slate-400" />
                      {job.education_level}
                    </span>
                  )}
                  {job.requirements?.length > 0 && (
                    <span className="inline-flex items-center px-2 py-1 rounded bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-medium">
                      {job.requirements.length} skills required
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {new Date(job.created_at).toLocaleDateString()}
                </span>
                <span className="font-semibold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                  View Pipeline <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
