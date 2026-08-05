'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  CreditCard, Zap, CheckCircle2, ShieldCheck, Download, ArrowUpRight, Sparkles, Clock, FileText, AlertCircle, Loader2,
} from 'lucide-react';
import { useSubscription, useBillingPlans, useCreditBalance, useInvoices, useCheckout } from '../queries';

export default function BillingPage() {
  const { data: subscription, isLoading: subLoading } = useSubscription();
  const { data: plans, isLoading: plansLoading } = useBillingPlans();
  const { data: credits } = useCreditBalance();
  const { data: invoices } = useInvoices();
  const checkoutMutation = useCheckout();

  const mockPlans = React.useMemo(() => {
    if (plans && plans.length > 0) return plans;
    return [
      { id: 'p1', name: 'Starter Plan', price_monthly: 49, included_credits: 5000, features: ['5 AI Agent Executions/mo', '1,000 CRM Contacts', 'Standard RAG Ingestion', 'Email Support'] },
      { id: 'p2', name: 'Pro Enterprise', price_monthly: 199, included_credits: 25000, features: ['Unlimited Agents & Workflows', '50,000 CRM Contacts', 'High-speed Vector RAG Engine', 'Priority API Gateway Access', 'Dedicated Account Manager'] },
      { id: 'p3', name: 'Scale Unlimited', price_monthly: 499, included_credits: 100000, features: ['Custom LLM Fine-Tuning', 'Unlimited Multi-tenant Orgs', 'SOC2 / HIPAA Compliance Suite', '24/7 SLA Support', 'Custom Integrations Connector'] },
    ];
  }, [plans]);

  const handleUpgrade = async (planId: string) => {
    try {
      const res = await checkoutMutation.mutateAsync(planId);
      if (res?.url) window.location.href = res.url;
    } catch (e) {
      console.error('Checkout error', e);
    }
  };

  const remainingPercent = credits
    ? Math.round((credits.remaining_credits / credits.total_credits) * 100)
    : 78;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Billing & Usage Credits</h1>
        <p className="text-sm text-zinc-500 mt-1">Manage subscription plan, AI credit quota, and enterprise invoices</p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Active Plan Card */}
        <div className="bg-gradient-to-br from-zinc-900 via-zinc-900 to-violet-950/40 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-violet-400">Current Subscription</span>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">ACTIVE</span>
          </div>
          <h2 className="text-2xl font-bold text-white">{subscription?.plan?.name || 'Pro Enterprise'}</h2>
          <p className="text-sm text-zinc-400 mt-1">$199 / month • Billed monthly</p>
          <div className="mt-6 pt-4 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-500">
            <span>Renews on Aug 28, 2026</span>
            <button className="text-violet-400 hover:text-violet-300 font-medium transition-colors">Manage Plan</button>
          </div>
        </div>

        {/* AI Token Credits Card */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5"><Sparkles className="w-4 h-4 text-amber-400" /> AI Usage Credits</span>
              <span className="text-xs text-amber-400 font-medium">{remainingPercent}% Remaining</span>
            </div>
            <div className="text-2xl font-bold text-white">
              {(credits?.remaining_credits ?? 19500).toLocaleString()} <span className="text-xs text-zinc-500 font-normal">/ {(credits?.total_credits ?? 25000).toLocaleString()} credits</span>
            </div>
            {/* Progress Bar */}
            <div className="w-full h-2.5 bg-zinc-800 rounded-full mt-4 overflow-hidden">
              <motion.div initial={{ width: 0 }} animate={{ width: `${remainingPercent}%` }} transition={{ duration: 1 }} className="h-full bg-gradient-to-r from-amber-500 to-violet-500 rounded-full" />
            </div>
          </div>
          <button className="mt-4 w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" /> Top Up AI Credits
          </button>
        </div>

        {/* Payment Method Card */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400 block mb-3">Payment Method</span>
            <div className="flex items-center gap-3">
              <div className="w-10 h-7 bg-zinc-800 border border-zinc-700 rounded flex items-center justify-center"><CreditCard className="w-5 h-5 text-white" /></div>
              <div>
                <p className="text-sm font-medium text-white">Visa ending in 4242</p>
                <p className="text-xs text-zinc-500">Expires 12/28</p>
              </div>
            </div>
          </div>
          <button className="mt-4 w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-medium transition-colors">
            Update Payment Method
          </button>
        </div>
      </div>

      {/* Subscription Plans Comparison */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white">Select a Plan</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {mockPlans.map((plan, i) => {
            const isCurrent = i === 1;
            return (
              <div key={plan.id} className={`bg-zinc-900/60 border rounded-2xl p-6 flex flex-col justify-between relative ${isCurrent ? 'border-violet-500 shadow-xl shadow-violet-500/10' : 'border-zinc-800'}`}>
                {isCurrent && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-violet-600 text-white text-[10px] font-bold uppercase tracking-wider rounded-full shadow">MOST POPULAR</span>
                )}
                <div>
                  <h3 className="text-lg font-bold text-white">{plan.name}</h3>
                  <div className="mt-3 flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold text-white">${plan.price_monthly}</span>
                    <span className="text-xs text-zinc-500">/ month</span>
                  </div>
                  <p className="text-xs text-amber-400 mt-2 font-medium">Includes {plan.included_credits.toLocaleString()} AI Credits</p>

                  <ul className="mt-6 space-y-2.5 border-t border-zinc-800 pt-6">
                    {plan.features.map((f, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-xs text-zinc-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>

                <button onClick={() => handleUpgrade(plan.id)} disabled={isCurrent || checkoutMutation.isPending}
                  className={`mt-8 w-full py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isCurrent ? 'bg-zinc-800 text-zinc-400 cursor-default' : 'bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-500/20'
                  }`}>
                  {isCurrent ? 'Current Plan' : 'Upgrade Plan'}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Invoices History Table */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white">Invoice History</h2>
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Invoice Number</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Amount</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Status</th>
                <th className="text-left px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Date</th>
                <th className="text-right px-5 py-3.5 text-xs font-medium text-zinc-500 uppercase tracking-wider">Receipt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {invoices && invoices.length > 0 ? (
                invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-5 py-4 text-sm font-medium text-white">{inv.number}</td>
                    <td className="px-5 py-4 text-sm text-zinc-300">${inv.amount.toFixed(2)}</td>
                    <td className="px-5 py-4"><span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400">{inv.status}</span></td>
                    <td className="px-5 py-4 text-sm text-zinc-400">{new Date(inv.created_at).toLocaleDateString()}</td>
                    <td className="px-5 py-4 text-right"><button className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 ml-auto"><Download className="w-3.5 h-3.5" /> PDF</button></td>
                  </tr>
                ))
              ) : (
                [
                  { id: '1', number: 'INV-2026-001', amount: 199.00, status: 'PAID', date: '2026-07-01' },
                  { id: '2', number: 'INV-2026-002', amount: 199.00, status: 'PAID', date: '2026-06-01' },
                ].map(inv => (
                  <tr key={inv.id} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-5 py-4 text-sm font-medium text-white">{inv.number}</td>
                    <td className="px-5 py-4 text-sm text-zinc-300">${inv.amount.toFixed(2)}</td>
                    <td className="px-5 py-4"><span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400">{inv.status}</span></td>
                    <td className="px-5 py-4 text-sm text-zinc-400">{inv.date}</td>
                    <td className="px-5 py-4 text-right"><button className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 ml-auto"><Download className="w-3.5 h-3.5" /> Download</button></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
