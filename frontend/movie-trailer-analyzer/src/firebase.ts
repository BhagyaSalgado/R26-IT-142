import { initializeApp } from 'firebase/app';
import { getAnalytics, isSupported } from 'firebase/analytics';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyCBxg_qHZJmhf9urzbCZWze1GfoJcaXdR8',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'movie-trailer-analyzer.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'movie-trailer-analyzer',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'movie-trailer-analyzer.firebasestorage.app',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '715993570222',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:715993570222:web:ab3ee531b7682d909f063f',
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || 'G-QNCMPR4EGP'
};

export const firebaseApp = initializeApp(firebaseConfig);
export const auth = getAuth(firebaseApp);

if (typeof window !== 'undefined') {
  isSupported()
    .then((supported) => {
      if (supported) {
        getAnalytics(firebaseApp);
      }
    })
    .catch(() => {
      // Analytics is optional and can be unavailable in local browsers.
    });
}
