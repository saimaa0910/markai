import * as React from 'react';
import { usePrompts } from '../hooks';
import { usePromptsStore } from '../store/prompts';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { 
  BookOpen, Search, Star, Trash2, Copy, Plus, 
  Grid, List, ChevronRight, Share2, MoreVertical, Archive, ArrowUpDown 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';

export function LibraryPage() {
  const { prompts, isLoading, deletePrompt, createPrompt } = usePrompts();
  const store = usePromptsStore();

  const [viewMode, setViewMode] = React.useState<'grid' | 'table'>('grid');
  const [selectedCategory, setSelectedCategory] = React.useState<string>('all');
  const [selectedDocs, setSelectedDocs] = React.useState<string[]>([]);

  // Filter lists
  const filteredPrompts = React.useMemo(() => {
    return prompts.filter((p: any) => {
      if (selectedCategory !== 'all' && p.category !== selectedCategory) return false;
      if (store.filters.search) {
        const query = store.filters.search.toLowerCase();
        return p.name.toLowerCase().includes(query) || p.content.toLowerCase().includes(query);
      }
      return true;
    });
  }, [prompts, selectedCategory, store.filters.search]);

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    toast.success('Prompt Copied', 'Prompt instruction payload copied to clipboard.');
  };

  const handleDelete = (name: string) => {
    deletePrompt.mutate(name, {
      onSuccess: () => {
        toast.success('Prompt Deleted', 'Prompt family removed from the registry.');
      },
    });
  };

  const handleToggleSelect = (name: string) => {
    setSelectedDocs((prev) =>
      prev.includes(name) ? prev.filter((x) => x !== name) : [...prev, name]
    );
  };

  const handleBulkAction = (action: 'favorite' | 'delete') => {
    if (selectedDocs.length === 0) return;
    
    selectedDocs.forEach((name) => {
      if (action === 'favorite') store.toggleFavorite(name);
      if (action === 'delete') deletePrompt.mutate(name);
    });

    toast.success('Bulk Actions Complete', `Successfully processed ${selectedDocs.length} prompts.`);
    setSelectedDocs([]);
  };

  const handleClone = (prompt: any) => {
    createPrompt.mutate({
      name: `${prompt.name}_copy`,
      content: prompt.content,
      category: prompt.category,
      tags: prompt.tags,
      is_shared: prompt.is_shared,
      version: 1,
    }, {
      onSuccess: () => {
        toast.success('Prompt Cloned', `Cloned prompt copy ${prompt.name}_copy created.`);
      }
    });
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Prompt Library"
        description="Browse registered prompt families, duplicate templates, and extract parameters."
        icon={<BookOpen className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Library catalog</Badge>}
        actions={
          <a href="/dashboard/prompts/editor">
            <Button variant="violet" size="sm" className="h-8 text-[11px]">
              <Plus className="w-3.5 h-3.5 mr-1" />
              New Prompt
            </Button>
          </a>
        }
      />

      {/* Query filters */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-neutral-950/20 border border-white/5 p-4 rounded-xl">
        <div className="flex items-center flex-wrap gap-2">
          {['all', 'Marketing', 'CRM', 'Ads'].map((cat) => (
            <Button
              key={cat}
              variant="outline"
              size="sm"
              onClick={() => setSelectedCategory(cat)}
              className={`h-8 text-[11px] border-white/5 capitalize ${
                selectedCategory === cat ? 'bg-violet-600 border-violet-500/20 text-white' : 'bg-neutral-900/50'
              }`}
            >
              {cat === 'all' ? 'All categories' : cat}
            </Button>
          ))}
        </div>

        <div className="flex items-center flex-wrap gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:flex-none min-w-[200px]">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-neutral-500" />
            <Input
              placeholder="Search templates..."
              value={store.filters.search}
              onChange={(e) => store.setFilters({ search: e.target.value })}
              className="pl-9 bg-neutral-950/40 border-white/5 h-8 text-[11px]"
            />
          </div>

          <div className="flex items-center rounded-lg bg-neutral-900 border border-white/5 p-0.5 text-neutral-400">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1 rounded transition-all cursor-pointer ${viewMode === 'grid' ? 'bg-violet-600 text-white' : ''}`}
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-1 rounded transition-all cursor-pointer ${viewMode === 'table' ? 'bg-violet-600 text-white' : ''}`}
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Bulk actionbar */}
      {selectedDocs.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-3 bg-violet-600/10 border border-violet-500/20 rounded-xl flex items-center justify-between gap-4"
        >
          <span className="text-[11px] text-neutral-300 font-semibold">
            {selectedDocs.length} templates selected:
          </span>
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={() => handleBulkAction('favorite')} className="h-7 text-[10px] bg-neutral-900 text-amber-400 border border-amber-500/10">
              Add to Favorites
            </Button>
            <Button size="sm" onClick={() => handleBulkAction('delete')} className="h-7 text-[10px] bg-rose-600 text-white hover:bg-rose-700">
              Delete Selected
            </Button>
          </div>
        </motion.div>
      )}

      {/* Library listings */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 bg-neutral-900/60 rounded-xl border border-white/5" />
          ))}
        </div>
      ) : sortedPromptsList(filteredPrompts, store.favorites).length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence mode="popLayout">
              {sortedPromptsList(filteredPrompts, store.favorites).map((p) => {
                const isSel = selectedDocs.includes(p.name);
                const isFavorite = store.favorites.includes(p.name);
                return (
                  <motion.div
                    key={p.name}
                    className={`relative p-5 rounded-xl border bg-neutral-950/40 hover:border-violet-500/20 transition-all group flex flex-col gap-3.5 ${
                      isSel ? 'border-violet-500' : 'border-white/5'
                    }`}
                  >
                    {/* Checkbox selector */}
                    <button 
                      onClick={() => handleToggleSelect(p.name)}
                      className={`absolute top-4 left-4 w-4 h-4 rounded border flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100 cursor-pointer ${
                        isSel ? 'bg-violet-600 border-violet-500 opacity-100' : 'border-white/20 bg-neutral-900'
                      }`}
                    >
                      {isSel && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </button>

                    <div className="flex items-start justify-between gap-3 pl-6">
                      <div className="flex flex-col min-w-0">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <a 
                            href={`/dashboard/prompts/${p.name}`}
                            className="text-xs font-bold text-white hover:text-violet-400 hover:underline truncate block"
                          >
                            {p.name}
                          </a>
                          <Badge variant="neutral" size="sm">v{p.version}</Badge>
                        </div>
                        <span className="text-[10px] text-neutral-500 mt-0.5">{p.category}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        <button 
                          onClick={() => store.toggleFavorite(p.name)}
                          className="p-1 hover:text-amber-400 cursor-pointer text-neutral-500"
                        >
                          <Star className={`w-3.5 h-3.5 ${isFavorite ? 'fill-amber-400 text-amber-400' : ''}`} />
                        </button>
                        <button 
                          onClick={() => handleCopy(p.content)}
                          className="p-1 hover:text-white cursor-pointer text-neutral-500"
                        >
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                        <button 
                          onClick={() => handleDelete(p.name)}
                          className="p-1 hover:text-rose-400 cursor-pointer text-neutral-500"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <p className="text-[11px] text-neutral-400 line-clamp-2 leading-relaxed font-mono">
                      {p.content}
                    </p>

                    {/* Variable chip badges */}
                    {p.variables.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {p.variables.map((v: any) => (
                          <span key={v} className="text-[8px] font-mono bg-violet-600/10 border border-violet-500/20 text-violet-300 px-1.5 py-0.5 rounded">
                            {`{{${v}}}`}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between pt-3 border-t border-white/5 text-[10px] text-neutral-500 mt-auto">
                      <div className="flex flex-wrap gap-1">
                        {p.tags?.map((t: any) => (
                          <Badge key={t} variant="neutral" size="sm">{t}</Badge>
                        ))}
                      </div>
                      <span className="font-mono">{new Date(p.created_at).toLocaleDateString()}</span>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        ) : (
          <div className="border border-white/5 bg-neutral-950/20 rounded-xl overflow-hidden text-xs">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/5 text-neutral-500 uppercase tracking-wider font-semibold font-mono text-[9px]">
                  <th className="p-3">Prompt Template Name</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Version</th>
                  <th className="p-3">Variables count</th>
                  <th className="p-3">Created At</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-neutral-300">
                {sortedPromptsList(filteredPrompts, store.favorites).map((p) => {
                  const isFavorite = store.favorites.includes(p.name);
                  return (
                    <tr key={p.name} className="hover:bg-neutral-900/10">
                      <td className="p-3">
                        <a href={`/dashboard/prompts/${p.name}`} className="font-semibold text-white hover:text-violet-400 hover:underline">
                          {p.name}
                        </a>
                      </td>
                      <td className="p-3 font-mono text-[10px]">{p.category}</td>
                      <td className="p-3 font-mono">v{p.version}</td>
                      <td className="p-3 font-mono">{p.variables.length} vars</td>
                      <td className="p-3 font-mono text-neutral-500">{new Date(p.created_at).toLocaleDateString()}</td>
                      <td className="p-3 text-right flex items-center justify-end gap-2">
                        <button onClick={() => store.toggleFavorite(p.name)} className="p-1 hover:text-amber-400">
                          <Star className={`w-3.5 h-3.5 ${isFavorite ? 'fill-amber-400 text-amber-400' : ''}`} />
                        </button>
                        <button onClick={() => handleClone(p)} className="p-1 hover:text-sky-400" title="Clone template">
                          <Share2 className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => handleDelete(p.name)} className="p-1 hover:text-rose-400">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      ) : (
        <Card className="py-20 flex flex-col items-center justify-center text-center gap-3">
          <BookOpen className="w-10 h-10 text-neutral-600" />
          <h4 className="font-bold text-white text-sm">No Prompts Found</h4>
          <p className="text-xs text-neutral-500">Add a new prompt template or import a template to start.</p>
        </Card>
      )}
    </div>
  );
}

// Utility sort helper
function sortedPromptsList(list: any[], favorites: string[]) {
  return [...list].sort((a, b) => {
    const aFav = favorites.includes(a.name) ? 1 : 0;
    const bFav = favorites.includes(b.name) ? 1 : 0;
    if (aFav !== bFav) return bFav - aFav;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}
export { Archive, ArrowUpDown, MoreVertical };
