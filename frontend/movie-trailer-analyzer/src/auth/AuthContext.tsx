import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from 'react';
import {
  User,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
  updateProfile
} from 'firebase/auth';

import { auth } from '../firebase';
import { setAuthTokenProvider as setPopularityAuthTokenProvider } from '../services/popularityService';
import { setAuthTokenProvider as setVideoEmotionAuthTokenProvider } from '../services/videoEmotionApi';
import { setAuthTokenProvider as setCommentSentimentAuthTokenProvider } from '../services/commentSentimentService';
import { setAuthTokenProvider as setRecommendationAuthTokenProvider } from '../services/recommendationApi';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const getIdToken = useCallback(async () => {
    return auth.currentUser ? auth.currentUser.getIdToken(true) : null;
  }, []);

  useEffect(() => {
    setPopularityAuthTokenProvider(getIdToken);
    setVideoEmotionAuthTokenProvider(getIdToken);
    setCommentSentimentAuthTokenProvider(getIdToken);
    setRecommendationAuthTokenProvider(getIdToken);
  }, [getIdToken]);

  const login = useCallback(async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password);
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    const credential = await createUserWithEmailAndPassword(auth, email, password);

    if (name.trim()) {
      await updateProfile(credential.user, { displayName: name.trim() });
    }
  }, []);

  const logout = useCallback(async () => {
    await signOut(auth);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, getIdToken }),
    [getIdToken, loading, login, logout, register, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider.');
  }

  return context;
}
