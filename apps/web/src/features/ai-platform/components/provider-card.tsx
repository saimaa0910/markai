import * as React from 'react';
import { motion } from 'framer-motion';
import { 
  Cpu, CheckCircle2, XCircle, Zap, Shield, HelpCircle, 
  Activity, DollarSign, RefreshCw, Radio, Terminal, Settings2 
} from 'lucide-react';
import { AIProvider } from '../types';
import { HealthBadge } from './badges';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { toast } from '@/components/ui/toast';
import { useProviderHealth } from '../hooks';

interface ProviderCardProps {
  provider: AIProvider;
  delay: number;
}

// Icon mapper for provider logos
const PROVIDER_ICONS: Record<string, React.ReactNode> = {
  openai: <Cpu className="w-5 h-5 text-emerald-400" />,
  groq: <Zap className="w-5 h-5 text-amber-400" />,
  anthropic: <Shield className="w-5 h-5 text-rose-400" />,
  google: <Radio className="w-5 h-5 text-sky-400" />,
  openrouter: <Terminal className="w-5 h-5 text-violet-400" />,
};

const PROVIDER_THEMES: Record<string, string> = {
  openai: 'hover:border-emerald-500/30 shadow-emerald-950/5',
  groq: 'hover:border-amber-500/30 shadow-amber-950/5',
  anthropic: 'hover:border-rose-500/30 shadow-rose-950/5',
  google: 'hover:border-sky-500/30 shadow-sky-950/5',
  openrouter: 'hover:border-violet-500/30 shadow-violet-950/5',
};

export function ProviderCard({ provider, delay }: ProviderCardProps) {
  const { testConnection } = useProviderHealth();
  const [isEnabled, setIsEnabled] = React.useState(provider.isHealthy);
  const [localLatency, setLocalLatency] = React.useState(provider.latency);

  const themeClass = PROVIDER_THEMES[provider.key] || 'hover:border-white/20';

  const handleTestConnection = async () => {
    const toastId = toast.loading(`Testing latency ping to ${provider.name}...`);
    try {
      const data = await testConnection.mutateAsync(provider.key);
      setLocalLatency(parseFloat((data.latency / 1000).toFixed(2)));
      toast.dismiss(toastId);
      toast.success('Connection Successful', `Latency: ${data.latency}ms`);
    } catch (e) {
      toast.dismiss(toastId);
      toast.error('Connection Failed', 'Please verify API configuration.');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className={`glass rounded-2xl p-5 flex flex-col gap-4 transition-all duration-300 relative group shadow-lg ${themeClass}`}
    >
      {/* Top Details */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-neutral-900/80 border border-white/5 flex items-center justify-center">
            {PROVIDER_ICONS[provider.key] || <Cpu className="w-5 h-5 text-neutral-400" />}
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">{provider.name}</h3>
            <span className="text-[10px] text-neutral-400 capitalize">{provider.key} gateway</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <HealthBadge isHealthy={isEnabled && provider.isHealthy} statusLabel={isEnabled ? undefined : 'Disabled'} />
          <Badge variant={isEnabled ? 'emerald' : 'neutral'} size="sm">
            {isEnabled ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-0.5">
          <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Zap className="w-3 h-3 text-neutral-600" /> Latency
          </span>
          <span className="text-xs font-mono font-bold text-white">
            {localLatency}s
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-0.5">
          <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Settings2 className="w-3 h-3 text-neutral-600" /> Priority
          </span>
          <span className="text-xs font-mono font-bold text-white">
            #{provider.priority}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-0.5">
          <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <Activity className="w-3 h-3 text-neutral-600" /> Requests
          </span>
          <span className="text-xs font-mono font-bold text-white">
            {provider.currentRequests} active
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-neutral-950/40 border border-white/5 flex flex-col gap-0.5">
          <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider flex items-center gap-1">
            <DollarSign className="w-3 h-3 text-neutral-600" /> Cost log
          </span>
          <span className="text-xs font-mono font-bold text-emerald-400">
            ${provider.cost}
          </span>
        </div>
      </div>

      {/* Capabilities */}
      <div className="flex flex-col gap-2">
        <span className="text-[10px] text-neutral-500 font-semibold">Capabilities</span>
        <div className="flex flex-wrap gap-1.5">
          <Badge variant={provider.supportsStreaming ? 'violet' : 'neutral'} size="sm">
            Streaming
          </Badge>
          <Badge variant={provider.supportsVision ? 'violet' : 'neutral'} size="sm">
            Vision
          </Badge>
          <Badge variant={provider.supportsJson ? 'violet' : 'neutral'} size="sm">
            JSON Output
          </Badge>
          <Badge variant={provider.supportsToolCalling ? 'violet' : 'neutral'} size="sm">
            Tool Calling
          </Badge>
        </div>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between text-[10px] text-neutral-500 border-t border-white/5 pt-3">
        <span>Context size: <b className="text-neutral-300">{(provider.contextWindow / 1000).toFixed(0)}k</b></span>
        <span>Last Ping: <span className="font-mono">{provider.lastSync}</span></span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 border-t border-white/5 pt-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => window.location.href = `/dashboard/ai/providers/${provider.key}`}
          className="text-[11px] h-8 px-2.5 border-white/5 text-neutral-300 hover:text-white bg-neutral-900/50 hover:bg-neutral-900"
        >
          Details
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleTestConnection}
          className="flex-1 text-[11px] h-8 bg-neutral-900/50 hover:bg-neutral-900 border-white/5"
          disabled={testConnection.isPending}
        >
          <RefreshCw className={`w-3 h-3 mr-1 ${testConnection.isPending ? 'animate-spin' : ''}`} />
          Test Connection
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setIsEnabled(!isEnabled);
            toast.success(
              isEnabled ? 'Provider Suspended' : 'Provider Activated', 
              `${provider.name} is now ${isEnabled ? 'ignored' : 'leveraged'} for LLM routing.`
            );
          }}
          className={`text-[11px] h-8 px-3 border-white/5 ${
            isEnabled 
              ? 'text-rose-400 hover:bg-rose-500/10' 
              : 'text-emerald-400 hover:bg-emerald-500/10'
          }`}
        >
          {isEnabled ? 'Disable' : 'Enable'}
        </Button>
      </div>
    </motion.div>
  );
}
