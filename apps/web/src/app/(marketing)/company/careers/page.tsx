'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Briefcase, Heart, Globe, Terminal, Award, HelpCircle, 
  MapPin, CheckCircle2, ChevronRight, ArrowRight, Zap, RefreshCw 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { FadeUp, GradientHeading, SectionLabel } from '@/components/landing/primitives';
import { useRouter } from 'next/navigation';

interface Job {
  id: string;
  title: string;
  department: string;
  location: string;
  type: string;
}

const JOBS: Job[] = [
  { id: '1', title: 'Senior Frontend Architect (Next.js/React)', department: 'Engineering', location: 'Remote (US/EU)', type: 'Full-time' },
  { id: '2', title: 'Senior AI Research Engineer (LLM Alignment)', department: 'Engineering', location: 'San Francisco, CA / Remote', type: 'Full-time' },
  { id: '3', title: 'Staff Distributed Systems Engineer (Rust/Go)', department: 'Engineering', location: 'Remote', type: 'Full-time' },
  { id: '4', title: 'Enterprise Growth Marketing Manager', department: 'Marketing', location: 'New York, NY / Remote', type: 'Full-time' },
  { id: '5', title: 'Senior Product Designer (SaaS / AI)', department: 'Product', location: 'Remote', type: 'Full-time' },
  { id: '6', title: 'Developer Relations Engineer', department: 'Product', location: 'Remote', type: 'Full-time' },
  { id: '7', title: 'Strategic Account Executive (Enterprise SaaS)', department: 'Sales', location: 'Remote (US)', type: 'Full-time' },
];

const DEPARTMENTS = ['All', 'Engineering', 'Product', 'Marketing', 'Sales'];

const BENEFITS = [
  { icon: Globe, title: 'Remote-First Culture', desc: 'Work from wherever you are most productive. We coordinate asynchronously across time zones.' },
  { icon: Award, title: 'Competitive Equity', desc: 'Every employee receives generous stock options. We want you to own a piece of our future.' },
  { icon: Heart, title: 'Premium Healthcare', desc: '100% covered health, dental, and vision insurance for you and your dependents.' },
  { icon: Zap, title: 'Home Office Stipend', desc: '$2,000 upfront hardware allowance to buy your dream setup plus $100/mo coworking stipend.' },
  { icon: Terminal, title: 'Continuous Growth', desc: '$3,000 annual learning and development budget for books, classes, and conferences.' },
  { icon: Briefcase, title: 'Flexible PTO', desc: 'Take time off when you need it. We require a minimum of 3 weeks taken per year.' },
];

const PROCESS_STEPS = [
  { step: '1', title: 'Application Review', desc: 'We review your profile and project history to see if there is alignment.' },
  { step: '2', title: 'Initial Alignment Call', desc: 'A 30-minute chat with a team member to discuss your goals, culture fit, and role details.' },
  { step: '3', title: 'Technical / Design Sync', desc: 'A hands-on coding or layout session collaborating with our developers or designers.' },
  { step: '4', title: 'Final Team Interview', desc: 'Meet our founders and cross-functional team members to talk through systems architecture.' },
  { step: '5', title: 'Offer & Welcome', desc: 'We align on compensation and present an offer. Onboarding starts the following week.' },
];

const FAQS = [
  { q: 'Do you hire internationally?', a: 'Yes. We are a globally distributed team. While we have hubs in San Francisco and New York, we hire remote workers across the US, Europe, and South America.' },
  { q: 'What is your stack?', a: 'We build on Next.js 16, React 19, TypeScript, Tailwind CSS, Python (FastAPI/SQLAlchemy), PostgreSQL, Redis, and run our vector DB pipelines on specialized cloud architectures.' },
  { q: 'What AI tools do employees use?', a: 'All employees receive premium subscriptions to Github Copilot, Gemini Advanced, and internal Viptant Playground tools to maximize developer velocity.' },
  { q: 'What is the PTO policy?', a: 'We run on a trust-based flexible PTO policy. To prevent burnout, we enforce a mandatory minimum of 15 days off per year.' },
];

export default function CareersPage() {
  const router = useRouter();
  const [selectedDept, setSelectedDept] = React.useState('All');
  const [appliedJob, setAppliedJob] = React.useState<string | null>(null);

  const filteredJobs = JOBS.filter(
    (job) => selectedDept === 'All' || job.department === selectedDept
  );

  const handleApply = (title: string) => {
    setAppliedJob(title);
    setTimeout(() => setAppliedJob(null), 3500);
  };

  return (
    <div className="bg-black text-white font-sans min-h-screen">
      {/* ─── Hero Section ─────────────────────────────────────────────────── */}
      <section className="relative pt-24 pb-20 overflow-hidden bg-grid-dots">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-violet-600/10 blur-[130px] pointer-events-none" />
        <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
          <FadeUp>
            <SectionLabel>We Are Hiring</SectionLabel>
          </FadeUp>
          <FadeUp delay={0.1}>
            <GradientHeading className="text-4xl sm:text-6xl font-extrabold tracking-tight mt-3 mb-6 max-w-4xl mx-auto leading-tight">
              Build the Autonomous Platform of Marketing
            </GradientHeading>
          </FadeUp>
          <FadeUp delay={0.2}>
            <p className="text-neutral-400 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed mb-10">
              Viptant is building the future of automated brand management. Join our remote team of engineers, researchers, and designers crafting premium AI-native workspaces.
            </p>
          </FadeUp>
          <FadeUp delay={0.3}>
            <a 
              href="#positions"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-violet-600 hover:bg-violet-700 transition-colors text-xs font-semibold text-white cursor-pointer"
            >
              View Open Positions <ArrowRight className="w-4 h-4" />
            </a>
          </FadeUp>
        </div>
      </section>

      {/* ─── Why Join & Benefits Section ─────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <FadeUp>
              <SectionLabel>Benefits & Perks</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Designed to Help You Thrive
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {BENEFITS.map((b, i) => {
              const Icon = b.icon;
              return (
                <FadeUp 
                  key={b.title} 
                  delay={i * 0.05} 
                  className="p-8 rounded-xl border border-white/6 bg-neutral-900/10 hover:border-violet-500/20 hover:bg-neutral-900/30 transition-all duration-300 group"
                >
                  <div className="w-10 h-10 rounded-lg bg-neutral-950 border border-white/8 flex items-center justify-center text-neutral-400 group-hover:text-violet-400 group-hover:border-violet-500/20 transition-all mb-5">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h4 className="text-base font-bold text-white mb-2">{b.title}</h4>
                  <p className="text-neutral-400 text-xs md:text-sm leading-relaxed">{b.desc}</p>
                </FadeUp>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── Open Positions List ────────────────────────────────────────── */}
      <section id="positions" className="py-24 relative">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Job Postings</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2 mb-4">
                Open Opportunities
              </GradientHeading>
              <p className="text-neutral-400 text-xs sm:text-sm max-w-md mx-auto">
                Explore our active positions. Find your next role in building state-of-the-art AI tooling.
              </p>
            </FadeUp>
          </div>

          {/* Department Filter Selector */}
          <div className="flex items-center gap-1.5 overflow-x-auto justify-start sm:justify-center py-2 mb-10 border-b border-white/5 scrollbar-none">
            {DEPARTMENTS.map((dept) => (
              <button
                key={dept}
                onClick={() => setSelectedDept(dept)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer shrink-0 ${
                  selectedDept === dept
                    ? 'bg-violet-600 text-white'
                    : 'bg-neutral-900 border border-white/5 text-neutral-400 hover:text-white'
                }`}
              >
                {dept}
              </button>
            ))}
          </div>

          {/* Jobs Listing */}
          <div className="space-y-4">
            <AnimatePresence mode="wait">
              {filteredJobs.length > 0 ? (
                filteredJobs.map((job, idx) => (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -12 }}
                    transition={{ duration: 0.25, delay: idx * 0.03 }}
                    className="p-5 sm:p-6 rounded-xl border border-white/6 bg-neutral-950/40 hover:border-violet-500/25 hover:bg-neutral-900/10 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
                  >
                    <div>
                      <h4 className="text-base font-bold text-white group-hover:text-violet-300 transition-colors mb-1.5">
                        {job.title}
                      </h4>
                      <div className="flex items-center gap-4 text-xs text-neutral-400">
                        <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" /> {job.location}</span>
                        <span>·</span>
                        <span>{job.department}</span>
                        <span>·</span>
                        <span>{job.type}</span>
                      </div>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleApply(job.title)}
                      className="h-9 px-4 text-xs font-semibold text-neutral-300 hover:text-white border-white/10 shrink-0 self-start sm:self-center"
                    >
                      Apply Now <ChevronRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </motion.div>
                ))
              ) : (
                <div className="py-12 text-center text-neutral-500 text-sm">
                  No positions open in this department at this time.
                </div>
              )}
            </AnimatePresence>
          </div>

          {/* Applied Dialog / Confirmation Toast */}
          <AnimatePresence>
            {appliedJob && (
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="fixed bottom-6 right-6 z-50 p-4 rounded-xl border border-violet-500/30 bg-neutral-950 shadow-2xl max-w-sm flex items-start gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400 shrink-0">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">Application Started</h4>
                  <p className="text-[10px] text-neutral-400 mt-0.5 leading-relaxed">
                    Opening the application portal for <strong className="text-violet-300">{appliedJob}</strong>. We look forward to reviewing your profile!
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* ─── Hiring Process Section ─────────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-neutral-950/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <FadeUp>
              <SectionLabel>Hiring Process</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                How We Collaborate
              </GradientHeading>
            </FadeUp>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 max-w-5xl mx-auto relative">
            {PROCESS_STEPS.map((s, i) => (
              <FadeUp 
                key={s.step} 
                delay={i * 0.05} 
                className="p-6 rounded-xl border border-white/6 bg-neutral-900/10 hover:border-violet-500/20 transition-all flex flex-col justify-between"
              >
                <div>
                  <span className="w-7 h-7 rounded-full bg-violet-600/10 border border-violet-500/30 flex items-center justify-center font-mono text-xs font-bold text-violet-400 mb-4">
                    {s.step}
                  </span>
                  <h4 className="text-xs font-bold text-white mb-2">{s.title}</h4>
                  <p className="text-neutral-500 text-[10px] sm:text-xs leading-relaxed">{s.desc}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Careers FAQ Section ────────────────────────────────────────── */}
      <section className="py-24">
        <div className="max-w-3xl mx-auto px-6">
          <div className="text-center mb-14">
            <FadeUp>
              <SectionLabel>Careers FAQ</SectionLabel>
              <GradientHeading className="text-3xl sm:text-4xl font-extrabold tracking-tight mt-2">
                Common Questions
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

      {/* ─── Bottom General Apply CTA ───────────────────────────────────── */}
      <section className="py-24 border-t border-white/5 bg-gradient-to-b from-transparent to-neutral-950/50 text-center relative overflow-hidden">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] bg-violet-600/5 blur-[120px] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-6 relative z-10">
          <FadeUp>
            <h3 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-4">
              Don't See Your Role?
            </h3>
            <p className="text-neutral-400 text-sm max-w-md mx-auto leading-relaxed mb-8">
              We are always looking for talented developers, designers, and growth managers to join Viptant. Send a general application today.
            </p>
            <Button
              variant="violet"
              size="lg"
              onClick={() => handleApply('General Application')}
              className="h-11 px-6 text-xs font-semibold"
            >
              Submit General Application <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </FadeUp>
        </div>
      </section>
    </div>
  );
}

// Reusable micro-FAQ item component matching parent faq.tsx
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
