import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { mockAPI } from '../lib/mockAPI';
import { SwipeCard } from '../components/SwipeCard';
import { motion, AnimatePresence } from 'motion/react';
import { Sparkles, CheckCircle, XCircle, SkipForward } from 'lucide-react';
import { toast } from 'sonner';

export function ApproveLeads() {
  const { leads, updateLeadStatus, setLeads } = useStore();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [exitX, setExitX] = useState(0);
  const [exitY, setExitY] = useState(0);
  const [sessionApproved, setSessionApproved] = useState(0);
  const [sessionRejected, setSessionRejected] = useState(0);

  useEffect(() => {
    if (leads.length === 0) {
      mockAPI.getLeads().then(setLeads);
    }
  }, [leads.length, setLeads]);

  const pendingLeads = leads.filter(lead => lead.status === 'pending');
  const currentLead = pendingLeads[currentIndex];

  const handleSwipe = async (direction: 'left' | 'right' | 'up') => {
    if (!currentLead) return;

    if (direction === 'left') {
      setExitX(-1000);
      setExitY(0);
      updateLeadStatus(currentLead.id, 'rejected');
      setSessionRejected(prev => prev + 1);
      toast.error(`${currentLead.company_name} rejected`, { icon: <XCircle className="w-5 h-5" /> });
    } else if (direction === 'right') {
      setExitX(1000);
      setExitY(0);
      updateLeadStatus(currentLead.id, 'approved');
      setSessionApproved(prev => prev + 1);
      toast.success(`${currentLead.company_name} approved!`, { icon: <CheckCircle className="w-5 h-5" /> });
    } else if (direction === 'up') {
      setExitX(0);
      setExitY(-1000);
      updateLeadStatus(currentLead.id, 'skipped');
      toast.info(`${currentLead.company_name} skipped`, { icon: <SkipForward className="w-5 h-5" /> });
    }

    await mockAPI.updateLeadStatus(currentLead.id, direction === 'right' ? 'approved' : direction === 'left' ? 'rejected' : 'skipped');

    setTimeout(() => {
      setCurrentIndex((prev) => prev + 1);
      setExitX(0);
      setExitY(0);
    }, 300);
  };

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'a') handleSwipe('right');
      if (e.key.toLowerCase() === 'r') handleSwipe('left');
      if (e.key.toLowerCase() === 's') handleSwipe('up');
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentLead]);

  if (pendingLeads.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', duration: 0.6 }}
            className="w-24 h-24 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto mb-6"
          >
            <CheckCircle className="w-12 h-12 text-white" />
          </motion.div>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">All Caught Up!</h2>
          <p className="text-slate-600">No more leads to review. Check back later for new matches.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-blue-50 p-4 lg:p-8 overflow-hidden">
      {/* Header */}
      <div className="mb-8 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold text-slate-900 mb-2 flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-blue-600" />
            Approve Leads
          </h1>
          <div className="flex gap-4 text-sm font-medium">
            <span className="text-slate-600">{pendingLeads.length} remaining</span>
            <span className="text-green-600">✓ {sessionApproved} Approved</span>
            <span className="text-red-600">✗ {sessionRejected} Rejected</span>
          </div>
        </div>

        {/* Progress */}
        <div className="bg-white rounded-2xl shadow-lg px-6 py-4 border border-slate-200">
          <div className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-2">Session Progress</div>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden w-full lg:w-48">
              <motion.div
                className="h-full bg-gradient-to-r from-blue-500 to-cyan-500"
                initial={{ width: 0 }}
                animate={{
                  width: `${((leads.filter(l => l.status !== 'pending').length) / leads.length) * 100}%`
                }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <span className="text-sm font-semibold text-slate-900">
              {leads.filter(l => l.status !== 'pending').length}/{leads.length}
            </span>
          </div>
        </div>
      </div>

      {/* Card Stack */}
      <div className="flex-1 relative max-w-4xl mx-auto w-full">

        <AnimatePresence>
          {/* Show next 3 cards in stack */}
          {pendingLeads.slice(currentIndex, currentIndex + 3).map((lead, index) => {
            const isTop = index === 0;

            return (
              <motion.div
                key={lead.id}
                initial={isTop ? { scale: 1, y: 0 } : { scale: 0.95 - (index * 0.05), y: index * 20 }}
                animate={{
                  scale: 1 - (index * 0.05),
                  y: index * 20,
                  opacity: 1 - (index * 0.2)
                }}
                exit={{
                  x: exitX,
                  y: exitY,
                  opacity: 0,
                  rotate: exitX !== 0 ? (exitX > 0 ? 30 : -30) : 0,
                  transition: { duration: 0.3 }
                }}
                style={{
                  zIndex: 3 - index,
                  pointerEvents: isTop ? 'auto' : 'none',
                }}
                className="absolute inset-0"
              >
                {isTop && (
                  <SwipeCard
                    lead={lead}
                    onSwipe={handleSwipe}
                  />
                )}
                {!isTop && (
                  <div className="w-full h-full bg-white rounded-3xl shadow-xl border border-slate-200" />
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>

        {/* Instructions overlay for first time */}
        {currentIndex === 0 && (
          <motion.div
            initial={{ opacity: 1 }}
            animate={{ opacity: 0 }}
            transition={{ delay: 3, duration: 1 }}
            className="absolute inset-0 pointer-events-none flex items-center justify-center"
          >
            <div className="bg-slate-900/80 backdrop-blur-sm text-white px-6 py-4 rounded-2xl shadow-2xl">
              <p className="text-center font-medium">
                Swipe right to approve • Swipe left to reject • Swipe up to skip
              </p>
            </div>
          </motion.div>
        )}
      </div>

      {/* Action Stats */}
      <div className="mt-8 flex items-center justify-center gap-8">
        <div className="text-center">
          <div className="text-3xl font-bold text-red-600">
            {leads.filter(l => l.status === 'rejected').length}
          </div>
          <div className="text-sm text-slate-600">Rejected</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-blue-600">
            {leads.filter(l => l.status === 'skipped').length}
          </div>
          <div className="text-sm text-slate-600">Skipped</div>
        </div>
        <div className="text-center">
          <div className="text-3xl font-bold text-green-600">
            {leads.filter(l => l.status === 'approved').length}
          </div>
          <div className="text-sm text-slate-600">Approved</div>
        </div>
      </div>
    </div>
  );
}
