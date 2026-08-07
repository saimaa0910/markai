'use client';

/**
 * Social Studio — Enterprise Three-Panel UI — Sprint 7.5
 * =========================================================
 * LEFT   → Platform Selector, Campaign, Brand, Audience, Tone, Schedule, Provider
 * CENTER → AI Chat, Editor, Live Preview, Thread Builder, Carousel Builder
 * RIGHT  → Reflection, Evaluation, Analytics, Hashtags, Character Counter,
 *          Publishing Queue, Timeline
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import useSocialStudio from '../hooks/useSocialStudio';
import { useSocialStore } from '../store/socialStore';
import { useAgents } from '../../agents/hooks';
import {
  PLATFORM_ICONS, PLATFORM_COLORS, CONTENT_TYPE_ICONS,
  formatPlatformName, formatContentTypeName, formatScore,
  getScoreColor, truncateText, copyToClipboard, formatRelativeTime,
} from '../utils';
import { getCharCount } from '../validators';
import type {
  SocialPlatform, SocialContentType, ScheduleType,
  SocialPostResponse, SocialStreamEventType,
} from '../types';

const PLATFORMS: SocialPlatform[] = [
  'LINKEDIN', 'TWITTER', 'INSTAGRAM', 'FACEBOOK', 'THREADS',
  'TIKTOK', 'PINTEREST', 'YOUTUBE_COMMUNITY', 'YOUTUBE_SHORTS',
  'REDDIT', 'DISCORD', 'TELEGRAM', 'MEDIUM', 'QUORA',
];

const CONTENT_TYPES: SocialContentType[] = [
  'POST', 'THREAD', 'CAROUSEL', 'STORY', 'REEL', 'SHORT',
  'ANNOUNCEMENT', 'LAUNCH_POST', 'CASE_STUDY', 'TESTIMONIAL',
  'POLL', 'QUESTION', 'MEME', 'EDUCATIONAL', 'PRODUCT_UPDATE',
  'HIRING_POST', 'COMMUNITY_POST', 'NEWSLETTER_PROMO', 'EVENT_PROMO', 'BLOG_PROMO',
];

const IMAGE_STYLES = [
  { id: 'minimal', label: 'Clean Minimal', icon: '▫️' },
  { id: 'modern saas', label: 'Modern SaaS', icon: '⚡' },
  { id: 'glassmorphism', label: 'Glassmorphism', icon: '🔮' },
  { id: 'photorealistic', label: 'Photorealistic', icon: '📷' },
  { id: 'clay', label: 'Matte Clay', icon: '🧸' },
  { id: '3d', label: '3D Render', icon: '🎨' },
];

const SCHEDULE_OPTIONS: { value: ScheduleType; label: string; icon: string }[] = [
  { value: 'DRAFT', label: 'Save as Draft', icon: '📝' },
  { value: 'PUBLISH_NOW', label: 'Publish Now', icon: '⚡' },
  { value: 'SCHEDULED', label: 'Schedule', icon: '📅' },
  { value: 'RECURRING', label: 'Recurring', icon: '🔄' },
  { value: 'QUEUE', label: 'Add to Queue', icon: '📋' },
];

export const SocialStudio: React.FC = () => {
  const store = useSocialStore();
  const {
    startStream, stopStream, streamTokens, streamEvents,
    isStreaming, streamResult,
    generateMutation, hashtagsMutation, optimizeMutation,
    usePlatforms, useHistory, useQueue, useAnalytics,
    scheduleMutation, publishMutation,
  } = useSocialStudio();

  const { data: platforms = [] } = usePlatforms();
  const { data: history = [] } = useHistory(undefined);
  const { data: queueData } = useQueue();
  const { data: analyticsData } = useAnalytics();

  // Custom Social Agents
  const { agents } = useAgents(1, 100);
  const socialAgents = agents.filter(a => a.agent_type === 'SOCIAL');
  const [selectedAgentId, setSelectedAgentId] = useState('');

  useEffect(() => {
    if (socialAgents.length > 0 && !selectedAgentId) {
      setSelectedAgentId(socialAgents[0].id);
    }
  }, [socialAgents, selectedAgentId]);

  const handleAgentChange = (agentId: string) => {
    setSelectedAgentId(agentId);
    const agent = socialAgents.find(a => a.id === agentId);
    if (agent?.temperature !== undefined) {
      store.setTemperature(agent.temperature);
    }
  };

  // Chat / prompt state
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [activeResult, setActiveResult] = useState<SocialPostResponse | null>(null);
  const [editedContent, setEditedContent] = useState('');
  const [activePanel, setActivePanel] = useState<'chat' | 'editor' | 'preview' | 'thread'>('chat');
  const [rightTab, setRightTab] = useState<'reflection' | 'evaluation' | 'analytics' | 'hashtags' | 'queue'>('evaluation');
  const [copied, setCopied] = useState(false);
  const [keywordInput, setKeywordInput] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, streamTokens]);

  // Sync stream result to active result
  useEffect(() => {
    if (streamResult) {
      setActiveResult(streamResult);
      setEditedContent(streamResult.content?.raw_content || '');
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: streamResult.content?.raw_content || '' },
      ]);
    }
  }, [streamResult]);

  const handleGenerate = useCallback(async () => {
    if (!store.prompt.trim() || isStreaming) return;

    setChatMessages((prev) => [...prev, { role: 'user', content: store.prompt }]);
    setActiveResult(null);
    setEditedContent('');

    await startStream({
      platform: store.platform,
      content_type: store.contentType,
      prompt: store.prompt,
      target_audience: store.targetAudience || undefined,
      keywords: store.keywords.length ? store.keywords : undefined,
      brand_voice_override: store.brandVoice || undefined,
      generate_image: store.generateImage,
      image_style: store.imageStyle,
      temperature: store.temperature,
      run_reflection: true,
      run_evaluation: true,
      agent_id: selectedAgentId || undefined,
    });
  }, [store, isStreaming, startStream, selectedAgentId]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleGenerate();
    }
  };

  const handleAddKeyword = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && keywordInput.trim()) {
      store.setKeywords([...store.keywords, keywordInput.trim()]);
      setKeywordInput('');
    }
  };

  const handleCopy = async () => {
    const text = editedContent || activeResult?.content?.raw_content || '';
    await copyToClipboard(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const charInfo = getCharCount(editedContent || activeResult?.content?.raw_content || '', store.platform);
  const currentEvent = streamEvents[streamEvents.length - 1];
  const currentPhase = currentEvent?.type as SocialStreamEventType | undefined;

  // Color for current platform
  const platformColor = PLATFORM_COLORS[store.platform] || '#0ea5e9';

  return (
    <div
      id="social-studio"
      style={{
        display: 'flex',
        height: '100vh',
        background: 'linear-gradient(135deg, #0a0a1a 0%, #0d0d2b 50%, #0a0a1a 100%)',
        color: '#e2e8f0',
        fontFamily: "'Inter', -apple-system, sans-serif",
        overflow: 'hidden',
      }}
    >
      {/* ═══════════════════════════════════════════════════════════════════════
          LEFT PANEL — Configuration
         ═══════════════════════════════════════════════════════════════════════ */}
      <div
        id="social-left-panel"
        style={{
          width: '280px',
          minWidth: '260px',
          background: 'rgba(255,255,255,0.03)',
          borderRight: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          flexDirection: 'column',
          overflowY: 'auto',
          padding: '20px 16px',
          gap: '20px',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
          <div style={{
            background: `linear-gradient(135deg, ${platformColor}33, ${platformColor}11)`,
            border: `1px solid ${platformColor}44`,
            borderRadius: '10px',
            padding: '8px',
            fontSize: '20px',
          }}>
            📲
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>Social Studio</div>
            <div style={{ fontSize: '11px', color: '#64748b' }}>Enterprise Social Agent</div>
          </div>
        </div>

        {/* Agent Selector */}
        <Section title="Social Agent">
          <select
            id="social-agent-select"
            value={selectedAgentId}
            onChange={(e) => handleAgentChange(e.target.value)}
            style={selectStyle}
          >
            <option value="">-- Select Agent --</option>
            {socialAgents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                🤖 {agent.name}
              </option>
            ))}
          </select>
          {selectedAgentId && (
            <div style={{
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '8px',
              padding: '10px',
              marginTop: '6px',
              fontSize: '11px',
              color: '#94a3b8',
              lineHeight: '1.4',
            }}>
              <strong style={{ color: platformColor, display: 'block', marginBottom: '2px' }}>Agent Info:</strong>
              {socialAgents.find((a) => a.id === selectedAgentId)?.description || 'No description provided.'}
            </div>
          )}
        </Section>

        {/* Platform Selector */}
        <Section title="Platform">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
            {PLATFORMS.map((p) => (
              <button
                key={p}
                id={`platform-btn-${p.toLowerCase()}`}
                onClick={() => store.setPlatform(p)}
                title={formatPlatformName(p)}
                style={{
                  background: store.platform === p
                    ? `${PLATFORM_COLORS[p]}22`
                    : 'rgba(255,255,255,0.04)',
                  border: store.platform === p
                    ? `1.5px solid ${PLATFORM_COLORS[p]}88`
                    : '1px solid rgba(255,255,255,0.07)',
                  borderRadius: '8px',
                  padding: '8px 4px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.2s',
                }}
              >
                {PLATFORM_ICONS[p]}
              </button>
            ))}
          </div>
          <div style={{
            fontSize: '12px', fontWeight: 600, color: platformColor,
            textAlign: 'center', marginTop: '6px',
          }}>
            {formatPlatformName(store.platform)}
          </div>
        </Section>

        {/* Content Type */}
        <Section title="Content Type">
          <select
            id="content-type-select"
            value={store.contentType}
            onChange={(e) => store.setContentType(e.target.value as SocialContentType)}
            style={selectStyle}
          >
            {CONTENT_TYPES.map((ct) => (
              <option key={ct} value={ct}>
                {CONTENT_TYPE_ICONS[ct]} {formatContentTypeName(ct)}
              </option>
            ))}
          </select>
        </Section>

        {/* Target Audience */}
        <Section title="Target Audience">
          <input
            id="audience-input"
            type="text"
            placeholder="e.g. SaaS founders, B2B CMOs..."
            value={store.targetAudience}
            onChange={(e) => store.setTargetAudience(e.target.value)}
            style={inputStyle}
          />
        </Section>

        {/* Keywords */}
        <Section title="Keywords / Hashtag Seeds">
          <input
            id="keyword-input"
            type="text"
            placeholder="Press Enter to add..."
            value={keywordInput}
            onChange={(e) => setKeywordInput(e.target.value)}
            onKeyDown={handleAddKeyword}
            style={inputStyle}
          />
          {store.keywords.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
              {store.keywords.map((kw) => (
                <span
                  key={kw}
                  style={{
                    background: 'rgba(14,165,233,0.15)',
                    border: '1px solid rgba(14,165,233,0.3)',
                    borderRadius: '20px',
                    padding: '2px 8px',
                    fontSize: '11px',
                    color: '#38bdf8',
                    cursor: 'pointer',
                  }}
                  onClick={() => store.setKeywords(store.keywords.filter((k) => k !== kw))}
                >
                  #{kw} ×
                </span>
              ))}
            </div>
          )}
        </Section>

        {/* Brand Voice */}
        <Section title="Brand Voice">
          <textarea
            id="brand-voice-input"
            placeholder="e.g. Professional, data-driven, never use jargon..."
            value={store.brandVoice}
            onChange={(e) => store.setBrandVoice(e.target.value)}
            rows={2}
            style={{ ...inputStyle, resize: 'none' }}
          />
        </Section>

        {/* Image Generation */}
        <Section title="Image">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <ToggleSwitch
              id="generate-image-toggle"
              checked={store.generateImage}
              onChange={store.setGenerateImage}
            />
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Generate Image</span>
          </div>
          {store.generateImage && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
              {IMAGE_STYLES.map((s) => (
                <button
                  key={s.id}
                  id={`style-btn-${s.id.replace(/\s/g, '-')}`}
                  onClick={() => store.setImageStyle(s.id)}
                  style={{
                    background: store.imageStyle === s.id ? 'rgba(139,92,246,0.2)' : 'rgba(255,255,255,0.04)',
                    border: store.imageStyle === s.id ? '1px solid rgba(139,92,246,0.5)' : '1px solid rgba(255,255,255,0.07)',
                    borderRadius: '6px',
                    padding: '6px 4px',
                    cursor: 'pointer',
                    fontSize: '10px',
                    color: store.imageStyle === s.id ? '#a78bfa' : '#94a3b8',
                    transition: 'all 0.2s',
                  }}
                >
                  {s.icon} {s.label}
                </button>
              ))}
            </div>
          )}
        </Section>

        {/* Schedule */}
        <Section title="Schedule">
          <select
            id="schedule-type-select"
            value={store.scheduleType}
            onChange={(e) => store.setScheduleType(e.target.value as ScheduleType)}
            style={selectStyle}
          >
            {SCHEDULE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.icon} {opt.label}</option>
            ))}
          </select>
          {store.scheduleType === 'SCHEDULED' && (
            <input
              id="scheduled-at-input"
              type="datetime-local"
              value={store.scheduledAt || ''}
              onChange={(e) => store.setScheduledAt(e.target.value)}
              style={{ ...inputStyle, marginTop: '6px' }}
            />
          )}
        </Section>

        {/* Temperature */}
        <Section title={`Creativity: ${store.temperature.toFixed(2)}`}>
          <input
            id="temperature-slider"
            type="range"
            min="0.1"
            max="1.5"
            step="0.05"
            value={store.temperature}
            onChange={(e) => store.setTemperature(parseFloat(e.target.value))}
            style={{ width: '100%', accentColor: platformColor }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#475569' }}>
            <span>Conservative</span><span>Creative</span>
          </div>
        </Section>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          CENTER PANEL — AI Chat + Editor + Preview
         ═══════════════════════════════════════════════════════════════════════ */}
      <div
        id="social-center-panel"
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          borderRight: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        {/* Center Header */}
        <div style={{
          padding: '14px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255,255,255,0.02)',
        }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            {(['chat', 'editor', 'preview', 'thread'] as const).map((tab) => (
              <button
                key={tab}
                id={`center-tab-${tab}`}
                onClick={() => setActivePanel(tab)}
                style={{
                  background: activePanel === tab ? `${platformColor}22` : 'transparent',
                  border: activePanel === tab ? `1px solid ${platformColor}44` : '1px solid transparent',
                  borderRadius: '6px',
                  padding: '5px 12px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  color: activePanel === tab ? '#f1f5f9' : '#64748b',
                  fontWeight: activePanel === tab ? 600 : 400,
                  transition: 'all 0.2s',
                  textTransform: 'capitalize',
                }}
              >
                {tab === 'chat' ? '💬' : tab === 'editor' ? '✏️' : tab === 'preview' ? '👁️' : '🧵'} {tab}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {isStreaming && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                fontSize: '11px', color: '#22d3ee',
              }}>
                <div style={{
                  width: '6px', height: '6px', borderRadius: '50%',
                  background: '#22d3ee', animation: 'pulse 1s infinite',
                }} />
                Generating...
              </div>
            )}
            <div style={{
              fontSize: '11px', color: '#475569',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '4px', padding: '3px 8px',
            }}>
              {formatPlatformName(store.platform)} · {formatContentTypeName(store.contentType)}
            </div>
          </div>
        </div>

        {/* Center Content Area */}
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {activePanel === 'chat' && (
            <ChatPanel
              messages={chatMessages}
              streamTokens={isStreaming ? streamTokens : ''}
              isStreaming={isStreaming}
              platformColor={platformColor}
              chatEndRef={chatEndRef}
              currentPhase={currentPhase}
              streamEvents={streamEvents}
            />
          )}

          {activePanel === 'editor' && (
            <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <textarea
                id="social-editor"
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                placeholder="Generated content will appear here for editing..."
                style={{
                  flex: 1,
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '10px',
                  padding: '16px',
                  color: '#e2e8f0',
                  fontSize: '14px',
                  lineHeight: '1.7',
                  resize: 'none',
                  fontFamily: 'inherit',
                  outline: 'none',
                }}
              />
              <div style={{ display: 'flex', gap: '8px' }}>
                <ActionButton id="copy-btn" onClick={handleCopy} color="#38bdf8" icon={copied ? '✓' : '📋'}>
                  {copied ? 'Copied!' : 'Copy'}
                </ActionButton>
                <ActionButton
                  id="optimize-btn"
                  onClick={async () => {
                    if (!editedContent) return;
                    const res = await optimizeMutation.mutateAsync({
                      content: editedContent,
                      platform: store.platform,
                    });
                    setEditedContent(res.optimized_content);
                  }}
                  color="#a78bfa"
                  icon="✨"
                >
                  Optimize
                </ActionButton>
              </div>
            </div>
          )}

          {activePanel === 'preview' && (
            <PreviewPanel
              result={activeResult}
              platform={store.platform}
              platformColor={platformColor}
              editedContent={editedContent}
            />
          )}

          {activePanel === 'thread' && (
            <ThreadBuilder
              result={activeResult}
              platform={store.platform}
              platformColor={platformColor}
            />
          )}
        </div>

        {/* Prompt Input Area */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid rgba(255,255,255,0.08)',
          background: 'rgba(255,255,255,0.02)',
        }}>
          <div style={{
            display: 'flex',
            gap: '10px',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: '12px',
            padding: '10px 14px',
            alignItems: 'flex-end',
          }}>
            <textarea
              id="prompt-textarea"
              placeholder={`Describe your ${formatContentTypeName(store.contentType).toLowerCase()} for ${formatPlatformName(store.platform)}... (⌘+Enter to generate)`}
              value={store.prompt}
              onChange={(e) => store.setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
              style={{
                flex: 1,
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: '#e2e8f0',
                fontSize: '14px',
                lineHeight: '1.5',
                resize: 'none',
                fontFamily: 'inherit',
              }}
            />
            <button
              id="generate-btn"
              onClick={isStreaming ? stopStream : handleGenerate}
              disabled={!store.prompt.trim() && !isStreaming}
              style={{
                background: isStreaming
                  ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                  : `linear-gradient(135deg, ${platformColor}, ${platformColor}cc)`,
                border: 'none',
                borderRadius: '8px',
                padding: '8px 16px',
                cursor: store.prompt.trim() || isStreaming ? 'pointer' : 'not-allowed',
                color: '#fff',
                fontSize: '13px',
                fontWeight: 600,
                whiteSpace: 'nowrap',
                transition: 'all 0.2s',
                opacity: !store.prompt.trim() && !isStreaming ? 0.5 : 1,
              }}
            >
              {isStreaming ? '⏹ Stop' : '⚡ Generate'}
            </button>
          </div>
          <div style={{ fontSize: '11px', color: '#475569', marginTop: '6px', paddingLeft: '4px' }}>
            ⌘+Enter to generate · {PLATFORM_ICONS[store.platform]} {formatPlatformName(store.platform)} ·{' '}
            <span style={{ color: charInfo.status === 'ok' ? '#22d3ee' : charInfo.status === 'warning' ? '#f59e0b' : '#ef4444' }}>
              {charInfo.used}/{charInfo.limit} chars
            </span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════
          RIGHT PANEL — Reflection, Evaluation, Analytics, Hashtags, Queue
         ═══════════════════════════════════════════════════════════════════════ */}
      <div
        id="social-right-panel"
        style={{
          width: '300px',
          minWidth: '280px',
          background: 'rgba(255,255,255,0.02)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Right Tabs */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          overflowX: 'auto',
          padding: '0 8px',
        }}>
          {(['evaluation', 'reflection', 'hashtags', 'analytics', 'queue'] as const).map((tab) => (
            <button
              key={tab}
              id={`right-tab-${tab}`}
              onClick={() => setRightTab(tab)}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: rightTab === tab ? `2px solid ${platformColor}` : '2px solid transparent',
                padding: '10px 10px',
                cursor: 'pointer',
                fontSize: '11px',
                color: rightTab === tab ? '#f1f5f9' : '#64748b',
                fontWeight: rightTab === tab ? 600 : 400,
                whiteSpace: 'nowrap',
                textTransform: 'capitalize',
                transition: 'all 0.2s',
              }}
            >
              {tab === 'evaluation' ? '📊' : tab === 'reflection' ? '🔍' : tab === 'hashtags' ? '#' : tab === 'analytics' ? '📈' : '📋'} {tab}
            </button>
          ))}
        </div>

        {/* Right Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
          {rightTab === 'evaluation' && (
            <EvaluationPanel result={activeResult} platformColor={platformColor} />
          )}
          {rightTab === 'reflection' && (
            <ReflectionPanel result={activeResult} platformColor={platformColor} />
          )}
          {rightTab === 'hashtags' && (
            <HashtagPanel result={activeResult} platformColor={platformColor} />
          )}
          {rightTab === 'analytics' && (
            <AnalyticsPanel analytics={analyticsData} history={history} platformColor={platformColor} />
          )}
          {rightTab === 'queue' && (
            <QueuePanel queue={queueData} platformColor={platformColor} />
          )}
        </div>

        {/* Character Counter */}
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid rgba(255,255,255,0.08)',
          background: 'rgba(255,255,255,0.02)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '11px', color: '#64748b' }}>Character Count</span>
            <span style={{
              fontSize: '11px', fontWeight: 600,
              color: charInfo.status === 'ok' ? '#22d3ee' : charInfo.status === 'warning' ? '#f59e0b' : '#ef4444',
            }}>
              {charInfo.used} / {charInfo.limit}
            </span>
          </div>
          <div style={{
            height: '4px', borderRadius: '2px',
            background: 'rgba(255,255,255,0.1)',
            overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${Math.min(charInfo.percentage, 100)}%`,
              background: charInfo.status === 'ok'
                ? 'linear-gradient(90deg, #22d3ee, #38bdf8)'
                : charInfo.status === 'warning'
                ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                : 'linear-gradient(90deg, #ef4444, #f87171)',
              borderRadius: '2px',
              transition: 'all 0.3s',
            }} />
          </div>
        </div>

        {/* Publish Action */}
        {activeResult?.run_id && (
          <div style={{ padding: '12px 16px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <button
              id="publish-btn"
              onClick={() => {
                if (!activeResult.run_id) return;
                publishMutation.mutate({
                  post_run_id: activeResult.run_id,
                  platform: store.platform,
                  override_content: editedContent || undefined,
                  image_url: activeResult.image_url || undefined,
                });
              }}
              disabled={publishMutation.isPending}
              style={{
                width: '100%',
                background: `linear-gradient(135deg, ${platformColor}, ${platformColor}cc)`,
                border: 'none',
                borderRadius: '8px',
                padding: '10px',
                cursor: 'pointer',
                color: '#fff',
                fontSize: '13px',
                fontWeight: 700,
                transition: 'all 0.2s',
                opacity: publishMutation.isPending ? 0.7 : 1,
              }}
            >
              {publishMutation.isPending ? '⏳ Publishing...' : `🚀 Publish to ${formatPlatformName(store.platform)}`}
            </button>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
      `}</style>
    </div>
  );
};

// ─── Sub-components ───────────────────────────────────────────────────────────

const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div>
    <div style={{
      fontSize: '10px', fontWeight: 700, color: '#475569',
      textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '8px',
    }}>
      {title}
    </div>
    {children}
  </div>
);

const ToggleSwitch: React.FC<{ id: string; checked: boolean; onChange: (v: boolean) => void }> = ({
  id, checked, onChange,
}) => (
  <button
    id={id}
    onClick={() => onChange(!checked)}
    style={{
      width: '36px', height: '20px', borderRadius: '10px',
      background: checked ? 'linear-gradient(90deg, #0ea5e9, #38bdf8)' : 'rgba(255,255,255,0.1)',
      border: 'none', cursor: 'pointer', position: 'relative', transition: 'all 0.3s',
    }}
  >
    <div style={{
      position: 'absolute', top: '2px',
      left: checked ? '18px' : '2px',
      width: '16px', height: '16px', borderRadius: '50%',
      background: '#fff', transition: 'all 0.3s',
      boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
    }} />
  </button>
);

const ActionButton: React.FC<{
  id: string;
  onClick: () => void;
  color: string;
  icon: string;
  children: React.ReactNode;
}> = ({ id, onClick, color, icon, children }) => (
  <button
    id={id}
    onClick={onClick}
    style={{
      background: `${color}18`,
      border: `1px solid ${color}40`,
      borderRadius: '6px',
      padding: '6px 14px',
      cursor: 'pointer',
      color,
      fontSize: '12px',
      fontWeight: 600,
      transition: 'all 0.2s',
    }}
  >
    {icon} {children}
  </button>
);

const ScoreBar: React.FC<{ label: string; value: number }> = ({ label, value }) => (
  <div style={{ marginBottom: '10px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
      <span style={{ fontSize: '11px', color: '#94a3b8' }}>{label}</span>
      <span style={{ fontSize: '11px', fontWeight: 700, color: getScoreColor(value) }}>
        {formatScore(value)}
      </span>
    </div>
    <div style={{ height: '4px', borderRadius: '2px', background: 'rgba(255,255,255,0.07)' }}>
      <div style={{
        height: '100%', width: `${value * 100}%`,
        background: `linear-gradient(90deg, ${getScoreColor(value)}, ${getScoreColor(value)}99)`,
        borderRadius: '2px', transition: 'width 0.5s ease',
      }} />
    </div>
  </div>
);

const ChatPanel: React.FC<{
  messages: Array<{ role: 'user' | 'assistant'; content: string }>;
  streamTokens: string;
  isStreaming: boolean;
  platformColor: string;
  chatEndRef: React.RefObject<HTMLDivElement | null>;
  currentPhase?: SocialStreamEventType;
  streamEvents: Array<{ type: SocialStreamEventType; data: any }>;
}> = ({ messages, streamTokens, isStreaming, platformColor, chatEndRef, currentPhase, streamEvents }) => {
  const PHASE_LABELS: Partial<Record<SocialStreamEventType, string>> = {
    planning: '🗺️ Planning execution...',
    brand: '🎨 Loading brand context...',
    campaign: '📣 Loading campaign...',
    knowledge: '📚 Searching knowledge...',
    content: '✍️ Generating content...',
    image: '🖼️ Creating image...',
    hashtags: '#️⃣ Generating hashtags...',
    optimization: '⚙️ Optimizing for platform...',
    reflection: '🔍 Running reflection...',
    evaluation: '📊 Scoring output...',
    completed: '✅ Complete!',
  };

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {messages.length === 0 && !isStreaming && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#334155' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>📲</div>
          <div style={{ fontSize: '15px', fontWeight: 600, color: '#475569' }}>Social Studio ready</div>
          <div style={{ fontSize: '12px', marginTop: '6px' }}>
            Choose a platform, describe your post, and hit ⚡ Generate
          </div>
        </div>
      )}

      {messages.map((msg, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            animation: 'fadeIn 0.3s ease',
          }}
        >
          <div style={{
            maxWidth: '85%',
            background: msg.role === 'user'
              ? `linear-gradient(135deg, ${platformColor}33, ${platformColor}11)`
              : 'rgba(255,255,255,0.06)',
            border: msg.role === 'user'
              ? `1px solid ${platformColor}44`
              : '1px solid rgba(255,255,255,0.1)',
            borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            padding: '12px 16px',
            fontSize: '13px',
            lineHeight: '1.7',
            color: '#e2e8f0',
            whiteSpace: 'pre-wrap',
          }}>
            {msg.content}
          </div>
        </div>
      ))}

      {isStreaming && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Phase indicator */}
          {currentPhase && PHASE_LABELS[currentPhase] && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              fontSize: '12px', color: '#38bdf8',
              padding: '8px 12px',
              background: 'rgba(14,165,233,0.08)',
              border: '1px solid rgba(14,165,233,0.2)',
              borderRadius: '8px',
            }}>
              <div style={{
                width: '6px', height: '6px', borderRadius: '50%',
                background: '#38bdf8', animation: 'pulse 1s infinite',
              }} />
              {PHASE_LABELS[currentPhase]}
            </div>
          )}

          {/* Streaming tokens */}
          {streamTokens && (
            <div style={{
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '16px 16px 16px 4px',
              padding: '12px 16px',
              fontSize: '13px',
              lineHeight: '1.7',
              color: '#e2e8f0',
              whiteSpace: 'pre-wrap',
              maxWidth: '85%',
            }}>
              {streamTokens}
              <span style={{ display: 'inline-block', width: '2px', height: '14px', background: '#38bdf8', marginLeft: '2px', animation: 'pulse 0.8s infinite' }} />
            </div>
          )}
        </div>
      )}
      <div ref={chatEndRef} />
    </div>
  );
};

const PreviewPanel: React.FC<{
  result: SocialPostResponse | null;
  platform: SocialPlatform;
  platformColor: string;
  editedContent: string;
}> = ({ result, platform, platformColor, editedContent }) => {
  const displayContent = editedContent || result?.content?.raw_content || '';
  if (!displayContent) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#334155' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>{PLATFORM_ICONS[platform]}</div>
          <div style={{ fontSize: '12px' }}>Generate a post to see the preview</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Platform Mock Card */}
      <div style={{
        background: 'rgba(255,255,255,0.05)',
        border: `1px solid ${platformColor}33`,
        borderRadius: '12px',
        padding: '16px',
        animation: 'fadeIn 0.3s ease',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '50%',
            background: `linear-gradient(135deg, ${platformColor}, ${platformColor}88)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '16px',
          }}>
            🏢
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>Your Company</div>
            <div style={{ fontSize: '11px', color: '#64748b' }}>Just now · {PLATFORM_ICONS[platform]} {formatPlatformName(platform)}</div>
          </div>
        </div>

        {/* Content */}
        <div style={{ fontSize: '13px', lineHeight: '1.7', color: '#cbd5e1', whiteSpace: 'pre-wrap', marginBottom: '12px' }}>
          {displayContent}
        </div>

        {/* Image Preview */}
        {result?.image_url && (
          <img
            src={result.image_url}
            alt="Generated social media image"
            style={{
              width: '100%', borderRadius: '8px',
              marginBottom: '12px', maxHeight: '300px', objectFit: 'cover',
            }}
          />
        )}

        {/* Engagement mock */}
        <div style={{
          display: 'flex', gap: '16px', paddingTop: '10px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
          fontSize: '12px', color: '#475569',
        }}>
          <span>👍 Like</span><span>💬 Comment</span><span>↗️ Share</span>
        </div>
      </div>
    </div>
  );
};

const ThreadBuilder: React.FC<{
  result: SocialPostResponse | null;
  platform: SocialPlatform;
  platformColor: string;
}> = ({ result, platform, platformColor }) => {
  const parts = result?.content?.thread_parts;
  if (!parts || parts.length === 0) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#334155' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🧵</div>
          <div style={{ fontSize: '12px' }}>Generate a THREAD post to see the thread builder</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {parts.map((part, i) => (
        <div key={i} style={{
          display: 'flex', gap: '12px',
          animation: 'fadeIn 0.3s ease',
          animationDelay: `${i * 0.05}s`,
        }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
            <div style={{
              width: '28px', height: '28px', borderRadius: '50%',
              background: `linear-gradient(135deg, ${platformColor}, ${platformColor}99)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '11px', fontWeight: 700, color: '#fff',
            }}>
              {i + 1}
            </div>
            {i < parts.length - 1 && (
              <div style={{ width: '2px', flex: 1, minHeight: '20px', background: 'rgba(255,255,255,0.1)' }} />
            )}
          </div>
          <div style={{
            flex: 1,
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '10px',
            padding: '12px',
            fontSize: '13px',
            lineHeight: '1.6',
            color: '#cbd5e1',
          }}>
            {part}
          </div>
        </div>
      ))}
    </div>
  );
};

const EvaluationPanel: React.FC<{ result: SocialPostResponse | null; platformColor: string }> = ({
  result, platformColor,
}) => {
  const ev = result?.evaluation;
  if (!ev) {
    return <EmptyState icon="📊" text="Generate a post to see evaluation scores" />;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', animation: 'fadeIn 0.3s ease' }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px', borderRadius: '10px', marginBottom: '12px',
        background: ev.passed ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
        border: `1px solid ${ev.passed ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
      }}>
        <span style={{ fontSize: '13px', fontWeight: 700, color: ev.passed ? '#10b981' : '#ef4444' }}>
          {ev.passed ? '✅ Passed' : '⚠️ Needs Review'}
        </span>
        <span style={{
          fontSize: '20px', fontWeight: 800,
          color: getScoreColor(ev.overall_score),
        }}>
          {formatScore(ev.overall_score)}
        </span>
      </div>
      <ScoreBar label="Brand Score" value={ev.brand_score} />
      <ScoreBar label="Engagement Score" value={ev.engagement_score} />
      <ScoreBar label="Platform Score" value={ev.platform_score} />
      <ScoreBar label="Readability" value={ev.readability} />
      <ScoreBar label="SEO Score" value={ev.seo_score} />
      <ScoreBar label="Viral Potential" value={ev.viral_potential} />
      <ScoreBar label="Confidence" value={ev.confidence} />
      {ev.critique && (
        <div style={{
          marginTop: '8px', padding: '10px', borderRadius: '8px',
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
          fontSize: '12px', color: '#fca5a5', lineHeight: '1.5',
        }}>
          {ev.critique}
        </div>
      )}
    </div>
  );
};

const ReflectionPanel: React.FC<{ result: SocialPostResponse | null; platformColor: string }> = ({
  result, platformColor,
}) => {
  const rf = result?.reflection;
  if (!rf) {
    return <EmptyState icon="🔍" text="Generate a post to see reflection results" />;
  }
  const checks = [
    { label: 'Platform Compliant', ok: rf.platform_compliant },
    { label: 'Brand Aligned', ok: rf.brand_compliant },
    { label: 'Readability OK', ok: rf.readability_ok },
    { label: 'Formatting OK', ok: rf.formatting_ok },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', animation: 'fadeIn 0.3s ease' }}>
      {checks.map((c) => (
        <div key={c.label} style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '8px 12px', borderRadius: '8px',
          background: c.ok ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
          border: `1px solid ${c.ok ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
        }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>{c.label}</span>
          <span style={{ fontSize: '14px' }}>{c.ok ? '✅' : '❌'}</span>
        </div>
      ))}
      <ScoreBar label="Engagement Score" value={rf.engagement_score} />
      <ScoreBar label="CTA Quality" value={rf.cta_quality} />
      <ScoreBar label="Hook Quality" value={rf.hook_quality} />
      {rf.critique && (
        <div style={{
          padding: '10px', borderRadius: '8px',
          background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)',
          fontSize: '12px', color: '#fcd34d', lineHeight: '1.5',
        }}>
          💡 {rf.critique}
        </div>
      )}
      {rf.suggested_edits && (
        <div style={{
          padding: '10px', borderRadius: '8px',
          background: 'rgba(14,165,233,0.08)', border: '1px solid rgba(14,165,233,0.2)',
          fontSize: '12px', color: '#7dd3fc', lineHeight: '1.5',
        }}>
          ✏️ {rf.suggested_edits}
        </div>
      )}
    </div>
  );
};

const HashtagPanel: React.FC<{ result: SocialPostResponse | null; platformColor: string }> = ({
  result, platformColor,
}) => {
  const hashtags = result?.hashtags;
  if (!hashtags) {
    return <EmptyState icon="#️⃣" text="Generate a post to see hashtag suggestions" />;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', animation: 'fadeIn 0.3s ease' }}>
      <div style={{
        padding: '10px', borderRadius: '8px',
        background: 'rgba(14,165,233,0.08)', border: '1px solid rgba(14,165,233,0.2)',
        fontSize: '12px', color: '#7dd3fc', lineHeight: '1.6', wordBreak: 'break-word',
      }}>
        {hashtags.hashtag_string}
      </div>
      <div style={{ fontSize: '11px', color: '#64748b' }}>
        {hashtags.total_count} hashtags · Est. reach: {(hashtags.estimated_reach * 100).toFixed(0)}%
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {hashtags.hashtags.map((h) => (
          <div key={h.tag} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '6px 10px', borderRadius: '6px',
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
          }}>
            <span style={{ fontSize: '12px', color: '#38bdf8' }}>{h.tag}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '10px', color: '#475569', textTransform: 'uppercase' }}>{h.category}</span>
              <span style={{ fontSize: '11px', fontWeight: 600, color: getScoreColor(h.reach_score) }}>
                {formatScore(h.reach_score)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const AnalyticsPanel: React.FC<{
  analytics: any;
  history: any[];
  platformColor: string;
}> = ({ analytics, history, platformColor }) => {
  if (!analytics && !history.length) {
    return <EmptyState icon="📈" text="No analytics data yet. Generate some posts first." />;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', animation: 'fadeIn 0.3s ease' }}>
      {analytics && (
        <>
          <StatCard label="Total Posts" value={analytics.total_posts} color="#22d3ee" />
          <StatCard label="Avg Tokens" value={analytics.avg_tokens?.toFixed(0)} color="#a78bfa" />
          <StatCard label="Avg Latency" value={`${analytics.avg_latency_ms?.toFixed(0)}ms`} color="#fb7185" />
        </>
      )}
      <div style={{ fontSize: '10px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '4px' }}>
        Recent Posts
      </div>
      {history.slice(0, 5).map((item: any) => (
        <div key={item.run_id} style={{
          padding: '8px 10px', borderRadius: '8px',
          background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>{item.platform}</span>
            <span style={{ fontSize: '10px', color: '#475569' }}>
              {item.created_at ? formatRelativeTime(item.created_at) : '—'}
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>{truncateText(item.output_preview, 80)}</div>
        </div>
      ))}
    </div>
  );
};

const QueuePanel: React.FC<{ queue: any; platformColor: string }> = ({ queue, platformColor }) => {
  if (!queue || queue.total === 0) {
    return <EmptyState icon="📋" text="Your publishing queue is empty" />;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', animation: 'fadeIn 0.3s ease' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
        <StatCard label="Total" value={queue.total} color="#22d3ee" />
        <StatCard label="Drafts" value={queue.draft_count} color="#f59e0b" />
        <StatCard label="Scheduled" value={queue.scheduled_count} color="#10b981" />
      </div>
      {queue.queue.map((item: any) => (
        <div key={item.run_id} style={{
          padding: '10px 12px', borderRadius: '8px',
          background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>
              {PLATFORM_ICONS[item.platform as SocialPlatform] || '🌐'} {item.platform}
            </span>
            <span style={{
              fontSize: '10px', padding: '1px 6px', borderRadius: '10px',
              background: item.status === 'SCHEDULED' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
              color: item.status === 'SCHEDULED' ? '#10b981' : '#f59e0b',
            }}>
              {item.status}
            </span>
          </div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>{truncateText(item.preview, 70)}</div>
          {item.scheduled_at && (
            <div style={{ fontSize: '10px', color: '#475569', marginTop: '4px' }}>
              📅 {new Date(item.scheduled_at).toLocaleString()}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const StatCard: React.FC<{ label: string; value: any; color: string }> = ({ label, value, color }) => (
  <div style={{
    flex: 1, padding: '10px', borderRadius: '8px', textAlign: 'center',
    background: `${color}12`, border: `1px solid ${color}30`,
  }}>
    <div style={{ fontSize: '16px', fontWeight: 800, color }}>{value}</div>
    <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>{label}</div>
  </div>
);

const EmptyState: React.FC<{ icon: string; text: string }> = ({ icon, text }) => (
  <div style={{ textAlign: 'center', padding: '40px 20px', color: '#334155' }}>
    <div style={{ fontSize: '28px', marginBottom: '8px' }}>{icon}</div>
    <div style={{ fontSize: '12px', lineHeight: '1.5' }}>{text}</div>
  </div>
);

// ─── Styles ───────────────────────────────────────────────────────────────────

const inputStyle: React.CSSProperties = {
  width: '100%',
  background: 'rgba(255,255,255,0.06)',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '8px',
  padding: '8px 10px',
  color: '#e2e8f0',
  fontSize: '12px',
  outline: 'none',
  boxSizing: 'border-box',
  fontFamily: 'inherit',
};

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  cursor: 'pointer',
  appearance: 'none',
};
