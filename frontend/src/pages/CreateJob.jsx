import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  Plus,
  Trash2,
  AlertCircle,
  Loader2,
  Briefcase,
  MapPin,
  Clock,
  GraduationCap,
  FileText,
  CheckCircle2,
} from 'lucide-react';
import api from '@/lib/api';

export default function CreateJob() {
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [location, setLocation] = useState('');
  const [minExperience, setMinExperience] = useState('');
  const [educationLevel, setEducationLevel] = useState('');
  const [description, setDescription] = useState('');

  const [requirements, setRequirements] = useState([
    { skill: 'Python', importance: 'required', weight: 1.0 },
    { skill: 'SQL', importance: 'required', weight: 1.0 },
    { skill: 'Docker', importance: 'preferred', weight: 1.0 },
  ]);

  const [newSkillInput, setNewSkillInput] = useState('');
  const [newSkillImportance, setNewSkillImportance] = useState('required');

  const [isExtracting, setIsExtracting] = useState(false);
  const [extractSuccess, setExtractSuccess] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleAddCustomSkill = (e) => {
    e?.preventDefault();
    const trimmed = newSkillInput.trim();
    if (!trimmed) return;

    if (requirements.some((r) => r.skill.toLowerCase() === trimmed.toLowerCase())) {
      setError(`Skill "${trimmed}" is already added.`);
      return;
    }

    setRequirements([
      ...requirements,
      { skill: trimmed, importance: newSkillImportance, weight: 1.0 },
    ]);
    setNewSkillInput('');
    setError(null);
  };

  const handleToggleImportance = (index) => {
    const updated = [...requirements];
    updated[index].importance =
      updated[index].importance === 'required' ? 'preferred' : 'required';
    setRequirements(updated);
  };

  const handleRemoveRequirement = (index) => {
    setRequirements(requirements.filter((_, i) => i !== index));
  };

  const handleExtractFromDescription = async () => {
    if (!description.trim()) {
      setError('Please provide a job description first to extract requirements.');
      return;
    }

    setIsExtracting(true);
    setExtractSuccess(false);
    setError(null);

    try {
      // Create temporary job to leverage backend extract-requirements endpoint
      const tempJob = await api.post('/jobs', {
        title: title || 'Draft Opening',
        description,
        department: department || null,
        location: location || null,
        min_experience_years: minExperience ? parseFloat(minExperience) : null,
        education_level: educationLevel || null,
        requirements: [],
      });

      const extractRes = await api.post(
        `/jobs/${tempJob.data.id}/extract-requirements`
      );
      const extracted = extractRes.data.extracted_skills || [];

      if (extracted.length > 0) {
        setRequirements(
          extracted.map((item) => ({
            skill: item.skill,
            importance: item.importance,
            weight: item.suggested_weight || 1.0,
          }))
        );
        setExtractSuccess(true);
      }

      if (extractRes.data.suggested_min_experience_years && !minExperience) {
        setMinExperience(
          extractRes.data.suggested_min_experience_years.toString()
        );
      }
      if (extractRes.data.suggested_education_level && !educationLevel) {
        setEducationLevel(extractRes.data.suggested_education_level);
      }

      // Cleanup draft job
      await api.delete(`/jobs/${tempJob.data.id}`);
    } catch {
      setError('Unable to auto-extract skills. You can still add skills manually below.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const payload = {
        title,
        description,
        department: department || null,
        location: location || null,
        min_experience_years: minExperience ? parseFloat(minExperience) : null,
        education_level: educationLevel || null,
        requirements: requirements
          .filter((r) => r.skill.trim())
          .map((r) => ({
            skill: r.skill.trim(),
            importance: r.importance,
            weight: parseFloat(r.weight) || 1.0,
          })),
      };

      const res = await api.post('/jobs', payload);
      navigate(`/jobs/${res.data.id}`);
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Failed to create job opening.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Breadcrumb & Heading */}
      <div className="flex items-center gap-3">
        <Link
          to="/jobs"
          className="p-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Create Job Opening
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Define role parameters, experience expectations, and skill requirements for automated scoring.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 flex items-start gap-3">
          <AlertCircle className="h-4 w-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
          <p className="text-xs text-rose-700 dark:text-rose-300 font-medium">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Role Overview */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <Briefcase className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              1. Role Overview
            </h2>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
              Job Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Backend Engineer"
              className="w-full px-3.5 py-2.5 bg-slate-50/60 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Department
              </label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-3 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="e.g. Engineering, Product"
                  className="w-full pl-9 pr-3.5 py-2.5 bg-slate-50/60 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Location
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Remote, San Francisco, CA"
                  className="w-full pl-9 pr-3.5 py-2.5 bg-slate-50/60 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Experience & Education Standards */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
            <Clock className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              2. Experience &amp; Education Criteria
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Minimum Experience (Years)
              </label>
              <div className="relative">
                <Clock className="absolute left-3 top-3 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="number"
                  min="0"
                  max="40"
                  step="0.5"
                  value={minExperience}
                  onChange={(e) => setMinExperience(e.target.value)}
                  placeholder="e.g. 3.0"
                  className="w-full pl-9 pr-3.5 py-2.5 bg-slate-50/60 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Leave blank if no minimum experience requirement.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5">
                Minimum Education Level
              </label>
              <div className="relative">
                <GraduationCap className="absolute left-3 top-3 h-3.5 w-3.5 text-slate-400" />
                <select
                  value={educationLevel}
                  onChange={(e) => setEducationLevel(e.target.value)}
                  className="w-full pl-9 pr-3.5 py-2.5 bg-slate-50/60 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 transition-all"
                >
                  <option value="">No Minimum Degree Required</option>
                  <option value="high_school">High School</option>
                  <option value="associate">Associate Degree</option>
                  <option value="bachelor">Bachelor&apos;s Degree</option>
                  <option value="master">Master&apos;s Degree</option>
                  <option value="doctorate">Doctorate / Ph.D.</option>
                </select>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Evaluated against normalized educational taxonomy.
              </p>
            </div>
          </div>
        </div>

        {/* Section 3: Job Description & Auto-Extractor */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                3. Role Description
              </h2>
            </div>
            <button
              type="button"
              onClick={handleExtractFromDescription}
              disabled={isExtracting || !description.trim()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-950/70 hover:bg-indigo-100 dark:hover:bg-indigo-900 text-indigo-700 dark:text-indigo-300 text-xs font-semibold border border-indigo-100 dark:border-indigo-800 transition-all disabled:opacity-50 cursor-pointer"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="animate-spin h-3.5 w-3.5 mr-1" />
                  Extracting...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                  Extract Requirements with AI
                </>
              )}
            </button>
          </div>

          {extractSuccess && (
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs rounded-xl flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>Skills and criteria extracted successfully from description! Review and adjust below.</span>
            </div>
          )}

          <div>
            <textarea
              required
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste or write the complete role description, responsibilities, and expected technical stack..."
              className="w-full px-3.5 py-3 bg-slate-50/60 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 leading-relaxed transition-all"
            />
          </div>
        </div>

        {/* Section 4: Target Requirements & Skill Weights */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                4. Skill Requirements ({requirements.length})
              </h2>
            </div>
            <span className="text-xs text-slate-400">
              Required skills carry <span className="font-semibold text-indigo-600 dark:text-indigo-400">2x weight</span>
            </span>
          </div>

          {/* Quick-add skill input */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200/60 dark:border-slate-800">
            <input
              type="text"
              value={newSkillInput}
              onChange={(e) => setNewSkillInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddCustomSkill();
                }
              }}
              placeholder="Type a skill (e.g. FastAPI, PostgreSQL, Kubernetes)..."
              className="flex-1 px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600"
            />
            <div className="flex items-center gap-2">
              <select
                value={newSkillImportance}
                onChange={(e) => setNewSkillImportance(e.target.value)}
                className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 focus:outline-none"
              >
                <option value="required">Required (2x)</option>
                <option value="preferred">Preferred (1x)</option>
              </select>
              <button
                type="button"
                onClick={handleAddCustomSkill}
                className="inline-flex items-center gap-1 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors shrink-0"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add</span>
              </button>
            </div>
          </div>

          {/* Requirements Badges List */}
          {requirements.length === 0 ? (
            <p className="text-xs text-slate-400 py-3 text-center italic">
              No skills added yet. Type above or extract directly from the description.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2 pt-2">
              {requirements.map((req, idx) => (
                <div
                  key={idx}
                  className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs transition-all ${
                    req.importance === 'required'
                      ? 'bg-indigo-50/80 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-200 border-indigo-200 dark:border-indigo-800/80'
                      : 'bg-slate-100/80 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                  }`}
                >
                  <span className="font-semibold">{req.skill}</span>
                  <button
                    type="button"
                    onClick={() => handleToggleImportance(idx)}
                    title="Click to toggle Required / Preferred"
                    className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider transition-colors ${
                      req.importance === 'required'
                        ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-300'
                    }`}
                  >
                    {req.importance === 'required' ? 'Req (2x)' : 'Pref (1x)'}
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRemoveRequirement(idx)}
                    className="text-slate-400 hover:text-rose-600 p-0.5 transition-colors"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submit Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Link
            to="/jobs"
            className="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-xs hover:shadow transition-all disabled:opacity-60 cursor-pointer"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin h-4 w-4 mr-1.5" />
                Publishing Opening...
              </>
            ) : (
              'Publish Job Opening'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
