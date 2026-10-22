import { Button } from '@/components/ui/button';

/**
 * Root App component.
 * Placeholder for Phase 0 — replaced with routing and layout in Phase 4.
 */
function App() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
      <div className="text-center space-y-4 p-8">
        <h1 className="text-4xl font-semibold text-slate-900 dark:text-slate-50">
          HireLens
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-lg">
          AI Resume Screening &amp; Candidate Ranking
        </p>
        <Button variant="default" size="lg">
          Get Started
        </Button>
        <p className="text-xs text-slate-400">Phase 0 scaffold — backend and frontend running ✓</p>
      </div>
    </div>
  );
}

export default App;
