import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, AlertCircle, Loader2, Mail, Lock, Eye, EyeOff, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate('/jobs');
    } catch (err) {
      const msg = err.response?.data?.error?.message || 'Invalid email or password.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/80 dark:bg-slate-950 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans antialiased text-slate-800 dark:text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        {/* Brand Icon */}
        <div className="mx-auto h-12 w-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-200 dark:shadow-none mb-3">
          <Sparkles className="h-6 w-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Sign in to HireLens
        </h1>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          AI-powered explainable resume screening &amp; candidate ranking
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white dark:bg-slate-900 py-8 px-6 sm:px-10 shadow-xs border border-slate-200/80 dark:border-slate-800 rounded-2xl">
          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 flex items-start gap-2.5">
              <AlertCircle className="h-4 w-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
              <p className="text-xs text-rose-700 dark:text-rose-300 font-medium leading-relaxed">{error}</p>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
                Work Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="recruiter@company.com"
                  className="w-full pl-9 pr-3.5 py-2.5 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 text-xs transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-10 py-2.5 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 text-xs transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex justify-center items-center py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 shadow-xs hover:shadow disabled:opacity-60 transition-all cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="animate-spin h-4 w-4 mr-2" />
                    Authenticating...
                  </>
                ) : (
                  'Sign In to Dashboard'
                )}
              </button>
            </div>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 dark:border-slate-800 text-center text-xs">
            <span className="text-slate-500 dark:text-slate-400">Don&apos;t have an account? </span>
            <Link
              to="/register"
              className="font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 transition-colors"
            >
              Create recruiter account
            </Link>
          </div>
        </div>

        {/* Security badge footer */}
        <div className="mt-6 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          <span>Secured with Argon2id • Transparent AI Decision Support</span>
        </div>
      </div>
    </div>
  );
}
