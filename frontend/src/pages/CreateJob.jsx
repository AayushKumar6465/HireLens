import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Sparkles,
  Plus,
  Trash2,
  AlertCircle,
  Loader2,
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
  ]);

  const [isExtracting, setIsExtracting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleAddRequirement = () => {
    setRequirements([...requirements, { skill: '', importance: 'required', weight: 1.0 }]);
  };

  const handleRemoveRequirement = (index) => {
    setRequirements(requirements.filter((_, i) => i !== index));
  };

  const handleRequirementChange = (index, field, value) => {
    const updated = [...requirements];
    updated[index][field] = value;
    setRequirements(updated);
  };

  const handleExtractFromDescription = async () => {
    if (!description.trim()) {
      setError('Please provide a job description first to extract requirements.');
      return;
    }

    setIsExtracting(true);
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

      const extractRes = await api.post(`/jobs/${tempJob.data.id}/extract-requirements`);
      const extracted = extractRes.data.extracted_skills || [];

      if (extracted.length > 0) {
        setRequirements(
          extracted.map((item) => ({
            skill: item.skill,
            importance: item.importance,
            weight: item.suggested_weight || 1.0,
          }))
        );
      }

      if (extractRes.data.suggested_min_experience_years && !minExperience) {
        setMinExperience(extractRes.data.suggested_min_experience_years.toString());
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
      const validRequirements = requirements
        .filter((r) => r.skill.trim())
        .map((r) => ({
          skill: r.skill.trim(),
          importance: r.importance,
          weight: parseFloat(r.weight) || 1.0,
        }));

      const payload = {
        title: title.strip ? title.strip() : title.trim(),
        description: description.trim(),
        department: department.trim() || null,
        location: location.trim() || null,
        min_experience_years: minExperience ? parseFloat(minExperience) : null,
        education_level: educationLevel || null,
        requirements: validRequirements,
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
      <div className="flex items-center gap-3">
        <Link
          to="/jobs"
          className="p-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Create New Job Opening
          </h1>
          <p className="text-sm text-slate-500">
            Define requirements and description to screen candidate resumes.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
          <p className="text-sm text-rose-700 dark:text-rose-300">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-3">
            Position Details
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Job Title *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Senior Full Stack Engineer"
                className="mt-1 block w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Department
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                placeholder="Engineering"
                className="mt-1 block w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Remote / New York, NY"
                className="mt-1 block w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Minimum Experience (Years)
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={minExperience}
                onChange={(e) => setMinExperience(e.target.value)}
                placeholder="3.0"
                className="mt-1 block w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Education Level
              </label>
              <select
                value={educationLevel}
                onChange={(e) => setEducationLevel(e.target.value)}
                className="mt-1 block w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">No Degree Required</option>
                <option value="high_school">High School</option>
                <option value="associate">Associate Degree</option>
                <option value="bachelor">Bachelor&apos;s Degree</option>
                <option value="master">Master&apos;s Degree</option>
                <option value="doctorate">Doctorate / Ph.D.</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Job Description *
              </label>
              <button
                type="button"
                onClick={handleExtractFromDescription}
                disabled={isExtracting}
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700"
              >
                <Sparkles className="h-3.5 w-3.5" />
                {isExtracting ? 'Extracting...' : 'Auto-Extract Requirements'}
              </button>
            </div>
            <textarea
              required
              rows={6}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste or write the full job description here..."
              className="mt-1 block w-full px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Skill Requirements Section */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Skill Requirements
              </h2>
              <p className="text-xs text-slate-500">
                Required skills count 2x towards candidate match score.
              </p>
            </div>
            <button
              type="button"
              onClick={handleAddRequirement}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium rounded-lg transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Skill
            </button>
          </div>

          <div className="space-y-3">
            {requirements.map((req, index) => (
              <div key={index} className="flex items-center gap-3">
                <input
                  type="text"
                  required
                  value={req.skill}
                  onChange={(e) => handleRequirementChange(index, 'skill', e.target.value)}
                  placeholder="e.g. Python, Docker, React"
                  className="flex-1 px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-indigo-500"
                />

                <select
                  value={req.importance}
                  onChange={(e) => handleRequirementChange(index, 'importance', e.target.value)}
                  className="w-32 px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="required">Required (2x)</option>
                  <option value="preferred">Preferred (1x)</option>
                </select>

                <button
                  type="button"
                  onClick={() => handleRemoveRequirement(index)}
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
                  title="Remove skill"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-2">
          <Link
            to="/jobs"
            className="px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-sm disabled:opacity-60 transition-colors"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin h-4 w-4" />
                Saving Opening...
              </>
            ) : (
              'Save & Open Pipeline'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
