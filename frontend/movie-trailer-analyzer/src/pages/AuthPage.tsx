import { FormEvent, useEffect, useState } from 'react';
import { AlertCircle, Film, Loader2, LockKeyhole, LogIn, Mail, UserPlus } from 'lucide-react';

import { useAuth } from '../auth/AuthContext';

type AuthMode = 'login' | 'register';

interface AuthPageProps {
  initialMode?: AuthMode;
  onAuthenticated: () => void;
  onModeChange: (mode: AuthMode) => void;
}

export default function AuthPage({
  initialMode = 'login',
  onAuthenticated,
  onModeChange
}: AuthPageProps) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isRegister = mode === 'register';

  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setError('');
    onModeChange(nextMode);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (isRegister) {
        await register(name, email, password);
      } else {
        await login(email, password);
      }

      onAuthenticated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-[98%] 2xl:max-w-[1920px] items-center gap-8 px-4 py-8 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-8 xl:px-10">
      <section className="space-y-6">
        <div className="inline-flex items-center gap-3 rounded-full bg-blue-50 px-4 py-2 text-sm font-black text-electric ring-1 ring-blue-100">
          <Film className="h-4 w-4" />
          Movie Trailer Analyzer
        </div>

        <div>
          <h1 className="max-w-3xl text-4xl font-black leading-tight text-deepnavy sm:text-5xl">
            Sign in to save trailer analysis under your account.
          </h1>
          <p className="mt-5 max-w-2xl text-base font-semibold leading-8 text-slatebrand/60">
            Your analysis history, trailer metrics, feature outputs and predictions are stored in the backend with your Firebase user id.
          </p>
        </div>
      </section>

      <section className="rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-slate-200/80 sm:p-8">
        <div className="mb-6 grid grid-cols-2 rounded-2xl bg-lightbrand p-1">
          <button
            type="button"
            onClick={() => switchMode('login')}
            className={`rounded-xl px-4 py-3 text-sm font-black transition ${
              !isRegister ? 'bg-deepnavy text-white shadow-lg' : 'text-slatebrand/65'
            }`}
          >
            Login
          </button>

          <button
            type="button"
            onClick={() => switchMode('register')}
            className={`rounded-xl px-4 py-3 text-sm font-black transition ${
              isRegister ? 'bg-deepnavy text-white shadow-lg' : 'text-slatebrand/65'
            }`}
          >
            Register
          </button>
        </div>

        <div>
          <p className="text-xs font-black uppercase tracking-widest text-electric">
            {isRegister ? 'Create account' : 'Welcome back'}
          </p>
          <h2 className="mt-2 text-3xl font-black text-deepnavy">
            {isRegister ? 'Register' : 'Login'}
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {isRegister && (
            <label className="block">
              <span className="text-sm font-black text-deepnavy">Name</span>
              <div className="mt-2 flex items-center gap-3 rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 focus-within:border-electric focus-within:ring-4 focus-within:ring-electric/10">
                <UserPlus className="h-5 w-5 text-slatebrand/40" />
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Your name"
                  className="w-full bg-transparent text-sm font-semibold text-deepnavy outline-none placeholder:text-slatebrand/35"
                />
              </div>
            </label>
          )}

          <label className="block">
            <span className="text-sm font-black text-deepnavy">Email</span>
            <div className="mt-2 flex items-center gap-3 rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 focus-within:border-electric focus-within:ring-4 focus-within:ring-electric/10">
              <Mail className="h-5 w-5 text-slatebrand/40" />
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                className="w-full bg-transparent text-sm font-semibold text-deepnavy outline-none placeholder:text-slatebrand/35"
              />
            </div>
          </label>

          <label className="block">
            <span className="text-sm font-black text-deepnavy">Password</span>
            <div className="mt-2 flex items-center gap-3 rounded-2xl border border-slate-200 bg-lightbrand px-4 py-3 focus-within:border-electric focus-within:ring-4 focus-within:ring-electric/10">
              <LockKeyhole className="h-5 w-5 text-slatebrand/40" />
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Minimum 6 characters"
                required
                minLength={6}
                className="w-full bg-transparent text-sm font-semibold text-deepnavy outline-none placeholder:text-slatebrand/35"
              />
            </div>
          </label>

          {error && (
            <div className="flex items-start gap-3 rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-100">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-electric px-5 py-4 text-sm font-black text-white shadow-lg shadow-blue-600/20 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <LogIn className="h-5 w-5" />}
            {isSubmitting ? 'Please wait...' : isRegister ? 'Create Account' : 'Login'}
          </button>
        </form>
      </section>
    </main>
  );
}
