'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mail, MessageSquare, Phone, Building, CheckCircle2, 
  MapPin, Clock, ArrowRight, ShieldAlert, Sparkles, Send, Check 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';

interface Office {
  city: string;
  address: string;
  hours: string;
  phone: string;
  coordinates: string;
}

const OFFICES: Office[] = [
  { city: 'San Francisco', address: '100 Pine Street, Floor 14, San Francisco, CA 94111', hours: '9 AM - 6 PM PST', phone: '+1 (415) 555-0142', coordinates: '37.7923° N, 122.4001° W' },
  { city: 'New York', address: '250 Park Avenue, Suite 10, New York, NY 10177', hours: '9 AM - 6 PM EST', phone: '+1 (212) 555-0198', coordinates: '40.7562° N, 73.9749° W' },
  { city: 'London', address: '30 St Mary Axe (The Gherkin), London EC3A 8BF', hours: '9 AM - 6 PM GMT', phone: '+44 20 7555 0165', coordinates: '51.5144° N, 0.0803° W' },
];

const FAQS = [
  { q: 'How quickly does Support respond?', a: 'For technical inquiries, Standard plans receive responses within 24 hours. Enterprise plans include a guaranteed < 1 hour response SLA with dedicated Slack channels.' },
  { q: 'Can I request a custom Proof of Concept (POC)?', a: 'Yes. For teams with over 100 seats, our sales architects can design a 14-day dedicated trial environment, pre-connected to sandbox datasets.' },
  { q: 'Where is my data hosted?', a: 'By default, Viptant hosts data in highly secure AWS/GCP regions in the United States (US-East). Enterprise tenants can request dedicated hosting in the EU (Frankfurt) or APAC.' },
  { q: 'Do you offer custom SLA agreements?', a: 'Yes, our enterprise contracts support custom availability clauses, liability terms, and dedicated VPC configurations.' },
];

export default function ContactPage() {
  const [formSubmitted, setFormSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [formData, setFormData] = React.useState({
    name: '',
    email: '',
    company: '',
    size: '1-10',
    help: 'sales',
    message: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name && formData.email && formData.message) {
      setLoading(true);
      setTimeout(() => {
        setLoading(false);
        setFormSubmitted(true);
        setFormData({
          name: '',
          email: '',
          company: '',
          size: '1-10',
          help: 'sales',
          message: '',
        });
      }, 1200);
    }
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-12 overflow-hidden bg-grid-dots border-b border-white/5">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>Contact Us</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-3 mb-4">
              Let's Start a Conversation
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Have questions about billing, integrations, or custom enterprise solutions? Write to us, and we will get back to you shortly.
            </p>
          </FadeUp>
        </div>
      </section>

      {/* ─── Split Grid: Form vs Info ────────────────────────────────────── */}
      <section className="py-20 max-w-7xl mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Contact Form Panel */}
          <div className="lg:col-span-7">
            <FadeUp>
              <div className="rounded-2xl border border-white/10 bg-neutral-950/40 p-8 glass relative">
                <div className="absolute top-0 right-0 w-[150px] h-[150px] rounded-full bg-violet-600/5 blur-[80px]" />
                
                <h3 className="text-xl font-bold mb-6 text-white flex items-center gap-2">
                  Send a Message <Sparkles className="w-4 h-4 text-violet-400" />
                </h3>

                <AnimatePresence mode="wait">
                  {!formSubmitted ? (
                    <motion.form 
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      onSubmit={handleSubmit} 
                      className="space-y-5 relative z-10"
                    >
                      {/* Name & Email */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="space-y-1.5">
                          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Your Name *</label>
                          <input
                            type="text"
                            required
                            name="name"
                            value={formData.name}
                            onChange={handleChange}
                            placeholder="John Doe"
                            className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                          />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Work Email *</label>
                          <input
                            type="email"
                            required
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="john@company.com"
                            className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                          />
                        </div>
                      </div>

                      {/* Company Info */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="space-y-1.5">
                          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Company Name</label>
                          <input
                            type="text"
                            name="company"
                            value={formData.company}
                            onChange={handleChange}
                            placeholder="Acme Corp"
                            className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors"
                          />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Company Size</label>
                          <select
                            name="size"
                            value={formData.size}
                            onChange={handleChange}
                            className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-neutral-300 focus:outline-none focus:border-violet-500 transition-colors"
                          >
                            <option value="1-10">1 - 10 employees</option>
                            <option value="11-50">11 - 50 employees</option>
                            <option value="51-200">51 - 200 employees</option>
                            <option value="201-500">201 - 500 employees</option>
                            <option value="500+">500+ employees</option>
                          </select>
                        </div>
                      </div>

                      {/* Topic Area */}
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">How can we help? *</label>
                        <select
                          name="help"
                          value={formData.help}
                          onChange={handleChange}
                          className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-neutral-300 focus:outline-none focus:border-violet-500 transition-colors"
                        >
                          <option value="sales">Request an Enterprise Demo / Quote</option>
                          <option value="support">Technical Support Inquiry</option>
                          <option value="billing">Billing or Licensing Account Help</option>
                          <option value="general">General Corporate Inquiry</option>
                        </select>
                      </div>

                      {/* Message Box */}
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-wider">Message *</label>
                        <textarea
                          required
                          name="message"
                          rows={4}
                          value={formData.message}
                          onChange={handleChange}
                          placeholder="Tell us about your campaign optimization and team goals..."
                          className="w-full px-3.5 py-2.5 rounded-lg bg-neutral-900 border border-white/8 text-xs text-white placeholder-neutral-600 focus:outline-none focus:border-violet-500 transition-colors resize-none"
                        />
                      </div>

                      <Button
                        type="submit"
                        variant="violet"
                        className="w-full h-11 text-xs font-semibold mt-2 gap-2"
                        isLoading={loading}
                      >
                        <Send className="w-3.5 h-3.5" /> Submit Inquiry
                      </Button>
                    </motion.form>
                  ) : (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="py-12 flex flex-col items-center justify-center text-center gap-4"
                    >
                      <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                        <Check className="w-6 h-6" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-white">Message Received!</h4>
                        <p className="text-xs text-neutral-400 leading-relaxed max-w-sm mt-1">
                          Thank you for reaching out. A representative from our team will email you at your business address within the next 4 hours.
                        </p>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => setFormSubmitted(false)} className="mt-4 border-white/10 text-xs text-neutral-300">
                        Send Another Inquiry
                      </Button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </FadeUp>
          </div>

          {/* Contact Support & Info Panels */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <FadeUp delay={0.1}>
              <div className="rounded-xl border border-white/6 bg-neutral-950/40 p-6 flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-violet-400 shrink-0">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">Sales Inquiries</h4>
                  <p className="text-xs text-neutral-400 leading-relaxed mt-1 mb-3">
                    Looking to learn about volume pricing, custom integrations, or VPC deployments?
                  </p>
                  <a href="mailto:sales@viptant.com" className="text-xs text-violet-400 hover:underline font-semibold flex items-center gap-1">
                    sales@viptant.com <ArrowRight className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </FadeUp>

            <FadeUp delay={0.2}>
              <div className="rounded-xl border border-white/6 bg-neutral-950/40 p-6 flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-indigo-400 shrink-0">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">Technical Support</h4>
                  <p className="text-xs text-neutral-400 leading-relaxed mt-1 mb-3">
                    Already a customer and need help with vector embeddings upload or prompt versions?
                  </p>
                  <a href="mailto:support@viptant.com" className="text-xs text-indigo-400 hover:underline font-semibold flex items-center gap-1">
                    support@viptant.com <ArrowRight className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </FadeUp>

            <FadeUp delay={0.3}>
              <div className="rounded-xl border border-white/6 bg-neutral-950/40 p-6 flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-neutral-900 border border-white/8 flex items-center justify-center text-emerald-400 shrink-0">
                  <Clock className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">Office Availability</h4>
                  <p className="text-xs text-neutral-400 leading-relaxed mt-1">
                    Support Coverage: <strong className="text-neutral-300">24/7/365</strong>
                  </p>
                  <p className="text-xs text-neutral-400 leading-relaxed mt-0.5">
                    Sales Desk: <strong className="text-neutral-300">9 AM - 6 PM EST</strong> (Mon-Fri)
                  </p>
                </div>
              </div>
            </FadeUp>
          </div>
        </div>
      </section>

      {/* ─── Office Locations with Map Placeholders ─────────────────────── */}
      <section className="py-20 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Global Footprint</SectionLabel>
              <h3 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-2 text-white">Our Office Locations</h3>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {OFFICES.map((off, idx) => (
              <FadeUp 
                key={off.city} 
                delay={idx * 0.05}
                className="group rounded-xl border border-white/6 bg-black overflow-hidden flex flex-col justify-between"
              >
                {/* Schematic Maps Mockup */}
                <div className="aspect-video w-full bg-neutral-950 border-b border-white/5 relative flex items-center justify-center bg-grid-dots overflow-hidden">
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60px] h-[60px] rounded-full bg-violet-600/10 border border-violet-500/20 flex items-center justify-center animate-pulse" />
                  <MapPin className="w-6 h-6 text-violet-400 z-10 animate-bounce" />
                  <span className="absolute bottom-2 left-3 text-[8px] font-mono text-neutral-500">{off.coordinates}</span>
                </div>

                <div className="p-6">
                  <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wider block mb-1">{off.city}</span>
                  <h4 className="text-sm font-bold text-white mb-3">{off.city} Hub</h4>
                  <p className="text-neutral-400 text-xs leading-relaxed mb-4">{off.address}</p>
                  
                  <div className="border-t border-white/5 pt-3.5 space-y-1.5 text-[10px] text-neutral-500">
                    <div className="flex justify-between"><span>Desk Hours:</span><span className="text-neutral-300 font-semibold">{off.hours}</span></div>
                    <div className="flex justify-between"><span>Phone Desk:</span><span className="text-neutral-300 font-semibold">{off.phone}</span></div>
                  </div>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Contact FAQs Accordion ────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5">
        <div className="max-w-3xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>FAQ Accordion</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Questions? We Have Answers
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="border-t border-white/5">
            {FAQS.map((faq, idx) => (
              <FaqItem key={faq.q} q={faq.q} a={faq.a} index={idx} />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

// Reusable micro-FAQ item matching parent components
function FaqItem({ q, a, index }: { q: string; a: string; index: number }) {
  const [open, setOpen] = React.useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35, delay: index * 0.04 }}
      className="border-b border-white/6 py-5"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-left cursor-pointer group"
      >
        <span className="text-sm font-semibold text-white group-hover:text-violet-300 transition-colors">
          {q}
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          className="text-neutral-500 text-xs"
        >
          ▼
        </motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <p className="pt-3.5 text-xs sm:text-sm text-neutral-400 leading-relaxed max-w-2xl">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
