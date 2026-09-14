import { LogIn, LogOut, Menu, Sparkles, UserPlus } from 'lucide-react';


type ViewKey =
  | 'dashboard'
  | 'analyze'
  | 'emotion_analysis'
  | 'components'
  | 'history'
  | 'popularity'
  | 'sentiment'
  | 'recommendations'
  | 'login'
  | 'register';

interface HeaderProps {
  activeView: ViewKey;
  onNavigate: (view: ViewKey) => void;
  isAuthenticated: boolean;
  userLabel?: string;
  onLogout: () => void;
}

const navItems: Array<{ key: ViewKey; label: string; requiresAuth?: boolean }> = [
  { key: 'dashboard', label: 'Dashboard' },
<<<<<<< HEAD
  { key: 'emotion_analysis', label: 'Emotion' },
  { key: 'popularity', label: 'Popularity' },
  { key: 'sentiment', label: 'Sentiment' },
  { key: 'recommendations', label: 'Recommend' },
  { key: 'history', label: 'History' }
=======
  // { key: 'analyze', label: 'Analyze' },
  { key: 'emotion_analysis', label: 'Emotion Analysis' },
  // { key: 'components', label: 'Components' },
  { key: 'history', label: 'History' },
  { key: 'popularity', label: 'Popularity Analysis' }
>>>>>>> 0a27a033026d81eecd876c34fc200f4a0abdcb9b
];

export default function Header({
  activeView,
  onNavigate,
  isAuthenticated,
  userLabel,
  onLogout
}: HeaderProps) {
  const visibleNavItems = navItems.filter((item) => isAuthenticated || item.key === 'dashboard');

  return (
    <header className="sticky top-0 z-40 border-b backdrop-blur-2xl border-slate-200/70 bg-white/85">
      <div className="flex items-center justify-between gap-4 px-4 py-3 mx-auto w-full max-w-[98%] 2xl:max-w-[1920px] sm:px-6 lg:px-8 xl:px-10">
        <button
          onClick={() => onNavigate('dashboard')}
          className="flex items-center gap-3 text-left"
          aria-label="Go to dashboard"
        >
          <img
            src="/logo-mark.png"
            alt="AI-Powered Movie Trailer Analyzer logo"
            className="object-cover h-12 w-14 rounded-2xl ring-1 ring-slate-200"
          />
          <div className="hidden sm:block">
            <p className="text-sm font-black uppercase tracking-[0.24em] text-deepnavy">
              AI-Powered
            </p>
            <p className="text-xs font-semibold text-electric">
              Movie Trailer Analyzer
            </p>
          </div>
        </button>

        <nav className="items-center hidden p-1 rounded-full bg-lightbrand md:flex">
          {visibleNavItems.map((item) => (
            <button
              key={item.key}
              onClick={() => onNavigate(item.key)}
              className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                activeView === item.key
                  ? 'bg-deepnavy text-white shadow-lg'
                  : 'text-slatebrand/70 hover:text-deepnavy'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              <div className="items-center hidden gap-2 px-4 py-2 text-sm font-bold border rounded-full max-w-52 border-electric/20 bg-electric/10 text-electric lg:flex">
                <Sparkles className="w-4 h-4 shrink-0" />
                <span className="truncate">{userLabel || 'Signed in'}</span>
              </div>

              <button
                onClick={onLogout}
                className="items-center hidden gap-2 px-4 py-3 text-sm font-black text-white rounded-2xl bg-deepnavy md:inline-flex"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </>
          ) : (
            <div className="items-center hidden gap-2 md:flex">
              <button
                onClick={() => onNavigate('login')}
                className="inline-flex items-center gap-2 px-4 py-3 text-sm font-black rounded-2xl bg-lightbrand text-deepnavy ring-1 ring-slate-200"
              >
                <LogIn className="w-4 h-4" />
                Login
              </button>

              <button
                onClick={() => onNavigate('register')}
                className="inline-flex items-center gap-2 px-4 py-3 text-sm font-black text-white rounded-2xl bg-electric"
              >
                <UserPlus className="w-4 h-4" />
                Register
              </button>
            </div>
          )}

          <button
            className="p-3 rounded-2xl bg-lightbrand text-deepnavy md:hidden"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </div>

      <nav className="flex gap-2 px-4 pb-3 overflow-x-auto md:hidden">
        {visibleNavItems.map((item) => (
          <button
            key={item.key}
            onClick={() => onNavigate(item.key)}
            className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-bold ${
              activeView === item.key
                ? 'bg-deepnavy text-white'
                : 'bg-lightbrand text-slatebrand/70'
            }`}
          >
            {item.label}
          </button>
        ))}

        {isAuthenticated ? (
          <button
            onClick={onLogout}
            className="px-4 py-2 text-sm font-bold text-white rounded-full whitespace-nowrap bg-deepnavy"
          >
            Logout
          </button>
        ) : (
          <>
            <button
              onClick={() => onNavigate('login')}
              className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-bold ${
                activeView === 'login' ? 'bg-deepnavy text-white' : 'bg-lightbrand text-slatebrand/70'
              }`}
            >
              Login
            </button>

            <button
              onClick={() => onNavigate('register')}
              className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-bold ${
                activeView === 'register' ? 'bg-deepnavy text-white' : 'bg-lightbrand text-slatebrand/70'
              }`}
            >
              Register
            </button>
          </>
        )}
      </nav>
    </header>
  );
}
