import { createPortal } from 'react-dom';
import { motion } from 'framer-motion';
import { BrainCircuit } from 'lucide-react';

// Render above every page so long-running analysis cannot be hidden by page layout.
export function AnalysisLoadingOverlay({
  message,
  onStop
}: {
  message: string;
  onStop?: () => void;
}) {
  return createPortal(
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[120] flex items-center justify-center bg-deepnavy/75 backdrop-blur-xl"
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <div className="flex flex-col items-center">
        <div className="relative flex items-center justify-center w-40 h-40">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2.8, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 border-2 border-transparent rounded-full border-r-electric border-t-tealbrand"
          />
          <motion.div
            animate={{ rotate: -360 }}
            transition={{ duration: 4.2, repeat: Infinity, ease: 'linear' }}
            className="absolute border-2 border-transparent rounded-full inset-3 border-b-magentabrand border-l-purplebrand"
          />
          <motion.div
            animate={{ scale: [0.96, 1.04, 0.96] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
            className="flex h-24 w-24 items-center justify-center rounded-full bg-white shadow-[0_0_55px_rgba(6,182,212,0.35)] ring-1 ring-white/80"
          >
            <BrainCircuit className="h-11 w-11 text-electric" />
          </motion.div>
        </div>

        <p className="mt-5 text-base font-black tracking-wide text-white">
          {message}
        </p>
        {onStop && (
          <button
            type="button"
            onClick={onStop}
            className="mt-4 rounded-xl border border-white/15 bg-white/10 px-5 py-2.5 text-sm font-black text-white transition hover:bg-white hover:text-deepnavy"
          >
            Stop analysis
          </button>
        )}
      </div>
    </motion.div>,
    document.body
  );
}
