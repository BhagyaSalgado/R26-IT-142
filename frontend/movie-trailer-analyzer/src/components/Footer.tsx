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

interface FooterProps {
  onNavigate: (view: ViewKey) => void;
}

const productLinks: Array<{ key: ViewKey; label: string }> = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'emotion_analysis', label: 'Emotion Analysis' },
  { key: 'popularity', label: 'Popularity Analysis' },
  { key: 'sentiment', label: 'Comment Sentiment' },
  { key: 'recommendations', label: 'Recommendations' },
  { key: 'history', label: 'Analysis History' }
];

export default function Footer({ onNavigate }: FooterProps) {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-16 border-t border-white/10 bg-deepnavy text-white">
      <div className="w-full px-4 py-12 mx-auto max-w-[98%] 2xl:max-w-[1920px] sm:px-6 lg:px-8 xl:px-10">
        <div className="flex flex-col justify-between gap-10 lg:flex-row">
          <div>
            <button onClick={() => onNavigate('dashboard')} className="flex items-center gap-3 text-left">
              <img
                src="/logo-mark.png"
                alt="AI-Powered Movie Trailer Analyzer logo"
                className="object-cover w-12 h-12 rounded-2xl ring-1 ring-white/15"
              />
              <div>
                <p className="text-sm font-black uppercase tracking-[0.24em]">AI-Powered</p>
                <p className="text-xs font-semibold text-tealbrand">Movie Trailer Analyzer</p>
              </div>
            </button>
            <p className="max-w-sm mt-4 text-sm leading-6 text-white/55">
              Audio, visual and audience intelligence for trailers, in one dashboard.
            </p>
          </div>

          <div>
            <p className="text-xs font-black uppercase tracking-[0.2em] text-white/40">Product</p>
            <ul className="grid grid-cols-2 mt-4 gap-x-8 gap-y-2.5 sm:grid-cols-3">
              {productLinks.map((link) => (
                <li key={link.key}>
                  <button
                    onClick={() => onNavigate(link.key)}
                    className="text-sm font-semibold text-white/70 transition hover:text-tealbrand"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between gap-3 pt-8 mt-10 text-xs font-semibold border-t border-white/10 text-white/45 sm:flex-row">
          <p>&copy; {year} AI-Powered Movie Trailer Analyzer. All rights reserved.</p>
          <p>Predictions are model-generated estimates, not guarantees.</p>
        </div>
      </div>
    </footer>
  );
}
