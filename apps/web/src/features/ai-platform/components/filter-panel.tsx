import * as React from 'react';
import { useAIPlatformStore } from '../store/ai-platform';
import { Input, Select } from '@/components/ui/input';
import { useProviders, useModels } from '../hooks';
import { Search, Calendar, RefreshCw, Cpu, Layers } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface FilterPanelProps {
  showModelSelector?: boolean;
  onRefresh?: () => void;
}

export function FilterPanel({ showModelSelector = true, onRefresh }: FilterPanelProps) {
  const { 
    selectedProvider, setSelectedProvider,
    selectedModel, setSelectedModel,
    searchQuery, setSearchQuery,
    timeRange, setTimeRange,
    viewPreference, setViewPreference
  } = useAIPlatformStore();

  const { providers } = useProviders();
  const { models } = useModels();

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedProvider(val === 'all' ? null : val);
    setSelectedModel(null); // Reset model selection when provider changes
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedModel(val === 'all' ? null : val);
  };

  const filteredModels = React.useMemo(() => {
    if (!selectedProvider) return models;
    return models.filter((m) => m.provider === selectedProvider);
  }, [models, selectedProvider]);

  return (
    <div className="glass rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
      {/* Search and Filters */}
      <div className="flex flex-1 flex-wrap items-center gap-3">
        {/* Search Input */}
        <div className="relative min-w-[200px] flex-1 md:flex-none">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-neutral-500" />
          <Input
            placeholder="Search registry..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-neutral-950/40 border-white/5 h-9 text-xs text-white"
          />
        </div>

        {/* Provider Dropdown */}
        <div className="relative min-w-[150px]">
          <Select 
            value={selectedProvider || 'all'} 
            onChange={handleProviderChange}
            className="bg-neutral-950/40 border-white/5 h-9 text-xs text-white"
            options={[
              { label: 'All Providers', value: 'all' },
              ...providers.map((p) => ({ label: p.name.toUpperCase(), value: p.name.toLowerCase() }))
            ]}
          />
        </div>

        {/* Model Dropdown */}
        {showModelSelector && (
          <div className="relative min-w-[180px]">
            <Select 
              value={selectedModel || 'all'} 
              onChange={handleModelChange}
              className="bg-neutral-950/40 border-white/5 h-9 text-xs text-white"
              disabled={filteredModels.length === 0}
              options={[
                { label: 'All Models', value: 'all' },
                ...filteredModels.map((m) => ({ label: `${m.name} (${m.provider})`, value: m.model_name }))
              ]}
            />
          </div>
        )}
      </div>

      {/* Preferences & Sync Actions */}
      <div className="flex items-center gap-3 shrink-0 self-end md:self-auto">
        {/* Time range triggers */}
        <div className="flex items-center rounded-lg bg-neutral-900 border border-white/5 p-1 text-[10px]">
          {(['24h', '7d', '30d'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setTimeRange(r)}
              className={`px-2.5 py-1 rounded font-semibold transition-all cursor-pointer ${
                timeRange === r ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
              }`}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>

        {/* View preferences grid vs table */}
        <div className="flex items-center rounded-lg bg-neutral-900 border border-white/5 p-1 text-[10px]">
          {(['grid', 'table'] as const).map((pref) => (
            <button
              key={pref}
              onClick={() => setViewPreference(pref)}
              className={`px-2.5 py-1 rounded font-semibold transition-all capitalize cursor-pointer ${
                viewPreference === pref ? 'bg-violet-600 text-white' : 'text-neutral-400 hover:text-white'
              }`}
            >
              {pref}
            </button>
          ))}
        </div>

        {onRefresh && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            className="h-9 px-3 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}
