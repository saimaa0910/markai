/**
 * Content Studio UI Component — Sprint 7.2
 * ========================================
 * High-end, premium split-pane dashboard for writing, improving, reflecting,
 * and reviewing live-generated brand copy.
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  FileText, Play, Copy, Download, RotateCcw, AlertTriangle, CheckCircle,
  Eye, Edit3, Settings, BookOpen, Layers, Sparkles, AlertCircle, BarChart
} from 'lucide-react';
import type {
  ContentType, ImprovementType, ContentSEOMetrics,
  ContentResponse, ContentTemplate, ContentHistoryItem
} from '../types';
import {
  generateContent, improveContent, fetchTemplates,
  fetchHistory, fetchSEOMetrics, streamContentFetch
} from '../services';

interface StudioProps {
  primaryColor?: string;
}

const CONTENT_TYPES: { value: ContentType; label: string; desc: string }[] = [
  { value: 'BLOG_ARTICLE', label: '📖 Blog Article', desc: 'Long-form structured articles' },
  { value: 'LANDING_PAGE', label: '🚀 Landing Page', desc: 'Hero headlines, benefits & CTAs' },
  { value: 'PRODUCT_PAGE', label: '🛍️ Product Page', desc: 'Catchy detail summary copy' },
  { value: 'EMAIL_CAMPAIGN', label: '📧 Email Campaign', desc: 'Subject lines, preview & CTA' },
  { value: 'NEWSLETTER', label: '📰 Newsletter', desc: 'Informational announcements' },
  { value: 'LINKEDIN_POST', label: '💼 LinkedIn Post', desc: 'Engaging narrative copy' },
  { value: 'TWITTER_POST', label: '🐦 Twitter Post', desc: 'Concise short-form updates' },
  { value: 'GOOGLE_AD', label: '🔍 Google Ad', desc: 'Copy optimized for search clicks' },
  { value: 'META_DESCRIPTION', label: '🏷️ Meta Description', desc: 'SEO description snippet' },
  { value: 'IMAGE_PROMPT', label: '🎨 Image Prompt', desc: 'Detailed Midjourney prompt instructions' },
];

const IMPROVEMENTS: { value: ImprovementType; label: string }[] = [
  { value: 'REWRITE', label: '🔄 Rewrite Copy' },
  { value: 'SUMMARIZE', label: '📝 Summarize Text' },
  { value: 'EXPAND', label: '➕ Expand Content' },
  { value: 'SHORTEN', label: '➖ Shorten Content' },
  { value: 'IMPROVE_SEO', label: '📈 Optimize SEO' },
  { value: 'IMPROVE_READABILITY', label: '🧩 Simplify Phrasing' },
  { value: 'IMPROVE_BRAND_VOICE', label: '🏷️ Align with Brand' },
  { value: 'TRANSLATE', label: '🌐 Translate language' },
];

export const ContentStudio: React.FC<StudioProps> = ({ primaryColor = '#7c3aed' }) => {
  // Input fields
  const [contentType, setContentType] = useState<ContentType>('BLOG_ARTICLE');
  const [prompt, setPrompt] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [keywords, setKeywords] = useState('');
  const [brandVoiceOverride, setBrandVoiceOverride] = useState('');
  const [forbiddenWords, setForbiddenWords] = useState('');
  const [preferredWords, setPreferredWords] = useState('');
  
  // Model settings
  const [model, setModel] = useState('groq/llama-3.1-70b');
  const [temp, setTemp] = useState(0.7);
  const [tokensLimit, setTokensLimit] = useState(2000);

  // Editor states
  const [editorText, setEditorText] = useState('');
  const [activeTab, setActiveTab] = useState<'edit' | 'preview'>('edit');
  const [historyStack, setHistoryStack] = useState<string[]>([]);
  const [redoStack, setRedoStack] = useState<string[]>([]);

  // Generation progress
  const [streaming, setStreaming] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [toolLogs, setToolLogs] = useState<{ id: string; msg: string; type: 'start' | 'result' | 'general' }[]>([]);
  const [runTimeline, setRunTimeline] = useState<string[]>([]);
  
  // Output Metrics
  const [latency, setLatency] = useState<number | null>(null);
  const [cost, setCost] = useState<number | null>(null);
  const [tokensUsed, setTokensUsed] = useState<number>(0);
  const [seoScore, setSeoScore] = useState<number | null>(null);
  const [readabilityLevel, setReadabilityLevel] = useState<string | null>(null);
  const [seoMetrics, setSeoMetrics] = useState<ContentSEOMetrics | null>(null);
  const [reflectionPassed, setReflectionPassed] = useState<boolean>(true);
  const [critique, setCritique] = useState<string | null>(null);
  const [suggestedEdits, setSuggestedEdits] = useState<string | null>(null);

  // Lists
  const [templates, setTemplates] = useState<ContentTemplate[]>([]);
  const [historyItems, setHistoryItems] = useState<ContentHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // References
  const textRef = useRef(editorText);
  textRef.current = editorText;

  // Initial loads
  useEffect(() => {
    fetchTemplates().then(setTemplates).catch(console.error);
    loadHistory();
  }, []);

  // Autosave simulation
  useEffect(() => {
    const interval = setInterval(() => {
      if (textRef.current) {
        localStorage.setItem('content_studio_autosave', textRef.current);
      }
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadHistory = () => {
    setLoadingHistory(true);
    fetchHistory()
      .then(setHistoryItems)
      .catch(console.error)
      .finally(() => setLoadingHistory(false));
  };

  const handleTextChange = (text: string) => {
    setHistoryStack(prev => [...prev, editorText]);
    setRedoStack([]);
    setEditorText(text);
  };

  const handleUndo = () => {
    if (historyStack.length === 0) return;
    const prev = historyStack[historyStack.length - 1];
    setRedoStack(p => [...p, editorText]);
    setEditorText(prev);
    setHistoryStack(p => p.slice(0, -1));
  };

  const handleRedo = () => {
    if (redoStack.length === 0) return;
    const next = redoStack[redoStack.length - 1];
    setHistoryStack(p => [...p, editorText]);
    setEditorText(next);
    setRedoStack(p => p.slice(0, -1));
  };

  // Perform Stream Generation
  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    setStreaming(true);
    setEditorText('');
    setStatusMessage('Analyzing objective...');
    setToolLogs([]);
    setRunTimeline(['Plan Created']);
    setLatency(null);
    setCost(null);
    setSeoScore(null);
    setSeoMetrics(null);
    setCritique(null);
    setSuggestedEdits(null);

    const kwArray = keywords.split(',').map(k => k.trim()).filter(Boolean);
    const forbiddenArray = forbiddenWords.split(',').map(w => w.trim()).filter(Boolean);
    const preferredArray = preferredWords.split(',').map(w => w.trim()).filter(Boolean);

    try {
      const generator = streamContentFetch({
        content_type: contentType,
        prompt: prompt,
        brand_voice_override: brandVoiceOverride || undefined,
        forbidden_words: forbiddenArray.length ? forbiddenArray : undefined,
        preferred_words: preferredArray.length ? preferredArray : undefined,
        target_audience: targetAudience || undefined,
        keywords: kwArray.length ? kwArray : undefined,
        preferred_model: model,
        temperature: temp,
        run_reflection: true,
        run_evaluation: true,
      });

      for await (const chunk of generator) {
        const { event, data } = chunk;

        if (event === 'status') {
          setStatusMessage(data.message);
          setRunTimeline(prev => [...prev, data.message]);
        } else if (event === 'plan') {
          setToolLogs(prev => [...prev, { id: uuidStr(), msg: `Planner choice: ${data.thought}`, type: 'general' }]);
        } else if (event === 'tool_start') {
          setToolLogs(prev => [...prev, { id: uuidStr(), msg: `🔧 Tool Started: ${data.tool_name} — ${data.description}`, type: 'start' }]);
        } else if (event === 'tool_result') {
          setToolLogs(prev => [...prev, { id: uuidStr(), msg: `✓ Tool Completed: ${data.tool_name} (Success: ${data.success})`, type: 'result' }]);
        } else if (event === 'llm_token') {
          setEditorText(prev => prev + data.token);
        } else if (event === 'reflection') {
          setReflectionPassed(data.is_satisfactory);
          setCritique(data.critique);
          setSuggestedEdits(data.suggested_edits);
        } else if (event === 'evaluation') {
          setSeoScore(data.seo_score);
          setReadabilityLevel(data.readability_level);
          setSeoMetrics(data);
        } else if (event === 'completed') {
          setLatency(data.latency_ms);
          setCost(data.cost_usd);
          setTokensUsed(data.total_tokens);
          setStreaming(false);
          loadHistory();
        }
      }
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Error: ${err.message || 'Generation failed'}`);
      setStreaming(false);
    }
  };

  // Content Improvement
  const handleImprove = async (impType: ImprovementType) => {
    if (!editorText) return;
    setStatusMessage(`Applying ${impType.replace('_', ' ')}...`);
    setStreaming(true);

    try {
      const res = await improveContent({
        content: editorText,
        improvement_type: impType,
        keywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
        preferred_model: model,
        temperature: 0.5,
      });

      handleTextChange(res.improved_content);
      setStatusMessage('Improvement complete!');
      setStreaming(false);
      // Run local SEO update
      updateLocalSEO(res.improved_content);
    } catch (err) {
      console.error(err);
      setStreaming(false);
    }
  };

  const updateLocalSEO = async (text: string) => {
    const kwArray = keywords.split(',').map(k => k.trim()).filter(Boolean);
    if (!kwArray.length) return;
    try {
      const data = await fetchSEOMetrics(text, kwArray);
      setSeoScore(data.seo_score);
      setReadabilityLevel(data.readability_level);
      setSeoMetrics(data);
    } catch (e) {
      console.error(e);
    }
  };

  const uuidStr = () => Math.random().toString(36).substring(7);

  // Copy Content
  const handleCopy = () => {
    navigator.clipboard.writeText(editorText);
  };

  // Download Content
  const handleDownload = (format: 'md' | 'txt' | 'html') => {
    const blob = new Blob([editorText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `content-studio-draft.${format}`;
    link.click();
  };

  // Counts
  const wordCount = editorText.split(/\s+/).filter(Boolean).length;
  const charCount = editorText.length;
  const estReadingTime = Math.max(1, Math.ceil(wordCount / 200));

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '320px 1fr 340px', height: 'calc(100vh - 64px)',
      background: '#0d0d12', color: '#e2e8f0', fontFamily: "'Inter', sans-serif"
    }}>
      {/* LEFT COLUMN: Setup Configuration */}
      <div style={{
        borderRight: '1px solid rgba(255,255,255,0.06)', padding: 20, display: 'flex',
        flexDirection: 'column', gap: 16, overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={20} color={primaryColor} />
          <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Content Studio</h3>
        </div>

        {/* Content Type */}
        <div>
          <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>CONTENT TYPE</label>
          <select
            value={contentType}
            onChange={(e) => setContentType(e.target.value as ContentType)}
            style={{
              width: '100%', padding: '10px 12px', background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none'
            }}
          >
            {CONTENT_TYPES.map(t => (
              <option key={t.value} value={t.value} style={{ background: '#121218', color: '#fff' }}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* Objective Prompt */}
        <div>
          <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>PROMPT / GOAL</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the product, goal, key topics, and format..."
            style={{
              width: '100%', height: 110, padding: '10px 12px', background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none', resize: 'none'
            }}
          />
        </div>

        {/* SEO Keywords */}
        <div>
          <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>SEO TARGET KEYWORDS (comma separated)</label>
          <input
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="e.g. email builder, marketing agent"
            style={{
              width: '100%', padding: '10px 12px', background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none'
            }}
          />
        </div>

        {/* Target Audience */}
        <div>
          <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>TARGET AUDIENCE</label>
          <input
            value={targetAudience}
            onChange={(e) => setTargetAudience(e.target.value)}
            placeholder="e.g. Sales Directors, tech founders"
            style={{
              width: '100%', padding: '10px 12px', background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none'
            }}
          />
        </div>

        {/* Brand overrides */}
        <div>
          <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>BRAND VOICE OVERRIDE</label>
          <input
            value={brandVoiceOverride}
            onChange={(e) => setBrandVoiceOverride(e.target.value)}
            placeholder="Guidelines, tone, company mission..."
            style={{
              width: '100%', padding: '10px 12px', background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none'
            }}
          />
        </div>

        {/* Dynamic Vocabulary */}
        <div>
          <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.4)', marginBottom: 6 }}>FORBIDDEN WORDS</label>
          <input
            value={forbiddenWords}
            onChange={(e) => setForbiddenWords(e.target.value)}
            placeholder="Avoid: revolutionary, synergy, etc."
            style={{
              width: '100%', padding: '10px 12px', background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, color: '#fff', fontSize: 13, outline: 'none'
            }}
          />
        </div>

        {/* Settings Toggle Accordion */}
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)' }}>LLM ROUTER SETTINGS</span>
            <Settings size={14} color="rgba(255,255,255,0.4)" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>Model Preference</span>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                style={{
                  width: '100%', padding: '6px 8px', background: 'rgba(255,255,255,0.02)',
                  border: '1px solid rgba(255,255,255,0.06)', borderRadius: 6, color: '#fff', fontSize: 11, outline: 'none', marginTop: 4
                }}
              >
                <option value="groq/llama-3.1-70b">Llama 3.1 70B (Groq)</option>
                <option value="groq/llama-3.1-8b">Llama 3.1 8B (Groq)</option>
                <option value="openai/gpt-4o-mini">GPT-4o Mini (OpenAI)</option>
              </select>
            </div>
            <div>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>Temperature ({temp})</span>
              <input
                type="range" min="0.1" max="1.0" step="0.1"
                value={temp}
                onChange={(e) => setTemp(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: primaryColor }}
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleGenerate}
          disabled={streaming || !prompt}
          style={{
            width: '100%', padding: '12px 14px', borderRadius: 8, background: primaryColor,
            color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 'auto',
            opacity: streaming || !prompt ? 0.5 : 1, transition: 'all 0.15s'
          }}
        >
          <Play size={16} fill="#fff" />
          {streaming ? 'Generating Content...' : 'Run Content Agent'}
        </button>
      </div>

      {/* CENTER COLUMN: Editor pane */}
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Editor Toolbar */}
        <div style={{
          height: 48, borderBottom: '1px solid rgba(255,255,255,0.06)', padding: '0 20px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0
        }}>
          {/* Edit / Preview Tabs */}
          <div style={{ display: 'flex', gap: 4 }}>
            {[
              { id: 'edit', label: 'Edit Draft', icon: Edit3 },
              { id: 'preview', label: 'Markdown Preview', icon: Eye },
            ].map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                style={{
                  padding: '5px 12px', borderRadius: 6, fontSize: 12, fontWeight: 600,
                  cursor: 'pointer', border: 'none', display: 'flex', alignItems: 'center', gap: 6,
                  background: activeTab === t.id ? 'rgba(255,255,255,0.08)' : 'transparent',
                  color: activeTab === t.id ? '#fff' : 'rgba(255,255,255,0.4)',
                }}
              >
                <t.icon size={13} />
                {t.label}
              </button>
            ))}
          </div>

          {/* Quick Toolbar */}
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={handleUndo} title="Undo" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.4)' }}><RotateCcw size={14} /></button>
            <button onClick={handleCopy} title="Copy Code" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.4)' }}><Copy size={14} /></button>
            <button onClick={() => handleDownload('md')} title="Download markdown" style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.4)' }}><Download size={14} /></button>
          </div>
        </div>

        {/* Content Editor area */}
        <div style={{ flex: 1, position: 'relative' }}>
          {activeTab === 'edit' ? (
            <textarea
              value={editorText}
              onChange={(e) => handleTextChange(e.target.value)}
              placeholder="Start typing or trigger Content Agent generation to start drafting copy..."
              style={{
                width: '100%', height: '100%', background: 'transparent', border: 'none', outline: 'none',
                color: '#e2e8f0', fontSize: 14, lineHeight: 1.6, padding: '24px 30px', resize: 'none',
                fontFamily: "'Courier New', Courier, monospace"
              }}
            />
          ) : (
            <div style={{
              width: '100%', height: '100%', overflowY: 'auto', padding: '24px 30px',
              lineHeight: 1.7, fontSize: 14, color: '#cbd5e1'
            }}>
              {editorText ? (
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'inherit' }}>{editorText}</pre>
              ) : (
                <span style={{ color: 'rgba(255,255,255,0.3)', fontStyle: 'italic' }}>Nothing to preview yet. Generate some content.</span>
              )}
            </div>
          )}
        </div>

        {/* Footer Statistics */}
        <div style={{
          height: 38, borderTop: '1px solid rgba(255,255,255,0.06)', background: '#0a0a0f',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px', fontSize: 11, color: 'rgba(255,255,255,0.4)'
        }}>
          <div style={{ display: 'flex', gap: 16 }}>
            <span>Words: <strong>{wordCount}</strong></span>
            <span>Chars: <strong>{charCount}</strong></span>
            <span>Read Time: <strong>{estReadingTime} min</strong></span>
          </div>
          <div>
            <span>Live Tokens Counter: <strong>~{Math.round(charCount / 4)}</strong></span>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN: Quality metrics and diagnostics */}
      <div style={{
        borderLeft: '1px solid rgba(255,255,255,0.06)', padding: 20, display: 'flex',
        flexDirection: 'column', gap: 16, overflowY: 'auto', background: '#0a0a0f'
      }}>
        {/* KPI Panel */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
          <div style={{ padding: 10, background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)', textAlign: 'center' }}>
            <span style={{ display: 'block', fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>SEO SCORE</span>
            <span style={{ fontSize: 18, fontWeight: 800, color: seoScore !== null && seoScore >= 0.7 ? '#4ade80' : seoScore !== null ? '#f59e0b' : '#64748b' }}>
              {seoScore !== null ? `${Math.round(seoScore * 100)}%` : '—'}
            </span>
          </div>
          <div style={{ padding: 10, background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)', textAlign: 'center' }}>
            <span style={{ display: 'block', fontSize: 10, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase' }}>READING LEVEL</span>
            <span style={{ fontSize: 14, fontWeight: 700, color: readabilityLevel === 'EASY' ? '#4ade80' : readabilityLevel === 'MEDIUM' ? '#60a5fa' : readabilityLevel === 'DIFFICULT' ? '#f87171' : '#64748b', marginTop: 4, display: 'inline-block' }}>
              {readabilityLevel || '—'}
            </span>
          </div>
        </div>

        {/* Telemetry Cost details */}
        {(latency || cost) && (
          <div style={{ display: 'flex', gap: 8 }}>
            {latency !== null && (
              <div style={{ flex: 1, padding: 8, background: 'rgba(255,255,255,0.02)', borderRadius: 6, fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>
                ⏱️ Latency: <strong style={{ color: '#fff' }}>{latency}ms</strong>
              </div>
            )}
            {cost !== null && (
              <div style={{ flex: 1, padding: 8, background: 'rgba(255,255,255,0.02)', borderRadius: 6, fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>
                💰 Run Cost: <strong style={{ color: '#34d399' }}>${cost.toFixed(5)}</strong>
              </div>
            )}
          </div>
        )}

        {/* RAG search documents sources */}
        {seoMetrics && (
          <div style={{ padding: 12, background: 'rgba(255,255,255,0.02)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.5)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <BookOpen size={13} />
              CITED SOURCES & DENSITY
            </div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div>Internal Links: <strong>{seoMetrics.internal_links_count}</strong></div>
              <div>External Links: <strong>{seoMetrics.external_links_count}</strong></div>
              {Object.keys(seoMetrics.keyword_density).length > 0 && (
                <div style={{ marginTop: 6 }}>
                  <div style={{ fontSize: 9, fontWeight: 700, color: 'rgba(255,255,255,0.3)', marginBottom: 2 }}>KEYWORDS USED:</div>
                  {Object.entries(seoMetrics.keyword_density).map(([kw, dens]) => (
                    <div key={kw} style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
                      <span>{kw}</span>
                      <strong>{(dens * 100).toFixed(1)}%</strong>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Reflector Engine Feedback */}
        {critique && (
          <div style={{
            padding: 12, borderRadius: 8,
            background: reflectionPassed ? 'rgba(74,222,128,0.04)' : 'rgba(248,113,113,0.04)',
            border: `1px solid ${reflectionPassed ? 'rgba(74,222,128,0.15)' : 'rgba(248,113,113,0.15)'}`
          }}>
            <div style={{
              fontSize: 11, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6,
              color: reflectionPassed ? '#4ade80' : '#f87171'
            }}>
              {reflectionPassed ? <CheckCircle size={13} /> : <AlertTriangle size={13} />}
              REFLECTION JUDGE FEEDBACK
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', lineHeight: 1.5 }}>
              "{critique}"
            </div>
            {suggestedEdits && (
              <div style={{ marginTop: 8, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 6, fontSize: 10, color: '#f59e0b' }}>
                💡 {suggestedEdits}
              </div>
            )}
          </div>
        )}

        {/* Diagnostics & Logs Stream */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1, minHeight: 180, overflowY: 'hidden' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Layers size={13} />
            RUN TIMELINE LOGS
          </div>
          <div style={{
            flex: 1, background: '#07070a', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 8,
            padding: 12, overflowY: 'auto', fontFamily: 'monospace', fontSize: 10, display: 'flex', flexDirection: 'column', gap: 6
          }}>
            {statusMessage && (
              <div style={{ color: primaryColor, fontWeight: 700, paddingBottom: 4, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                ⚡ Status: {statusMessage}
              </div>
            )}
            {toolLogs.map(log => (
              <div key={log.id} style={{
                color: log.type === 'start' ? '#a78bfa' : log.type === 'result' ? '#34d399' : 'rgba(255,255,255,0.5)',
                whiteSpace: 'pre-wrap'
              }}>{log.msg}</div>
            ))}
            {toolLogs.length === 0 && !statusMessage && (
              <span style={{ color: 'rgba(255,255,255,0.2)' }}>Idle. Click 'Run' to monitor logs.</span>
            )}
          </div>
        </div>

        {/* Content Improvements Action List */}
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,0.4)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Sparkles size={13} />
            ONE-CLICK IMPROVEMENTS
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
            {IMPROVEMENTS.map(imp => (
              <button
                key={imp.value}
                onClick={() => handleImprove(imp.value)}
                disabled={streaming || !editorText}
                style={{
                  padding: '8px 10px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 6, color: '#fff', fontSize: 10, cursor: 'pointer', textAlign: 'left',
                  opacity: streaming || !editorText ? 0.4 : 1, transition: 'all 0.15s'
                }}
              >
                {imp.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContentStudio;
