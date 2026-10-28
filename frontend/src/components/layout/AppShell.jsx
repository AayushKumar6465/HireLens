import { useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Briefcase,
  LayoutDashboard,
  Settings,
  LogOut,
  Menu,
  X,
  Sparkles,
  PlusCircle,
  ShieldCheck,
  ChevronRight,
  Sun,
  Moon,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';

export default function AppShell() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { label: 'Job Openings', href: '/jobs', icon: Briefcase },
    { label: 'Scoring & Weights', href: '/settings', icon: Settings },
  ];

  // Derive initials for avatar
  const getInitials = (name) => {
    if (!name) return 'RC';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    return parts[0].slice(0, 2).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-slate-50/75 dark:bg-slate-950 flex flex-col md:flex-row font-sans antialiased text-slate-800 dark:text-slate-100">
      {/* Mobile Top Header */}
      <header className="md:hidden sticky top-0 z-50 flex items-center justify-between px-4 py-3 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-sm">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-slate-900 dark:text-white block">
              HireLens
            </span>
            <span className="text-[10px] text-slate-400 block -mt-0.5 font-medium tracking-wide uppercase">
              Recruiter Hub
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={toggleTheme}
            className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-slate-600" />}
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Navigation Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800 flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        } md:static md:h-screen md:sticky md:top-0`}
      >
        {/* Brand Header */}
        <div className="p-5 flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-sm shadow-indigo-200 dark:shadow-none">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-slate-900 dark:text-white block">
                HireLens
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold text-indigo-600 dark:text-indigo-400 block">
                Explainable Screening
              </span>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle color mode"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-slate-500" />}
          </button>
        </div>

        {/* Quick Action Button */}
        <div className="px-4 pt-4 pb-2">
          <NavLink
            to="/jobs/new"
            onClick={() => setMobileMenuOpen(false)}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs hover:shadow transition-all"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Create Opening</span>
          </NavLink>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
          <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Workspace
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === '/dashboard'
                ? location.pathname === '/dashboard'
                : location.pathname.startsWith(item.href);
            return (
              <NavLink
                key={item.href}
                to={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`group flex items-center justify-between px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-50/80 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-800/80 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`h-4 w-4 transition-colors ${
                      isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>
                {isActive && <ChevronRight className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />}
              </NavLink>
            );
          })}
        </nav>

        {/* System Trust Indicator */}
        <div className="px-4 py-3 mx-3 my-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-500 shrink-0" />
          <span className="truncate">Decision Support • No Auto-Rejection</span>
        </div>

        {/* User Card & Sign out */}
        <div className="p-3 border-t border-slate-200/80 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <div className="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-slate-800/80 border border-slate-200/60 dark:border-slate-700/60">
            <div className="flex items-center gap-2.5 min-w-0 pr-2">
              <div className="h-8 w-8 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold text-xs flex items-center justify-center shrink-0 border border-indigo-200 dark:border-indigo-800">
                {getInitials(user?.full_name)}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                  {user?.full_name || 'Recruiter'}
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  {user?.email || 'Authenticated'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-md transition-colors shrink-0"
              aria-label="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
