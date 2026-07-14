'use client';

import * as React from 'react';
import { Card } from '@eaimos/ui';
import { 
  Megaphone, Plus, Calendar, Mail, Send, Pause, Play, Trash2, 
  Sparkles, Check, ChevronRight, BarChart3, Clock, AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { Dialog } from '@/components/ui/dialog';

interface Campaign {
  id: string;
  name: string;
  channel: 'EMAIL' | 'LINKEDIN' | 'ADWORDS' | 'SOCIAL';
  status: 'ACTIVE' | 'SCHEDULED' | 'PAUSED' | 'COMPLETED';
  audience: string;
  scheduledTime: string;
  content: string;
  stats: {
    sent: number;
    opened: number;
    clicked: number;
  };
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = React.useState<Campaign[]>([
    {
      id: 'c1',
      name: 'Summer Product Launch Outreach',
      channel: 'EMAIL',
      status: 'ACTIVE',
      audience: 'Tech Startup Founders',
      scheduledTime: '2026-07-20 09:00 AM',
      content: 'Hello, discover our new automated AI features...',
      stats: { sent: 1240, opened: 820, clicked: 340 }
    },
    {
      id: 'c2',
      name: 'LinkedIn Lead Gen Ads',
      channel: 'LINKEDIN',
      status: 'SCHEDULED',
      audience: 'VP Marketing / CMOs',
      scheduledTime: '2026-08-01 10:00 AM',
      content: 'Struggling to scale marketing copy? Let our collaborative agents help...',
      stats: { sent: 0, opened: 0, clicked: 0 }
    },
    {
      id: 'c3',
      name: 'Q3 Retargeting AdWords Campaign',
      channel: 'ADWORDS',
      status: 'PAUSED',
      audience: 'Website Visitors (last 30 days)',
      scheduledTime: '2026-07-15 08:00 AM',
      content: 'Get 20% off your first month with code EAIMOS20...',
      stats: { sent: 480, opened: 0, clicked: 84 }
    }
  ]);

  const [wizardOpen, setWizardOpen] = React.useState(false);
  const [wizardStep, setWizardStep] = React.useState(1);

  // Form states for new campaign
  const [formData, setFormData] = React.useState({
    name: '',
    channel: 'EMAIL' as Campaign['channel'],
    audience: '',
    scheduledTime: '',
    content: ''
  });

  const handleCreateCampaign = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.audience) {
      toast.error('Fields Missing', 'Please specify campaign name and target audience.');
      return;
    }

    const newCamp: Campaign = {
      id: `c_${Date.now()}`,
      name: formData.name,
      channel: formData.channel,
      status: formData.scheduledTime ? 'SCHEDULED' : 'ACTIVE',
      audience: formData.audience,
      scheduledTime: formData.scheduledTime || new Date().toLocaleString(),
      content: formData.content,
      stats: { sent: 0, opened: 0, clicked: 0 }
    };

    setCampaigns([newCamp, ...campaigns]);
    setWizardOpen(false);
    setWizardStep(1);
    setFormData({ name: '', channel: 'EMAIL', audience: '', scheduledTime: '', content: '' });
    toast.success('Campaign Configured', 'Multi-channel pipeline is active and queued.');
  };

  const handleToggleStatus = (id: string) => {
    setCampaigns(campaigns.map(c => {
      if (c.id === id) {
        const nextStatus: Campaign['status'] = 
          c.status === 'ACTIVE' ? 'PAUSED' : 
          c.status === 'PAUSED' ? 'ACTIVE' : c.status;
        toast.info('Status Updated', `Campaign is now ${nextStatus.toLowerCase()}.`);
        return { ...c, status: nextStatus };
      }
      return c;
    }));
  };

  const handleDelete = (id: string) => {
    setCampaigns(campaigns.filter(c => c.id !== id));
    toast.success('Campaign Deleted', 'The scheduling queues have been updated.');
  };

  const getChannelColor = (channel: Campaign['channel']) => {
    switch (channel) {
      case 'EMAIL': return 'text-violet-400 bg-violet-500/10 border-violet-500/20';
      case 'LINKEDIN': return 'text-sky-400 bg-sky-500/10 border-sky-500/20';
      case 'ADWORDS': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case 'SOCIAL': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    }
  };

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      {/* Header toolbar */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            Campaign Center <Megaphone className="w-6 h-6 text-violet-500" />
          </h1>
          <p className="text-neutral-400 mt-1">Design, execute, and monitor multi-channel autonomous marketing runs.</p>
        </div>

        <Button variant="violet" size="sm" onClick={() => setWizardOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" /> Create Campaign
        </Button>
      </header>

      {/* Campaigns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {campaigns.map((camp) => (
          <Card key={camp.id} className="glass flex flex-col justify-between p-5 border-white/5 hover:border-violet-500/20 transition-all gap-4">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 border rounded-full ${getChannelColor(camp.channel)}`}>
                  {camp.channel}
                </span>
                
                <span className={`text-[9px] font-bold uppercase ${
                  camp.status === 'ACTIVE' ? 'text-emerald-400' :
                  camp.status === 'SCHEDULED' ? 'text-violet-400' :
                  camp.status === 'PAUSED' ? 'text-amber-400' : 'text-neutral-500'
                }`}>
                  {camp.status}
                </span>
              </div>

              <h3 className="font-bold text-base text-white mt-1 leading-snug">{camp.name}</h3>
              <p className="text-xs text-neutral-400">Target Segment: <strong className="text-neutral-300">{camp.audience}</strong></p>
              
              <div className="flex items-center gap-1.5 text-[10px] text-neutral-500 mt-2">
                <Clock className="w-3.5 h-3.5" />
                <span>{camp.scheduledTime}</span>
              </div>
            </div>

            {/* Performance Stats if Active/Completed */}
            {camp.status !== 'SCHEDULED' && (
              <div className="grid grid-cols-3 gap-2 border-t border-white/5 pt-4">
                <div className="flex flex-col">
                  <span className="text-[9px] text-neutral-500 font-semibold uppercase">Delivered</span>
                  <span className="text-sm font-bold text-white">{camp.stats.sent}</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-neutral-500 font-semibold uppercase">Open Rate</span>
                  <span className="text-sm font-bold text-white">
                    {camp.stats.sent > 0 ? `${((camp.stats.opened / camp.stats.sent) * 100).toFixed(0)}%` : '0%'}
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[9px] text-neutral-500 font-semibold uppercase">CTR</span>
                  <span className="text-sm font-bold text-white">
                    {camp.stats.opened > 0 ? `${((camp.stats.clicked / camp.stats.opened) * 100).toFixed(0)}%` : '0%'}
                  </span>
                </div>
              </div>
            )}

            {/* Actions Panel */}
            <div className="flex items-center justify-between border-t border-white/5 pt-4 mt-2">
              <div className="flex gap-2">
                {camp.status !== 'COMPLETED' && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => handleToggleStatus(camp.id)}
                    className="h-8 px-2.5 text-xs gap-1.5 text-neutral-300 hover:text-white"
                  >
                    {camp.status === 'ACTIVE' ? (
                      <>
                        <Pause className="w-3.5 h-3.5 text-amber-400" /> Pause
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5 text-emerald-400" /> Resume
                      </>
                    )}
                  </Button>
                )}
              </div>

              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => handleDelete(camp.id)}
                className="p-2 h-8 w-8 text-neutral-500 hover:text-rose-400 hover:bg-rose-500/5"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* -------------------------------------------------- */}
      {/* CREATION WIZARD DIALOG */}
      {/* -------------------------------------------------- */}
      <Dialog
        isOpen={wizardOpen}
        onClose={() => {
          setWizardOpen(false);
          setWizardStep(1);
        }}
        title="Create Marketing Campaign"
        description="Launch a targeted dynamic run using collaborative AI templates."
        className="max-w-lg bg-neutral-950"
      >
        <div className="flex flex-col gap-6 mt-2">
          {/* Step Track */}
          <div className="flex justify-between items-center px-4 py-2.5 rounded-lg bg-neutral-900 border border-white/5 text-xs text-neutral-400 select-none">
            <span className={wizardStep >= 1 ? "text-violet-400 font-bold" : ""}>1. Details</span>
            <ChevronRight className="w-3 h-3" />
            <span className={wizardStep >= 2 ? "text-violet-400 font-bold" : ""}>2. AI Content</span>
            <ChevronRight className="w-3 h-3" />
            <span className={wizardStep >= 3 ? "text-violet-400 font-bold" : ""}>3. Schedule</span>
          </div>

          <form onSubmit={handleCreateCampaign} className="flex flex-col gap-4">
            {/* STEP 1: BASICS */}
            {wizardStep === 1 && (
              <div className="flex flex-col gap-4">
                <Input
                  label="Campaign Name"
                  placeholder="Winter Product Promotion"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
                
                <Select
                  label="Marketing Channel"
                  options={[
                    { label: 'Email Outreach', value: 'EMAIL' },
                    { label: 'LinkedIn Ads', value: 'LINKEDIN' },
                    { label: 'Google Search Ads', value: 'ADWORDS' },
                    { label: 'Social Posting', value: 'SOCIAL' }
                  ]}
                  value={formData.channel}
                  onChange={(e) => setFormData({ ...formData, channel: e.target.value as any })}
                />

                <Input
                  label="Audience Segment"
                  placeholder="Enterprise CMOs & Product Directors"
                  required
                  value={formData.audience}
                  onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
                />

                <Button 
                  type="button" 
                  variant="violet" 
                  onClick={() => setWizardStep(2)}
                  className="w-full mt-2"
                >
                  Next: Content Copy <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            )}

            {/* STEP 2: CONTENT */}
            {wizardStep === 2 && (
              <div className="flex flex-col gap-4">
                <div className="p-3 rounded bg-violet-600/10 border border-violet-500/20 text-violet-300 text-xs flex gap-2.5 items-center">
                  <Sparkles className="w-4 h-4 animate-pulse shrink-0" />
                  <span>Draft marketing content utilizing AI variant copy generated inside the Playground.</span>
                </div>
                
                <div>
                  <label className="block text-xs font-semibold text-neutral-400 mb-2">Campaign Message Copy</label>
                  <textarea
                    rows={4}
                    placeholder="Describe product highlights..."
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    className="w-full bg-neutral-900 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50"
                  />
                </div>

                <div className="flex gap-3 mt-2">
                  <Button type="button" variant="outline" onClick={() => setWizardStep(1)} className="flex-1">
                    Back
                  </Button>
                  <Button type="button" variant="violet" onClick={() => setWizardStep(3)} className="flex-1">
                    Next: Scheduler <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}

            {/* STEP 3: SCHEDULE */}
            {wizardStep === 3 && (
              <div className="flex flex-col gap-4">
                <Input
                  label="Schedule Time / Launch Queue"
                  type="text"
                  placeholder="e.g. 2026-07-20 09:00 AM (Leave blank for immediate)"
                  value={formData.scheduledTime}
                  onChange={(e) => setFormData({ ...formData, scheduledTime: e.target.value })}
                  helperText="Date format: YYYY-MM-DD HH:MM AM/PM"
                />

                <div className="flex items-center gap-2 p-3.5 rounded border border-white/5 bg-neutral-900/40 text-neutral-400 text-xs">
                  <AlertCircle className="w-4 h-4 text-violet-400 shrink-0" />
                  <span>Immediate launch publishes instantly to active CRM mailing queues.</span>
                </div>

                <div className="flex gap-3 mt-2">
                  <Button type="button" variant="outline" onClick={() => setWizardStep(2)} className="flex-1">
                    Back
                  </Button>
                  <Button type="submit" variant="violet" className="flex-1">
                    Launch Campaign <Send className="w-4 h-4 ml-1.5" />
                  </Button>
                </div>
              </div>
            )}
          </form>
        </div>
      </Dialog>
    </div>
  );
}
