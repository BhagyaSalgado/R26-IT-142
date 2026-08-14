import { Menu, Sparkles } from 'lucide-react';

type ViewKey = 'dashboard' | 'analyze' | 'components' | 'history';

interface HeaderProps {
  activeView: ViewKey;
  onNavigate: (view: ViewKey) => void;
}

const navItems: Array<{ key: ViewKey; label: string }> = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'analyze', label: 'Analyze' },
  { key: 'history', label: 'History' }
];

export default function Header({ activeView, onNavigate }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b backdrop-blur-2xl border-slate-200/70 bg-white/85">
      <div className="flex gap-4 justify-between items-center px-4 py-3 mx-auto max-w-7xl sm:px-6 lg:px-8">
        <button onClick={() => onNavigate('dashboard')} className="flex gap-3 items-center text-left" aria-label="Go to dashboard">
          <img src="/logo-mark.png" alt="AI-Powered Movie Trailer Analyzer logo" className="object-cover w-14 h-12 rounded-2xl ring-1 ring-slate-200" />
          <div className="hidden sm:block">
            <p className="text-sm font-black uppercase tracking-[0.24em] text-deepnavy">AI-Powered</p>
            <p className="text-xs font-semibold text-electric">Movie Trailer Analyzer</p>
          </div>
        </button>

        <nav className="hidden items-center p-1 rounded-full bg-lightbrand md:flex">
          {navItems.map((item) => (
            <button
              key={item.key}
              onClick={() => onNavigate(item.key)}
              className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                activeView === item.key ? 'bg-deepnavy text-white shadow-lg' : 'text-slatebrand/70 hover:text-deepnavy'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-electric/20 bg-electric/10 px-4 py-2 text-sm font-bold text-electric lg:flex">
            <Sparkles className="h-4 w-4" />
            AI Powered Insights
          </div>
          <button className="rounded-2xl bg-lightbrand p-3 text-deepnavy md:hidden" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>
      <nav className="flex overflow-x-auto gap-2 px-4 pb-3 md:hidden">
        {navItems.map((item) => (
          <button
            key={item.key}
            onClick={() => onNavigate(item.key)}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-bold ${
              activeView === item.key ? 'bg-deepnavy text-white' : 'bg-lightbrand text-slatebrand/70'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}
