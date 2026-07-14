import * as React from 'react';
import { useRouting, useModels } from '../hooks';
import { RoutingDiagram } from '../components/routing-diagram';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DataTable, DataTableColumn } from '@/components/ui/data-table';
import { Input, Select } from '@/components/ui/input';
import { Dialog } from '@/components/ui/dialog';
import { toast } from '@/components/ui/toast';
import { Router, Plus, Trash2, ArrowRight, ShieldCheck, ShieldAlert, Activity, RefreshCw } from 'lucide-react';

export function RouterPage() {
  const { rules, isLoading: loadingRules, refetch: refetchRules, createRule, updateRule, deleteRule } = useRouting();
  const { models } = useModels();

  const [showCreate, setShowCreate] = React.useState(false);
  const [form, setForm] = React.useState({
    request_type: 'chat',
    model_registry_id: '',
    is_active: true,
  });

  // Pre-fill model selection when models are loaded
  React.useEffect(() => {
    if (models.length > 0 && !form.model_registry_id) {
      setForm((prev) => ({ ...prev, model_registry_id: models[0].id }));
    }
  }, [models, form.model_registry_id]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.model_registry_id) {
      toast.error('Required', 'Please select a target model.');
      return;
    }

    try {
      await createRule.mutateAsync({
        request_type: form.request_type as any,
        model_registry_id: form.model_registry_id,
        is_active: form.is_active,
      });
      setShowCreate(false);
      toast.success('Routing Rule Active', `Incoming ${form.request_type} requests will now route dynamically.`);
    } catch (e) {
      toast.error('Rule Failed', 'An error occurred during rule compilation.');
    }
  };

  const handleDelete = (id: string) => {
    deleteRule.mutate(id, {
      onSuccess: () => toast.success('Rule Removed', 'Dynamic router table updated.')
    });
  };

  const handleToggle = (id: string, active: boolean) => {
    updateRule.mutate({ ruleId: id, updates: { is_active: !active } }, {
      onSuccess: () => toast.success('Rule Updated', 'Target rule active status toggled.')
    });
  };

  const getModelName = (id: string) => {
    const m = models.find((m) => m.id === id);
    return m ? `${m.name} (${m.provider})` : id.slice(0, 8) + '...';
  };

  const columns: DataTableColumn<any>[] = [
    {
      key: 'request_type',
      label: 'Request Category',
      sortable: true,
      render: (row) => (
        <Badge variant="violet" className="font-mono text-[10px] uppercase">
          {row.request_type}
        </Badge>
      ),
    },
    {
      key: 'model_registry_id',
      label: 'Target Gateway Model',
      render: (row) => (
        <span className="text-xs text-white font-semibold font-mono">
          {getModelName(row.model_registry_id)}
        </span>
      ),
    },
    {
      key: 'organization_id',
      label: 'Tenant Scope',
      render: (row) => (
        <Badge variant={row.organization_id ? 'amber' : 'sky'} size="sm">
          {row.organization_id ? 'Tenant Override' : 'Global Default'}
        </Badge>
      ),
    },
    {
      key: 'is_active',
      label: 'Health Check State',
      render: (row) => (
        <div className="flex items-center gap-1.5 text-xs text-neutral-300">
          {row.is_active ? (
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          ) : (
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          )}
          <span>{row.is_active ? 'Routing traffic' : 'Standby mode'}</span>
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Dynamic Router"
        description="Visualize and orchestrate automated model fallback chains, latency routing priorities, and tenant-scoped routing rules."
        icon={<Router className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">{rules.length} Active Rules</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="violet"
              size="sm"
              onClick={() => setShowCreate(true)}
              className="h-9 text-[11px]"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              Configure Custom Route
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchRules()}
              className="h-9 border-white/5 bg-neutral-900/50 hover:bg-neutral-900"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
          </div>
        }
      />

      {/* Visually stunning SVG routing diagram flow map */}
      <RoutingDiagram rules={rules} models={models} />

      {/* Rules list data table */}
      <div className="flex flex-col gap-4">
        <div>
          <h3 className="font-bold text-white text-sm">Active Rules Registry</h3>
          <p className="text-[11px] text-neutral-500 mt-0.5">Rules are processed top-down. Local tenant overrides supersede system defaults.</p>
        </div>

        <div className="rounded-xl border border-white/5 overflow-hidden">
          <DataTable
            columns={columns}
            data={rules}
            isLoading={loadingRules}
            pageSize={5}
            searchable={false}
            actions={(row) => (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleToggle(row.id, row.is_active)}
                  className={`h-7 text-[10px] ${row.is_active ? 'text-neutral-400' : 'text-emerald-400'}`}
                >
                  {row.is_active ? 'Deactivate' : 'Activate'}
                </Button>
                
                {/* Prevent deleting global system defaults */}
                {row.organization_id && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(row.id)}
                    className="h-7 text-[10px] text-rose-400 border-rose-500/10 hover:bg-rose-500/10"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                )}
              </div>
            )}
          />
        </div>
      </div>

      {/* Creation Dialog */}
      <Dialog 
        isOpen={showCreate} 
        onClose={() => setShowCreate(false)}
        title="Configure Custom Routing Rule"
      >
        <form onSubmit={handleCreate} className="flex flex-col gap-4 mt-2">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-neutral-400 font-semibold">Request Category</label>
            <Select
              value={form.request_type}
              onChange={(e) => setForm((prev) => ({ ...prev, request_type: e.target.value }))}
              className="bg-neutral-900 border-white/5 h-9 text-xs"
              options={[
                { label: 'Chat / Assistant', value: 'chat' },
                { label: 'Marketing Copy / Text Variants', value: 'content' },
                { label: 'Vision / OCR / Images Input', value: 'vision' },
                { label: 'Vector Embeddings', value: 'embeddings' },
                { label: 'Structured JSON Output', value: 'json' },
              ]}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-neutral-400 font-semibold">Target AI Model</label>
            <Select
              value={form.model_registry_id}
              onChange={(e) => setForm((prev) => ({ ...prev, model_registry_id: e.target.value }))}
              className="bg-neutral-900 border-white/5 h-9 text-xs"
              options={models.map((m) => ({
                label: `${m.name} (${m.provider} - ${m.model_name})`,
                value: m.id
              }))}
            />
          </div>

          <div className="flex items-center gap-2 mt-2">
            <input
              type="checkbox"
              id="is_active"
              checked={form.is_active}
              onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.checked }))}
              className="rounded border-white/5 bg-neutral-900 w-4 h-4 accent-violet-600"
            />
            <label htmlFor="is_active" className="text-xs text-neutral-300">
              Activate rule immediately upon seeding
            </label>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-white/5 pt-4 mt-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowCreate(false)}
              className="text-xs border-white/5"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="violet"
              size="sm"
              className="text-xs"
              disabled={createRule.isPending}
            >
              Commit Rule
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
