import * as React from 'react';
import { motion } from 'framer-motion';
import { AIRoutingRule, AIModel } from '../types';
import { Server, ShieldAlert, Cpu, Activity, ArrowRight, Zap, RefreshCw } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api-client';

interface RoutingDiagramProps {
  rules: AIRoutingRule[];
  models: AIModel[];
}

export function RoutingDiagram({ rules, models }: RoutingDiagramProps) {
  // Let's map request types to active rules and model names
  const requestTypes = [
    { key: 'chat', label: 'Chat Sandbox', y: 40 },
    { key: 'content', label: 'Campaign Copy', y: 110 },
    { key: 'vision', label: 'Multimodal Vision', y: 180 },
    { key: 'embeddings', label: 'Semantic Embeddings', y: 250 },
    { key: 'json', label: 'Structured JSON', y: 320 },
  ];

  // Map providers to their details
  const providers = [
    { key: 'groq', label: 'Groq LPU', y: 50, color: '#f59e0b' },
    { key: 'openai', label: 'OpenAI GPT', y: 130, color: '#10b981' },
    { key: 'google', label: 'Google Gemini', y: 210, color: '#38bdf8' },
    { key: 'anthropic', label: 'Claude Core', y: 290, color: '#f43f5e' },
  ];

  // Helper to find path target from rule
  const getRuleModel = (reqType: string) => {
    const rule = rules.find((r) => r.request_type === reqType && r.is_active);
    if (!rule) return null;
    const model = models.find((m) => m.id === rule.model_registry_id);
    return model;
  };

  return (
    <div className="glass rounded-2xl p-6 flex flex-col gap-6 relative overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            AI Gateway Routing Graph <Activity className="w-4.5 h-4.5 text-violet-400 animate-pulse" />
          </h3>
          <p className="text-xs text-neutral-400 mt-0.5">Real-time SVG flow path maps request pipelines to provider nodes.</p>
        </div>
        
        <div className="flex items-center gap-4 text-[10px] text-neutral-400 bg-neutral-900/60 border border-white/5 px-3 py-1.5 rounded-lg">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-violet-500 animate-ping" />
            <span>Active rule stream</span>
          </div>
          <div className="w-px h-3 bg-white/5" />
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-neutral-700" />
            <span>Fallback standby</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas Container */}
      <div className="relative w-full aspect-[2/1] min-h-[300px] border border-white/5 rounded-xl bg-black/40 p-4">
        <svg viewBox="0 0 800 380" className="w-full h-full" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Definitions for gradients and drop shadows */}
          <defs>
            <linearGradient id="purpleGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#c084fc" stopOpacity="0.2" />
            </linearGradient>
            <filter id="shadow">
              <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#8b5cf6" floodOpacity="0.4" />
            </filter>
          </defs>

          {/* BACKGROUND LINES */}
          {requestTypes.map((req) => {
            const activeModel = getRuleModel(req.key);
            if (!activeModel) return null;
            const targetProv = providers.find((p) => p.key === activeModel.provider);
            const targetY = targetProv ? targetProv.y : 190;

            // Draw cubic bezier curve from request to provider
            const pathData = `M 190 ${req.y} C 360 ${req.y}, 340 ${targetY}, 510 ${targetY}`;

            return (
              <g key={req.key}>
                {/* Standby background path */}
                <path
                  d={pathData}
                  stroke="#ffffff"
                  strokeOpacity="0.04"
                  strokeWidth="3"
                  fill="none"
                />
                {/* Active glowing path */}
                <motion.path
                  d={pathData}
                  stroke="url(#purpleGlow)"
                  strokeWidth="2"
                  filter="url(#shadow)"
                  fill="none"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                />
                {/* Animated dash signal traveling along the line */}
                <path
                  d={pathData}
                  stroke="#c084fc"
                  strokeWidth="2.5"
                  strokeDasharray="8 20"
                  fill="none"
                  style={{
                    animation: 'dash 4s linear infinite',
                  }}
                />
              </g>
            );
          })}

          {/* LEFT SIDE NODES: REQUEST TYPES */}
          {requestTypes.map((req) => {
            const model = getRuleModel(req.key);
            const isRouted = !!model;

            return (
              <g key={req.key} transform={`translate(20, ${req.y - 20})`}>
                <rect
                  width="170"
                  height="40"
                  rx="8"
                  fill="#0a0a0c"
                  stroke={isRouted ? '#8b5cf6' : '#262626'}
                  strokeWidth="1.5"
                  className="transition-colors duration-300"
                />
                {/* Glowing border if active */}
                {isRouted && (
                  <rect
                    width="170"
                    height="40"
                    rx="8"
                    fill="none"
                    stroke="#a78bfa"
                    strokeOpacity="0.5"
                    strokeWidth="1"
                    style={{ filter: 'drop-shadow(0px 0px 4px rgba(139,92,246,0.3))' }}
                  />
                )}
                <circle cx="20" cy="20" r="4" fill={isRouted ? '#a78bfa' : '#525252'} />
                <text x="35" y="24" fill="#d4d4d4" fontSize="11" fontWeight="bold" fontFamily="sans-serif">
                  {req.label}
                </text>
              </g>
            );
          })}

          {/* GATEWAY CENTRAL ROUTING DECORATOR OR NODE */}
          <g transform="translate(360, 160)">
            <circle cx="40" cy="30" r="35" fill="#000000" stroke="#8b5cf6" strokeWidth="2.5" />
            <circle cx="40" cy="30" r="40" fill="none" stroke="#a78bfa" strokeWidth="1" strokeDasharray="4 6" className="animate-spin" style={{ transformOrigin: '40px 30px', animationDuration: '10s' }} />
            <text x="40" y="27" fill="#ffffff" fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="sans-serif">AI</text>
            <text x="40" y="40" fill="#a78bfa" fontSize="8" fontWeight="bold" textAnchor="middle" fontFamily="sans-serif">ROUTER</text>
          </g>

          {/* RIGHT SIDE NODES: PROVIDERS */}
          {providers.map((prov) => {
            // Check if any rule targets this provider
            const activeRules = requestTypes.filter((req) => {
              const model = getRuleModel(req.key);
              return model && model.provider === prov.key;
            });
            const isActive = activeRules.length > 0;

            return (
              <g key={prov.key} transform={`translate(510, ${prov.y - 25})`}>
                <rect
                  width="180"
                  height="50"
                  rx="10"
                  fill="#0a0a0c"
                  stroke={isActive ? prov.color : '#262626'}
                  strokeWidth="1.5"
                />
                
                {/* Provider Bullet */}
                <circle cx="20" cy="25" r="5" fill={prov.color} />
                {isActive && (
                  <circle cx="20" cy="25" r="8" fill="none" stroke={prov.color} strokeWidth="1" className="animate-ping" style={{ animationDuration: '2s' }} />
                )}

                {/* Text Labels */}
                <text x="40" y="22" fill="#ffffff" fontSize="12" fontWeight="bold" fontFamily="sans-serif">
                  {prov.label}
                </text>
                <text x="40" y="37" fill="#737373" fontSize="9" fontFamily="sans-serif">
                  {isActive 
                    ? `${activeRules.length} route${activeRules.length > 1 ? 's' : ''} active` 
                    : 'Standby mode'}
                </text>
              </g>
            );
          })}
        </svg>

        {/* CSS Keyframe definition in React style tag */}
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes dash {
            to {
              stroke-dashoffset: -100;
            }
          }
        `}} />
      </div>

      {/* Connection Rules Summary List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-2">
        {requestTypes.map((req) => {
          const model = getRuleModel(req.key);
          return (
            <div key={req.key} className="p-3.5 rounded-xl border border-white/5 bg-neutral-950/40 flex items-center justify-between">
              <div className="flex flex-col">
                <span className="text-xs text-neutral-400 font-bold">{req.label}</span>
                <span className="text-[10px] text-neutral-500 font-mono mt-0.5">Type: {req.key}</span>
              </div>
              
              <div className="flex items-center gap-1">
                {model ? (
                  <>
                    <span className="text-xs text-violet-400 font-semibold font-mono">
                      {model.name}
                    </span>
                    <ArrowRight className="w-3 h-3 text-neutral-500" />
                    <span className="text-[9px] uppercase font-bold text-neutral-400 px-1.5 py-0.5 rounded border border-white/10 bg-neutral-900 font-mono">
                      {model.provider}
                    </span>
                  </>
                ) : (
                  <span className="text-[10px] text-neutral-600">No active rule</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
