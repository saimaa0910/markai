'use client';

import React, { useState, useRef, useEffect } from 'react';
import useImageStudio from '../hooks/useImageStudio';
import { useAgents } from '../../agents/hooks';
import {
  ImageGenerateRequest,
  ImageHistoryItem,
  ImageProvider,
  ImageModel
} from '../types';

import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';

export const ImageStudio: React.FC = () => {
  const { accessToken, activeOrg } = useAuthStore();
  const {
    useHistory,
    useProviders,
    useModels,
    generateMutation,
    editMutation,
    variationMutation,
    upscaleMutation,
    removeBackgroundMutation,
    replaceBackgroundMutation,
    inpaintMutation,
    outpaintMutation,
  } = useImageStudio();

  // Custom Agents
  const { agents } = useAgents(1, 100);
  const imageAgents = agents.filter(a => a.agent_type === 'IMAGE');
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [savingToKb, setSavingToKb] = useState(false);

  // Queries
  const { data: history = [], refetch: refetchHistory } = useHistory();
  const { data: providers = [] } = useProviders();
  const { data: models = [] } = useModels();

  // Component State
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('minimal');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [selectedModel, setSelectedModel] = useState('flux-schnell');
  const [seed, setSeed] = useState<number | undefined>(undefined);
  
  // Canvas State
  const [activeImage, setActiveImage] = useState<string | null>(null);
  const [brushSize, setBrushSize] = useState(25);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasMask, setHasMask] = useState(false);
  const [bgPrompt, setBgPrompt] = useState('');

  // Agent Selection Effect
  useEffect(() => {
    if (imageAgents.length > 0 && !selectedAgentId) {
      setSelectedAgentId(imageAgents[0].id);
    }
  }, [imageAgents, selectedAgentId]);

  const handleAgentChange = (agentId: string) => {
    setSelectedAgentId(agentId);
    const agent = imageAgents.find(a => a.id === agentId);
    if (agent?.preferred_model) {
      setSelectedModel(agent.preferred_model);
    }
  };

  const handleSaveToKnowledgeBase = async () => {
    if (!activeImage) return;
    setSavingToKb(true);
    try {
      const apiBase = apiClient.defaults.baseURL || '/api/v1';
      const res = await fetch(`${apiBase}/ai/knowledge/save-agent-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken || ''}`,
          'X-Organization-ID': activeOrg?.id || '',
        },
        body: JSON.stringify({
          image_url: activeImage,
          title: prompt || "Agent Generated Creative Image"
        })
      });
      if (!res.ok) throw new Error("Failed to save to Knowledge Base");
      alert("Successfully saved generated image to Knowledge Base under 'Agents File Folder'!");
    } catch (err: any) {
      alert(`Error saving to Knowledge Base: ${err.message}`);
    } finally {
      setSavingToKb(false);
    }
  };

  // SSE Stream log state
  const [streamLogs, setStreamLogs] = useState<string[]>([]);
  const [streamProgress, setStreamProgress] = useState(0);
  const [isStreaming, setIsStreaming] = useState(false);

  // Active generation results
  const [activeResult, setActiveResult] = useState<any>(null);

  // Canvas Refs
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);

  // Default Preset style configurations
  const stylePresets = [
    { id: 'apple', label: 'Apple Premium', icon: '🍏', desc: 'Minimal product focus' },
    { id: 'minimal', label: 'Clean Minimal', icon: '▫️', desc: 'Elegant negative space' },
    { id: 'modern saas', label: 'Modern SaaS', icon: '⚡', desc: 'Tech gradient cards' },
    { id: 'glassmorphism', label: 'Glassmorphism', icon: '🔮', desc: 'Refractive translucent' },
    { id: 'clay', label: 'Matte Clay', icon: '🧸', desc: 'Rounded 3D objects' },
    { id: '3d', label: '3D Render', icon: '🎨', desc: 'Octane rich depth' },
    { id: 'cyberpunk', label: 'Cyberpunk', icon: '🌆', desc: 'Neon rain streets' },
    { id: 'photorealistic', label: 'Photorealistic', icon: '📷', desc: '35mm real lens' },
  ];

  // Initialize Canvas context
  useEffect(() => {
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      canvas.width = canvas.parentElement?.clientWidth || 600;
      canvas.height = canvas.parentElement?.clientHeight || 600;
      
      const context = canvas.getContext('2d');
      if (context) {
        context.lineCap = 'round';
        context.strokeStyle = 'rgba(236, 72, 153, 0.6)'; // Pink mask translucent
        context.lineWidth = brushSize;
        contextRef.current = context;
      }
    }
  }, [activeImage]);

  // Adjust brush size dynamically
  useEffect(() => {
    if (contextRef.current) {
      contextRef.current.lineWidth = brushSize;
    }
  }, [brushSize]);

  // Drawing mouse handlers
  const startDrawing = ({ nativeEvent }: React.MouseEvent) => {
    const { offsetX, offsetY } = nativeEvent;
    if (contextRef.current) {
      contextRef.current.beginPath();
      contextRef.current.moveTo(offsetX, offsetY);
      setIsDrawing(true);
      setHasMask(true);
    }
  };

  const draw = ({ nativeEvent }: React.MouseEvent) => {
    if (!isDrawing || !contextRef.current) return;
    const { offsetX, offsetY } = nativeEvent;
    contextRef.current.lineTo(offsetX, offsetY);
    contextRef.current.stroke();
  };

  const stopDrawing = () => {
    if (contextRef.current) {
      contextRef.current.closePath();
    }
    setIsDrawing(false);
  };

  const clearMask = () => {
    if (canvasRef.current && contextRef.current) {
      contextRef.current.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      setHasMask(false);
    }
  };

  // Convert canvas mask to Base64
  const getMaskBase64 = (): string => {
    if (canvasRef.current) {
      return canvasRef.current.toDataURL('image/png');
    }
    return '';
  };

  // Native SSE event reader
  const handleStreamGenerate = async () => {
    if (!prompt.trim()) return;
    setIsStreaming(true);
    setStreamLogs([]);
    setStreamProgress(10);
    setActiveResult(null);

    const payload: ImageGenerateRequest = {
      prompt,
      style: selectedStyle,
      aspect_ratio: aspectRatio,
      negative_prompt: negativePrompt || undefined,
      model: selectedModel,
      seed,
      agent_id: selectedAgentId || undefined,
    };

    try {
      const apiBase = apiClient.defaults.baseURL || '/api/v1';
      const response = await fetch(`${apiBase}/agents/image/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken || ''}`,
          'X-Organization-ID': activeOrg?.id || '',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Stream request failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      let partialLine = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = (partialLine + chunk).split('\n');
        partialLine = lines.pop() || '';

        let currentEvent = '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.replace('event:', '').trim();
          } else if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.replace('data:', '').trim();
            try {
              const data = JSON.parse(dataStr);
              
              if (currentEvent === 'status') {
                setStreamLogs((prev) => [...prev, data.message]);
                setStreamProgress((prev) => Math.min(prev + 15, 90));
              } else if (currentEvent === 'plan') {
                setStreamLogs((prev) => [...prev, `Plan selected: ${data.thought}`]);
              } else if (currentEvent === 'reflection') {
                setStreamLogs((prev) => [...prev, 'Visual reflection metrics generated.']);
              } else if (currentEvent === 'evaluation') {
                setStreamLogs((prev) => [...prev, 'Layout creative evaluation scores completed.']);
              } else if (currentEvent === 'done') {
                setStreamProgress(100);
                setActiveResult(data);
                setActiveImage(data.storage_url);
                refetchHistory();
                setIsStreaming(false);
              } else if (currentEvent === 'error') {
                setStreamLogs((prev) => [...prev, `Error: ${data.message}`]);
                setIsStreaming(false);
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (err: any) {
      setStreamLogs((prev) => [...prev, `Streaming failure: ${err.message}`]);
      setIsStreaming(false);
    }
  };

  const handleSyncGenerate = () => {
    if (!prompt.trim()) return;
    setStreamProgress(20);
    generateMutation.mutate(
      {
        prompt,
        style: selectedStyle,
        aspect_ratio: aspectRatio,
        negative_prompt: negativePrompt || undefined,
        model: selectedModel,
        seed,
        agent_id: selectedAgentId || undefined,
      },
      {
        onSuccess: (data) => {
          setActiveResult(data);
          setActiveImage(data.storage_url);
          setStreamProgress(100);
        },
      }
    );
  };

  // Canvas Quick Action handlers
  const handleRemoveBg = () => {
    if (!activeImage) return;
    removeBackgroundMutation.mutate(
      { image_url: activeImage },
      {
        onSuccess: (data) => {
          setActiveResult(data);
          setActiveImage(data.storage_url);
        },
      }
    );
  };

  const handleReplaceBg = () => {
    if (!activeImage || !bgPrompt) return;
    replaceBackgroundMutation.mutate(
      { image_url: activeImage, background_prompt: bgPrompt },
      {
        onSuccess: (data) => {
          setActiveResult(data);
          setActiveImage(data.storage_url);
          setBgPrompt('');
        },
      }
    );
  };

  const handleUpscale = () => {
    if (!activeImage) return;
    upscaleMutation.mutate(
      { image_url: activeImage, scale: 2.0 },
      {
        onSuccess: (data) => {
          setActiveResult(data);
          setActiveImage(data.storage_url);
        },
      }
    );
  };

  const handleVariation = () => {
    if (!activeImage) return;
    variationMutation.mutate(
      { image_url: activeImage, style: selectedStyle },
      {
        onSuccess: (data) => {
          setActiveResult(data);
          setActiveImage(data.storage_url);
        },
      }
    );
  };

  const handleInpaint = () => {
    if (!activeImage || !hasMask || !prompt.trim()) return;
    const mask = getMaskBase64();
    inpaintMutation.mutate(
      { image_url: activeImage, mask_url: mask, prompt },
      {
        onSuccess: (data) => {
          setActiveResult(data);
          setActiveImage(data.storage_url);
          clearMask();
        },
      }
    );
  };

  const handleOutpaint = () => {
    if (!activeImage || !hasMask || !prompt.trim()) return;
    const mask = getMaskBase64();
    outpaintMutation.mutate(
      { image_url: activeImage, mask_url: mask, prompt },
      {
        onSuccess: (data) => {
          setActiveResult(data);
          setActiveImage(data.storage_url);
          clearMask();
        },
      }
    );
  };

  // Restore details from history item
  const handleSelectHistory = (item: ImageHistoryItem) => {
    setActiveImage(item.storage_url);
    setPrompt(item.prompt);
    setNegativePrompt(item.negative_prompt || '');
    if (item.tags?.preset_style) {
      setSelectedStyle(item.tags.preset_style.toLowerCase());
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] w-full overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* LEFT PANEL: CONFIG & PROMPTS */}
      <div className="w-1/4 min-w-[320px] max-w-[400px] border-r border-slate-800 bg-slate-900/60 p-5 flex flex-col gap-5 overflow-y-auto backdrop-blur-md">
        <div>
          <h2 className="text-lg font-bold text-violet-400">Creative Configuration</h2>
          <p className="text-xs text-slate-400">Assemble visual cues and target styles</p>
        </div>

        {/* Visual Agent selector */}
        <div className="flex flex-col gap-2 bg-slate-950/30 p-3 rounded-xl border border-slate-800/40">
          <label className="text-xs font-semibold text-slate-300">Active Visual Agent</label>
          <select
            value={selectedAgentId}
            onChange={(e) => handleAgentChange(e.target.value)}
            className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2.5 text-xs focus:outline-none focus:border-violet-500 text-slate-200"
          >
            <option value="">-- Select Agent --</option>
            {imageAgents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                🤖 {agent.name}
              </option>
            ))}
          </select>
          {selectedAgentId && (
            <div className="bg-slate-950/50 rounded-lg p-2.5 border border-slate-800/60 mt-1">
              <span className="text-[10px] text-violet-400 font-bold uppercase tracking-wider block">Agent Context</span>
              <p className="text-[11px] text-slate-300 mt-1 leading-normal font-medium">
                {imageAgents.find((a) => a.id === selectedAgentId)?.description || 'No description provided.'}
              </p>
            </div>
          )}
        </div>

        {/* Style presets */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-300">Preset Style</label>
          <div className="grid grid-cols-2 gap-2">
            {stylePresets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => setSelectedStyle(preset.id)}
                className={`flex flex-col p-3 rounded-lg border text-left transition-all ${
                  selectedStyle === preset.id
                    ? 'border-violet-500 bg-violet-600/20 shadow-[0_0_12px_rgba(139,92,246,0.3)]'
                    : 'border-slate-800 bg-slate-950/40 hover:border-slate-700'
                }`}
              >
                <span className="text-xl mb-1">{preset.icon}</span>
                <span className="text-xs font-bold">{preset.label}</span>
                <span className="text-[10px] text-slate-500 leading-tight">{preset.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Input prompt */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-300">Prompt Description</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A premium leather watch placement on a dark granite stone, soft key lighting..."
            rows={4}
            className="w-full rounded-lg bg-slate-950 border border-slate-800 p-3 text-xs text-slate-200 focus:outline-none focus:border-violet-500 transition-colors placeholder:text-slate-600"
          />
        </div>

        {/* Aspect ratios */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-300">Aspect Ratio</label>
          <div className="flex gap-2">
            {['1:1', '16:9', '9:16', '4:5', '3:2'].map((ratio) => (
              <button
                key={ratio}
                onClick={() => setAspectRatio(ratio)}
                className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                  aspectRatio === ratio
                    ? 'border-violet-500 bg-violet-600/10 text-violet-300'
                    : 'border-slate-800 bg-slate-950/30 hover:border-slate-700 text-slate-400'
                }`}
              >
                {ratio}
              </button>
            ))}
          </div>
        </div>

        {/* Negative prompt */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-300">Negative Constraints</label>
          <input
            type="text"
            value={negativePrompt}
            onChange={(e) => setNegativePrompt(e.target.value)}
            placeholder="watermarks, text, blurry, distortion..."
            className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2.5 text-xs focus:outline-none focus:border-violet-500 transition-colors"
          />
        </div>

        {/* Model select & seed */}
        <div className="flex gap-3">
          <div className="flex-1 flex flex-col gap-1.5">
            <label className="text-[11px] font-semibold text-slate-400">Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="rounded-lg bg-slate-950 border border-slate-800 p-2 text-xs focus:outline-none focus:border-violet-500"
            >
              {models.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
          <div className="w-[100px] flex flex-col gap-1.5">
            <label className="text-[11px] font-semibold text-slate-400">Seed</label>
            <input
              type="number"
              value={seed || ''}
              onChange={(e) => setSeed(e.target.value ? Number(e.target.value) : undefined)}
              placeholder="Random"
              className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2 text-xs focus:outline-none focus:border-violet-500"
            />
          </div>
        </div>

        {/* Action triggers */}
        <div className="flex gap-3 mt-2">
          <button
            onClick={handleSyncGenerate}
            disabled={generateMutation.isPending || isStreaming}
            className="flex-1 py-3 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-bold transition-all disabled:opacity-50"
          >
            {generateMutation.isPending ? 'Drafting...' : 'Quick Gen'}
          </button>
          <button
            onClick={handleStreamGenerate}
            disabled={generateMutation.isPending || isStreaming}
            className="flex-1 py-3 px-4 rounded-lg bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:opacity-90 text-xs font-bold transition-all shadow-[0_4px_16px_rgba(139,92,246,0.3)] disabled:opacity-50 text-white"
          >
            {isStreaming ? 'Streaming...' : '⚡ Stream Render'}
          </button>
        </div>
      </div>

      {/* CENTER PANEL: INTERACTIVE CANVAS */}
      <div className="flex-1 bg-slate-950 p-6 flex flex-col items-center justify-center gap-5 relative">
        
        {/* Top Canvas toolbar controls */}
        {activeImage && (
          <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800 px-4 py-2.5 rounded-full backdrop-blur-md z-10 shadow-lg">
            <button
              onClick={handleRemoveBg}
              disabled={removeBackgroundMutation.isPending}
              className="text-xs hover:text-pink-400 transition-colors font-semibold"
            >
              ✂️ BG Remove
            </button>
            <span className="w-px h-4 bg-slate-800" />
            <button
              onClick={handleUpscale}
              disabled={upscaleMutation.isPending}
              className="text-xs hover:text-pink-400 transition-colors font-semibold"
            >
              🔎 Upscale (2x)
            </button>
            <span className="w-px h-4 bg-slate-800" />
            <button
              onClick={handleVariation}
              disabled={variationMutation.isPending}
              className="text-xs hover:text-pink-400 transition-colors font-semibold"
            >
              🔄 Variation
            </button>
            <span className="w-px h-4 bg-slate-800" />
            <button
              onClick={handleSaveToKnowledgeBase}
              disabled={savingToKb}
              className="text-xs text-violet-400 hover:text-violet-300 font-bold transition-colors flex items-center gap-1"
            >
              💾 {savingToKb ? 'Saving...' : 'Save to KB'}
            </button>
            {hasMask && (
              <>
                <span className="w-px h-4 bg-slate-800" />
                <button
                  onClick={handleInpaint}
                  className="text-xs text-pink-400 hover:text-pink-300 font-bold transition-colors"
                >
                  🖌️ Inpaint
                </button>
                <span className="w-px h-4 bg-slate-800" />
                <button
                  onClick={handleOutpaint}
                  className="text-xs text-pink-400 hover:text-pink-300 font-bold transition-colors"
                >
                  🖼️ Outpaint
                </button>
                <span className="w-px h-4 bg-slate-800" />
                <button
                  onClick={clearMask}
                  className="text-xs hover:text-rose-400 transition-colors"
                >
                  Clear Mask
                </button>
              </>
            )}
          </div>
        )}

        {/* Dynamic loading logger status bar overlay */}
        {(generateMutation.isPending || isStreaming) && (
          <div className="absolute inset-0 bg-slate-950/80 z-20 flex flex-col items-center justify-center gap-4">
            <div className="w-64 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-violet-500 to-pink-500 rounded-full transition-all duration-300"
                style={{ width: `${streamProgress}%` }}
              />
            </div>
            <span className="text-xs font-bold text-violet-300 tracking-wider">
              {streamProgress}% - COMPILED PROCESS
            </span>
            <div className="w-96 max-h-40 overflow-y-auto flex flex-col gap-1.5 items-center mt-3 text-slate-500 px-6 font-mono text-[10px]">
              {streamLogs.map((log, idx) => (
                <div key={idx} className="w-full text-center">
                  &gt; {log}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Canvas panel container */}
        <div className="relative w-full max-w-2xl aspect-square bg-slate-900/40 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex items-center justify-center group">
          {activeImage ? (
            <>
              {/* Image asset backlayer */}
              <img
                src={activeImage}
                alt="Studio layout active render"
                className="absolute inset-0 w-full h-full object-contain pointer-events-none"
              />
              
              {/* Canvas draw mask layer */}
              <canvas
                ref={canvasRef}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                className="absolute inset-0 w-full h-full cursor-crosshair z-10"
              />
            </>
          ) : (
            <div className="flex flex-col items-center gap-2 text-slate-600">
              <span className="text-5xl">🎨</span>
              <span className="text-sm font-semibold">Image Studio Canvas</span>
              <span className="text-xs text-slate-700">Submit a layout prompt to compile creative mockups</span>
            </div>
          )}
        </div>

        {/* Secondary controls panel (Background Swapping) */}
        {activeImage && (
          <div className="w-full max-w-2xl bg-slate-900/60 border border-slate-800/80 p-4 rounded-xl flex items-center gap-3 shadow-lg">
            <input
              type="text"
              value={bgPrompt}
              onChange={(e) => setBgPrompt(e.target.value)}
              placeholder="Swap background: e.g. 'luxurious white marble, soft lighting'..."
              className="flex-1 rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs focus:outline-none focus:border-pink-500 transition-colors"
            />
            <button
              onClick={handleReplaceBg}
              disabled={replaceBackgroundMutation.isPending || !bgPrompt}
              className="px-4 py-2 bg-pink-600/20 text-pink-400 hover:bg-pink-600/30 text-xs font-bold rounded-lg border border-pink-500/30 transition-all"
            >
              Replace BG
            </button>
          </div>
        )}
      </div>

      {/* RIGHT PANEL: INSIGHTS & HISTORY */}
      <div className="w-1/4 min-w-[320px] max-w-[400px] border-l border-slate-800 bg-slate-900/60 p-5 flex flex-col gap-6 overflow-y-auto backdrop-blur-md">
        
        {/* Scoreboard scorecard visual gauges */}
        <div>
          <h2 className="text-lg font-bold text-pink-400">Studio Insights</h2>
          <p className="text-xs text-slate-400">Layout scores and quality critiques</p>
        </div>

        {activeResult ? (
          <div className="flex flex-col gap-4">
            <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
              <span className="text-xs font-bold text-slate-400">Overall Score</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-extrabold text-white">
                  {Math.round(activeResult.evaluation.overall_score * 100)}
                </span>
                <span className="text-xs text-slate-500">/ 100</span>
              </div>
            </div>

            {/* Micro score metrics grids */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Marketing Impact', val: activeResult.evaluation.marketing_score },
                { label: 'Brand Compliance', val: activeResult.evaluation.brand_score },
                { label: 'Accessibility', val: activeResult.evaluation.accessibility },
                { label: 'Image Quality', val: activeResult.evaluation.image_quality },
                { label: 'Creativity', val: activeResult.evaluation.creativity },
                { label: 'Composition', val: activeResult.evaluation.composition },
                { label: 'SEO Readability', val: activeResult.evaluation.seo_score },
                { label: 'Engagement Forecast', val: activeResult.evaluation.engagement_score },
              ].map((metric) => (
                <div key={metric.label} className="bg-slate-950/40 rounded-lg p-2.5 border border-slate-800/60">
                  <span className="text-[10px] text-slate-500 font-medium leading-none block">{metric.label}</span>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-sm font-bold text-white">{Math.round(metric.val * 100)}%</span>
                    <div className="w-12 h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-violet-500" style={{ width: `${metric.val * 100}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Qualitative critique cards */}
            <div className="flex flex-col gap-2.5 mt-2 bg-slate-950/30 border border-slate-800 p-3 rounded-lg text-xs leading-relaxed">
              <span className="font-bold text-slate-300">Critique & Suggestions</span>
              <p className="text-slate-400 font-sans italic">"{activeResult.reflection.critique}"</p>
              {activeResult.reflection.suggested_edits && (
                <div className="mt-1 pt-2 border-t border-slate-800/80 text-violet-400 font-medium">
                  💡 Suggestion: {activeResult.reflection.suggested_edits}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-xs text-slate-500 italic text-center py-10 bg-slate-950/20 border border-slate-800 border-dashed rounded-lg">
            No layout scores compiled. Submit a prompt to execute.
          </div>
        )}

        {/* Layout History Gallery scroll */}
        <div className="flex flex-col gap-3 flex-1">
          <span className="text-xs font-semibold text-slate-300">Creative Gallery History</span>
          <div className="flex flex-col gap-3 overflow-y-auto pr-1">
            {history.map((item) => (
              <button
                key={item.id}
                onClick={() => handleSelectHistory(item)}
                className="flex items-center gap-3 p-2 rounded-lg border border-slate-800/60 bg-slate-950/20 hover:border-slate-700 transition-colors text-left"
              >
                <img
                  src={item.storage_url}
                  alt="thumbnail"
                  className="w-12 h-12 object-cover rounded-md border border-slate-800 bg-slate-900"
                />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-slate-200 truncate">{item.prompt}</div>
                  <div className="text-[10px] text-slate-500 flex items-center justify-between mt-1">
                    <span>{item.provider} / {item.model}</span>
                    <a
                      href={item.storage_url}
                      download={`creative_${item.id}.png`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-pink-400 hover:text-pink-300 hover:underline"
                    >
                      Download
                    </a>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageStudio;
