import { useStore } from '../store/useStore';
import { motion } from 'motion/react';
import { Search, Mail, Phone, ExternalLink, Shield, TrendingUp } from 'lucide-react';
import { useState } from 'react';

export function ApprovedLeads() {
  const { approvedLeads } = useStore();
  const [searchQuery, setSearchQuery] = useState('');

  const filteredLeads = approvedLeads.filter(lead =>
    lead.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.industry.toLowerCase().includes(searchQuery.toLowerCase()) ||
    lead.location.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Approved Leads</h1>
          <p className="text-slate-600">{approvedLeads.length} leads approved and ready for outreach</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Search by company, industry, or location..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-4 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Leads Grid */}
      {filteredLeads.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-slate-400 text-lg">No approved leads yet. Start reviewing leads!</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredLeads.map((lead, index) => (
            <motion.div
              key={lead.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white rounded-2xl shadow-lg p-6 border border-slate-200 hover:shadow-xl transition-all hover:-translate-y-1"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-xl font-bold text-slate-900">{lead.company_name}</h3>
                    {lead.trust_verified && (
                      <Shield className="w-5 h-5 text-green-500 fill-green-100" />
                    )}
                  </div>
                  <p className="text-slate-600">{lead.industry} • {lead.location}</p>
                </div>
                <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-4 py-2 rounded-xl">
                  <div className="text-2xl font-bold">{lead.match_percentage}%</div>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <div className="text-xs text-slate-600 mb-1">Vector</div>
                  <div className="text-lg font-bold text-blue-600">
                    {(lead.vector_score * 100).toFixed(0)}
                  </div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg text-center">
                  <div className="text-xs text-slate-600 mb-1">Intent</div>
                  <div className="text-lg font-bold text-purple-600">
                    {(lead.intent_score * 100).toFixed(0)}
                  </div>
                </div>
                <div className="bg-orange-50 p-3 rounded-lg text-center">
                  <div className="text-xs text-slate-600 mb-1">Momentum</div>
                  <div className="text-lg font-bold text-orange-600">
                    {(lead.trade_momentum_index * 100).toFixed(0)}
                  </div>
                </div>
              </div>

              {/* Details */}
              <div className="space-y-2 mb-4 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-600">Company Size:</span>
                  <span className="font-semibold text-slate-900">{lead.company_size}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-600">Est. Value:</span>
                  <span className="font-semibold text-slate-900">{lead.estimated_value}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-600">Contact:</span>
                  <span className="font-semibold text-slate-900">{lead.contact_person}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t border-slate-200">
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  <Mail className="w-4 h-4" />
                  Email
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 text-slate-900 rounded-lg hover:bg-slate-200 transition-colors">
                  <Phone className="w-4 h-4" />
                  Call
                </button>
                <button className="px-4 py-2 bg-slate-100 text-slate-900 rounded-lg hover:bg-slate-200 transition-colors">
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
