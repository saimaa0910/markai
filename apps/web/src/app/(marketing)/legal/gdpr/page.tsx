'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, CheckCircle2, FileText, ArrowRight, UserCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

export default function GdprPage() {
  const [requestType, setRequestType] = React.useState('export');
  const [email, setEmail] = React.useState('');
  const [details, setDetails] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
    }, 1000);
  };

  const rights = [
    { title: 'Right to Access', desc: 'You can request a copy of all user data models, telemetry records, and prompt profiles stored in Viptant.' },
    { title: 'Right to Erasure', desc: 'You can request that we permanently delete your organization workspace, vectors databases, and API keys.' },
    { title: 'Right to Portability', desc: 'Export your database lead contexts, performance models, and custom prompts as standardized JSON files.' },
    { title: 'Right to Rectification', desc: 'Correct inaccurate profiling, change contacts details, and update campaign mappings instantly.' },
  ];

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-16 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>European Compliance</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              GDPR Compliance
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              We respect data privacy rights. Learn about your rights under GDPR and submit information requests directly.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Split Grid: GDPR Rights vs Interactive Request Form ─────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 text-left relative z-10">
        
        {/* Rights lists (col-span-6) */}
        <div className="lg:col-span-6 space-y-8">
          <FadeUp>
            <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-3">
              <UserCheck className="w-5 h-5 text-violet-400" /> Your Privacy Rights
            </h3>
            <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed mb-6">
              Under the General Data Protection Regulation (GDPR), European Union citizens can assert direct control over user telemetry logs and workspace database assets.
            </p>
          </FadeUp>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {rights.map((r, idx) => (
              <FadeUp 
                key={r.title} 
                delay={idx * 0.04}
                className="p-5 rounded-lg border border-white/5 bg-neutral-950/40"
              >
                <h4 className="text-xs font-bold text-white mb-1.5">{r.title}</h4>
                <p className="text-neutral-500 text-[11px] sm:text-xs leading-relaxed">{r.desc}</p>
              </FadeUp>
            ))}
          </div>
        </div>

        {/* Data Request Form (col-span-6) */}
        <div className="lg:col-span-6">
          <FadeUp className="p-6 sm:p-8 rounded-xl border border-white/10 bg-neutral-950/60 glass shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px] pointer-events-none" />
            
            <h3 className="text-lg font-bold text-white mb-1">GDPR Compliance Desk</h3>
            <p className="text-xs text-neutral-500 leading-relaxed mb-6">
              Complete this form to dispatch verification protocols and request data actions.
            </p>

            <AnimatePresence mode="wait">
              {!submitted ? (
                <motion.form 
                  key="form"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onSubmit={handleSubmit} 
                  className="space-y-4"
                >
                  {/* Action Selector */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Request Operation Type</label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setRequestType('export')}
                        className={`flex-1 py-2 rounded text-xs font-semibold cursor-pointer border ${
                          requestType === 'export' 
                            ? 'bg-violet-600 border-violet-500 text-white' 
                            : 'bg-neutral-900 border-white/5 text-neutral-400 hover:text-white'
                        }`}
                      >
                        Export My Data
                      </button>
                      <button
                        type="button"
                        onClick={() => setRequestType('delete')}
                        className={`flex-1 py-2 rounded text-xs font-semibold cursor-pointer border ${
                          requestType === 'delete' 
                            ? 'bg-rose-950/20 border-rose-500/30 text-rose-400' 
                            : 'bg-neutral-900 border-white/5 text-neutral-400 hover:text-white'
                        }`}
                      >
                        Delete My Account
                      </button>
                    </div>
                  </div>

                  {/* Email */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Email Address *</label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-violet-500 transition-colors font-mono"
                    />
                  </div>

                  {/* Details */}
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider block">Request Details & Verification Code</label>
                    <textarea
                      value={details}
                      onChange={(e) => setDetails(e.target.value)}
                      rows={3}
                      placeholder="Specify dates, workspaces IDs, or details supporting identity validation..."
                      className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-700 focus:outline-none focus:border-violet-500 transition-colors leading-relaxed"
                    />
                  </div>

                  <Button
                    type="submit"
                    variant={requestType === 'delete' ? 'outline' : 'violet'}
                    className={`w-full h-10 text-xs font-semibold mt-4 ${
                      requestType === 'delete' ? 'text-rose-400 hover:bg-rose-600/10 hover:text-rose-300 border-rose-500/20' : ''
                    }`}
                    isLoading={loading}
                  >
                    Submit Compliance Request <ArrowRight className="w-4 h-4 ml-1.5" />
                  </Button>
                </motion.form>
              ) : (
                <motion.div 
                  key="success"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="py-10 text-center space-y-4"
                >
                  <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Request Dispatched</h4>
                    <p className="text-[11px] text-neutral-400 mt-1.5 leading-relaxed max-w-xs mx-auto">
                      Your request has been logged. Our compliance officer will trigger identity verification links to <strong className="text-violet-300">{email}</strong> within 48 hours.
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}
