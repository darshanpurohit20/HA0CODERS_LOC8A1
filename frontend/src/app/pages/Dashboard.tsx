import { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { mockAPI } from '../lib/mockAPI';
import { TrendingUp, Users, Calendar, Target, Mail, Linkedin, Phone, MessageCircle, Play } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { KPICard } from '../components/KPICard';

export function Dashboard() {
  const { stats, leads, meetings, conversations, setLeads } = useStore();
  const [demoMode, setDemoMode] = useState(false);
  const [recentActivity, setRecentActivity] = useState([
    { action: 'New lead approved', company: 'Global Manufacturing Co.', time: '5 min ago' },
    { action: 'Meeting scheduled', company: 'Prime Technology Co.', time: '12 min ago' },
    { action: 'AI sent outreach', company: 'Elite Agriculture Co.', time: '28 min ago' },
    { action: 'Response received', company: 'Apex Textiles Co.', time: '1 hour ago' },
  ]);

  useEffect(() => {
    mockAPI.getLeads().then(setLeads);
  }, [setLeads]);

  // Demo Mode Simulation
  useEffect(() => {
    if (!demoMode) return;
    const interval = setInterval(() => {
      const actions = ['AI sent outreach', 'Meeting scheduled', 'Response received', 'New lead approved', 'Priority shift detected'];
      const companies = ['TechCorp Industries', 'GlobalManufacturing Ltd', 'EuroTech Co.', 'AsiaTrade Group', 'Summit Global'];

      const newActivity = {
        action: actions[Math.floor(Math.random() * actions.length)],
        company: companies[Math.floor(Math.random() * companies.length)],
        time: 'Just now'
      };

      setRecentActivity(prev => [newActivity, ...prev].slice(0, 5));
    }, 4000);
    return () => clearInterval(interval);
  }, [demoMode]);

  const channelData = [
    { name: 'Email', value: 45, color: '#3b82f6' },
    { name: 'LinkedIn', value: 30, color: '#0a66c2' },
    { name: 'WhatsApp', value: 15, color: '#25d366' },
    { name: 'Calls', value: 10, color: '#8b5cf6' },
  ];

  const pipelineData = [
    { stage: 'Approval', count: leads.filter(l => l.status === 'pending').length },
    { stage: 'Outreach', count: leads.filter(l => l.status === 'approved').length },
    { stage: 'Meetings', count: meetings.filter(m => m.status === 'scheduled').length },
    { stage: 'Converted', count: meetings.filter(m => m.status === 'completed').length },
  ];

  const heatmapData = [
    { country: 'Germany', score: 95, flag: '🇩🇪' },
    { country: 'USA', score: 88, flag: '🇺🇸' },
    { country: 'UAE', score: 82, flag: '🇦🇪' },
    { country: 'Singapore', score: 78, flag: '🇸🇬' },
    { country: 'UK', score: 75, flag: '🇬🇧' },
    { country: 'Japan', score: 70, flag: '🇯🇵' },
  ];

  return (
    <div className="p-4 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold text-slate-900 mb-2">Dashboard</h1>
          <p className="text-slate-600 text-sm lg:text-base">Welcome back! Here's your trade intelligence overview.</p>
        </div>
        <button
          onClick={() => setDemoMode(!demoMode)}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${demoMode
              ? 'bg-green-100 text-green-700 shadow-inner'
              : 'bg-blue-600 text-white shadow-lg hover:bg-blue-700'
            }`}
        >
          <Play className={`w-4 h-4 ${demoMode ? 'fill-green-700' : 'fill-white'}`} />
          {demoMode ? 'Live Simulation Active' : 'Start Simulation'}
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          icon={Users}
          value={stats.activeLeads}
          label="Active Leads"
          trend="+12%"
          iconColor="bg-blue-100 text-blue-600"
          delay={0.1}
        />
        <KPICard
          icon={TrendingUp}
          value={`${stats.responseRate.toFixed(1)}%`}
          label="Response Rate"
          trend="+8%"
          iconColor="bg-purple-100 text-purple-600"
          delay={0.2}
        />
        <KPICard
          icon={Calendar}
          value={stats.meetingsScheduled}
          label="Meetings Scheduled"
          trend="+15%"
          iconColor="bg-green-100 text-green-600"
          delay={0.3}
        />
        <KPICard
          icon={Target}
          value={`${stats.conversionRate.toFixed(1)}%`}
          label="Conversion Rate"
          trend="+5%"
          iconColor="bg-orange-100 text-orange-600"
          delay={0.4}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200"
        >
          <h2 className="text-xl font-bold text-slate-900 mb-6">Pipeline Overview</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={pipelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="stage" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Global Buyer Intent Heatmap */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200"
        >
          <h2 className="text-xl font-bold text-slate-900 mb-6">Global Buyer Intent</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {heatmapData.map((item, idx) => (
              <div
                key={item.country}
                className="p-4 rounded-xl border border-slate-100 flex flex-col items-center justify-center text-center transition-transform hover:scale-105"
                style={{ backgroundColor: `rgba(59, 130, 246, ${0.05 + (0.15 * (heatmapData.length - idx) / heatmapData.length)})` }}
              >
                <span className="text-2xl mb-1">{item.flag}</span>
                <span className="text-sm font-bold text-slate-900">{item.country}</span>
                <span className="text-xs font-semibold text-blue-600">{item.score} Score</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="lg:col-span-2 bg-white rounded-2xl shadow-lg p-6 border border-slate-200 overflow-hidden"
        >
          <h2 className="text-xl font-bold text-slate-900 mb-6">Intelligence Feed</h2>
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {recentActivity.map((activity, index) => (
                <motion.div
                  key={activity.company + activity.time + index}
                  layout
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex items-center gap-4 p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  <div className={`w-2 h-2 rounded-full ${index === 0 && demoMode ? 'bg-green-500 animate-pulse' : 'bg-blue-500'}`} />
                  <div className="flex-1">
                    <div className="font-semibold text-slate-900">{activity.action}</div>
                    <div className="text-sm text-slate-600">{activity.company}</div>
                  </div>
                  <div className="text-sm text-slate-500 font-medium">{activity.time}</div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Channel Performance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200"
        >
          <h2 className="text-xl font-bold text-slate-900 mb-6">Channels</h2>
          <div className="flex flex-col items-center">
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie
                  data={channelData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {channelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="w-full mt-4 space-y-2">
              {channelData.map((channel) => (
                <div key={channel.name} className="flex items-center gap-3">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: channel.color }} />
                  <span className="text-xs text-slate-600 flex-1">{channel.name}</span>
                  <span className="text-xs font-bold text-slate-900">{channel.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}