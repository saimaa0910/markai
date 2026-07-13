'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { Card } from '@eaimos/ui';
import {
  Sparkles,
  ArrowLeft,
  Copy,
  Check,
  Star,
  Loader2,
  Trash2,
  Share2,
  Sliders,
  Type,
  FileText
} from 'lucide-react';

export default function ContentGenerator() {
  const router = useRouter();
  const { token, activeOrgId } = useAuthStore();

  const [generatedList, setGeneratedList] = React.useState<any[]>([]);
  const [activeGen, setActiveGen] = React.useState<any | null>(null);

  // Form State
  const [formData, setFormData] = React.useState({
    title: '',
    copy_type: 'social',
    topic: '',
    tone: 'professional',
    audience: '',
    keywords: '',
    model_name: 'gemini-1.5-flash',
  });

  const [loading, setLoading] = React.useState(true);
  const [generating, setGenerating] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  // Guard routing
  React.useEffect(() => {
    if (!token) {
      router.push('/auth/login');
    }
  }, [token, router]);

  const fetchGeneratedList = React.useCallback(async () => {
    if (!token || !activeOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/v1/generator/', {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId,
        },
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setGeneratedList(data);
      if (data.length > 0 && !activeGen) {
        setActiveGen(data[0]);
      }
    } catch {
      setError('Failed to fetch generated content history.');
    } finally {
      setLoading(false);
    }
  }, [token, activeOrgId, activeGen]);

  React.useEffect(() => {
    fetchGeneratedList();
  }, [fetchGeneratedList]);

  // Actions
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.topic.trim()) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/v1/generator/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error('Generation failed.');
      const newRecord = await res.json();
      setFormData({
        title: '',
        copy_type: 'social',
        topic: '',
        tone: 'professional',
        audience: '',
        keywords: '',
        model_name: 'gemini-1.5-flash',
      });
      setGeneratedList([newRecord, ...generatedList]);
      setActiveGen(newRecord);
    } catch (err: any) {
      setError(err.message || 'An error occurred during copy generation.');
    } finally {
      setGenerating(false);
    }
  };

  const handleRateVariant = async (variantId: string, rating: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/generator/variants/${variantId}/rate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
        body: JSON.stringify({ rating }),
      });
      if (!res.ok) throw new Error();
      const updatedVariant = await res.json();
      
      // Update local state references
      if (activeGen) {
        const updatedVariants = activeGen.variants.map((v: any) =>
          v.id === variantId ? updatedVariant : v
        );
        const updatedGen = { ...activeGen, variants: updatedVariants };
        setActiveGen(updatedGen);
        setGeneratedList(generatedList.map((g) => (g.id === activeGen.id ? updatedGen : g)));
      }
    } catch {
      setError('Failed to record variant rating.');
    }
  };

  const handleDeleteRecord = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/generator/${id}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Organization-ID': activeOrgId || '',
        },
      });
      if (!res.ok) throw new Error();
      if (activeGen?.id === id) {
        setActiveGen(null);
      }
      setGeneratedList(generatedList.filter((g) => g.id !== id));
    } catch {
      setError('Failed to delete content record.');
    }
  };

  const handleCopyToClipboard = (variantId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(variantId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-screen bg-black text-white relative">
      {/* Background glow */}
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-[160px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Navigation back */}
        <button
          onClick={() => router.push('/dashboard')}
          className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors mb-6 text-sm font-semibold cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>

        {/* Header */}
        <header className="mb-12">
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-violet-500" /> AI Content Generator
          </h1>
          <p className="text-neutral-400 mt-1">Generate multi-variant copywriting options and perform A/B design test validation.</p>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
            {error}
          </div>
        )}

        {/* Core Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
          
          {/* Left Column: Form Inputs & History */}
          <div className="space-y-6">
            <Card className="glass p-6">
              <h3 className="font-bold text-lg mb-6 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-violet-400" /> Style Parameters
              </h3>

              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Campaign Title</label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Q3 Launch Email"
                    className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Copy Type</label>
                    <select
                      value={formData.copy_type}
                      onChange={(e) => setFormData({ ...formData, copy_type: e.target.value })}
                      className="w-full px-3 py-2 rounded bg-zinc-900 border border-white/10 text-xs focus:border-violet-500 focus:outline-none"
                    >
                      <option value="social">Social Post</option>
                      <option value="email">Cold Email</option>
                      <option value="ad">Ad Copy</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Tone</label>
                    <select
                      value={formData.tone}
                      onChange={(e) => setFormData({ ...formData, tone: e.target.value })}
                      className="w-full px-3 py-2 rounded bg-zinc-900 border border-white/10 text-xs focus:border-violet-500 focus:outline-none"
                    >
                      <option value="professional">Professional</option>
                      <option value="creative">Creative</option>
                      <option value="witty">Witty</option>
                      <option value="academic">Academic</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Topic Description</label>
                  <textarea
                    required
                    rows={3}
                    value={formData.topic}
                    onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                    placeholder="Describe your product, offer, or service launch..."
                    className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-sm focus:border-violet-500 focus:outline-none resize-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Audience</label>
                    <input
                      type="text"
                      value={formData.audience}
                      onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
                      placeholder="Startups"
                      className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-xs focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">Keywords</label>
                    <input
                      type="text"
                      value={formData.keywords}
                      onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                      placeholder="SaaS, automated"
                      className="w-full px-3 py-2 rounded bg-white/5 border border-white/10 text-xs focus:border-violet-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">AI Model</label>
                  <select
                    value={formData.model_name}
                    onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                    className="w-full px-3 py-2 rounded bg-zinc-900 border border-white/10 text-xs focus:border-violet-500 focus:outline-none"
                  >
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                    <option value="gpt-4o">OpenAI GPT-4o</option>
                    <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={generating}
                  className="w-full py-2.5 rounded bg-violet-600 hover:bg-violet-700 transition-colors font-semibold text-sm cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Generating Variants...
                    </>
                  ) : (
                    <>Generate Copies</>
                  )}
                </button>
              </form>
            </Card>

            {/* Generation History */}
            <Card className="glass p-6">
              <h3 className="font-bold text-sm text-neutral-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4" /> Generation History
              </h3>

              {loading ? (
                <div className="py-8 flex justify-center">
                  <Loader2 className="w-6 h-6 animate-spin text-neutral-500" />
                </div>
              ) : generatedList.length === 0 ? (
                <p className="text-neutral-500 text-xs text-center py-6">No records generated yet.</p>
              ) : (
                <div className="space-y-1">
                  {generatedList.map((g) => (
                    <div
                      key={g.id}
                      className={`flex items-center justify-between p-2 rounded text-sm cursor-pointer group ${
                        activeGen?.id === g.id ? 'bg-violet-500/10 text-violet-300' : 'hover:bg-white/5 text-neutral-300'
                      }`}
                      onClick={() => setActiveGen(g)}
                    >
                      <span className="truncate">{g.title}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteRecord(g.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 text-neutral-500 hover:text-rose-400 transition-opacity cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Right Column: Comparative Variant Output Panel */}
          <div className="lg:col-span-2 space-y-6">
            {activeGen ? (
              <div className="space-y-6">
                <div className="flex justify-between items-center border-b border-white/10 pb-4">
                  <div>
                    <h2 className="text-xl font-bold">{activeGen.title}</h2>
                    <p className="text-xs text-neutral-500 mt-1 font-mono">{activeGen.prompt_used}</p>
                  </div>
                </div>

                {/* Variant side-by-side comparative cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {activeGen.variants.map((variant: any) => (
                    <Card key={variant.id} className="glass p-6 flex flex-col justify-between h-full relative">
                      <div>
                        {/* Title and Rating indicators */}
                        <div className="flex justify-between items-center mb-4">
                          <span className="text-xs font-bold uppercase tracking-wider text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded">
                            {variant.variant_label}
                          </span>
                          
                          {/* Rating score buttons */}
                          <div className="flex gap-1">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <button
                                key={star}
                                onClick={() => handleRateVariant(variant.id, star)}
                                className="p-0.5 text-neutral-600 hover:text-yellow-400 transition-colors cursor-pointer"
                              >
                                <Star
                                  className={`w-3.5 h-3.5 ${
                                    variant.rating && variant.rating >= star ? 'text-yellow-400 fill-yellow-400' : ''
                                  }`}
                                />
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Copy Content */}
                        <p className="text-sm text-neutral-200 whitespace-pre-wrap leading-relaxed mb-6">
                          {variant.content}
                        </p>
                      </div>

                      {/* Card Footer Actions */}
                      <div className="border-t border-white/10 pt-4 flex items-center justify-between mt-auto">
                        <span className="text-[10px] text-neutral-500 font-mono">
                          Model: {variant.model_used}
                        </span>

                        <div className="flex gap-2">
                          <button
                            onClick={() => handleCopyToClipboard(variant.id, variant.content)}
                            className="p-2 rounded bg-neutral-900 border border-white/10 hover:border-violet-500/30 transition-colors text-xs font-bold flex items-center gap-1.5 cursor-pointer"
                          >
                            {copiedId === variant.id ? (
                              <>
                                <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied!
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" /> Copy
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            ) : (
              <Card className="glass text-center py-20">
                <Sparkles className="w-12 h-12 text-neutral-600 mx-auto mb-4 animate-pulse" />
                <h3 className="text-lg font-bold text-neutral-300">Copywriting Workspace Empty</h3>
                <p className="text-sm text-neutral-500 mt-2 max-w-sm mx-auto">
                  Adjust parameter configurations in the left sidebar and launch the generator to compare multiple creative options.
                </p>
              </Card>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
