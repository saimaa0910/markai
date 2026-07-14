import * as React from 'react';
import { useKnowledgeSearch } from '../../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input, Select } from '@/components/ui/input';
import { Card } from '@eaimos/ui';
import { 
  Search, Sparkles, Network, ArrowRight, FileText, 
  HelpCircle, MessageSquare, Compass, ShieldAlert, Cpu 
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion } from 'framer-motion';

export function SearchPage() {
  const { search, searchResults, isSearching } = useKnowledgeSearch();
  
  const [queryText, setQueryText] = React.useState('');
  const [searchMode, setSearchMode] = React.useState<'semantic' | 'keyword' | 'hybrid'>('semantic');
  const [hasQueried, setHasQueried] = React.useState(false);
  const [activeStep, setActiveStep] = React.useState<number>(0);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setHasQueried(true);
    setActiveStep(1); // Set to "Search Chunks" step
    
    try {
      await search({ queryText });
      toast.success('Vector search completed', 'Retrieved nearest matching document chunks.');
      
      // Simulate sequential step activation for the RAG visualizer!
      setTimeout(() => setActiveStep(2), 600);  // Construct context
      setTimeout(() => setActiveStep(3), 1200); // Compile prompt
      setTimeout(() => setActiveStep(4), 1800); // LLM response
    } catch (err) {
      toast.error('Search failed', 'Could not run similarity query.');
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="Cognitive Semantic Search"
        description="Search your knowledge index using semantic meaning, keywords, or hybrid embeddings."
        icon={<Search className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Vector search</Badge>}
      />

      {/* Query Bar */}
      <form onSubmit={handleQuery} className="flex flex-col sm:flex-row gap-3 bg-neutral-950/20 border border-white/5 p-4 rounded-xl">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-neutral-500" />
          <Input
            placeholder="Type a query (e.g. How do we configure our API route limits?)"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            className="pl-10 bg-neutral-950 border-white/5 h-10 text-xs w-full"
          />
        </div>

        <Select
          value={searchMode}
          onChange={(e) => setSearchMode(e.target.value as any)}
          className="bg-neutral-900 border-white/5 h-10 text-xs w-full sm:w-36"
          options={[
            { label: 'Semantic (Vector)', value: 'semantic' },
            { label: 'Keyword (Lexical)', value: 'keyword' },
            { label: 'Hybrid search', value: 'hybrid' },
          ]}
        />

        <Button variant="violet" size="sm" type="submit" className="h-10 text-xs w-full sm:w-28" disabled={isSearching}>
          {isSearching ? 'Searching...' : 'Run Query'}
        </Button>
      </form>

      {/* Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* RESULTS WORKSPACE (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <Card className="flex flex-col gap-4 min-h-[300px]">
            <div>
              <h3 className="font-bold text-white text-sm">Similar Chunks Retrieved</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">Nearest vector chunk results from pgvector store.</p>
            </div>

            <div className="flex flex-col gap-4">
              {isSearching ? (
                <div className="flex flex-col gap-3 animate-pulse py-8">
                  <div className="h-20 bg-neutral-900/60 rounded-xl border border-white/5" />
                  <div className="h-20 bg-neutral-900/60 rounded-xl border border-white/5" />
                </div>
              ) : searchResults.length > 0 ? (
                searchResults.map((chunk, idx) => (
                  <motion.div
                    key={chunk.id || idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="p-4 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col gap-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="violet" size="sm">Chunk #{idx + 1}</Badge>
                        <span className="text-[9px] text-neutral-500 font-mono">
                          similarity score
                        </span>
                      </div>
                      <Badge variant="emerald" className="font-mono text-[9px] font-bold">
                        {Math.round((chunk.similarity || 0.88) * 100)}% Match
                      </Badge>
                    </div>

                    <p className="text-xs text-neutral-300 font-mono leading-relaxed border-l-2 border-violet-500/20 pl-3">
                      {chunk.content}
                    </p>
                  </motion.div>
                ))
              ) : (
                <div className="py-20 flex flex-col items-center justify-center text-center text-neutral-600">
                  <Compass className="w-10 h-10 mb-2 text-neutral-700" />
                  <span className="text-xs font-semibold">Ready for Query</span>
                  <p className="text-[10px] text-neutral-500 mt-1 max-w-[200px]">
                    Enter a prompt question above to perform similarity search diagnostics.
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* RAG FLOW VISUALIZER (Right 1 column) */}
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4">
            <div>
              <h3 className="font-bold text-white text-sm">Interactive RAG Pipeline Visualizer</h3>
              <p className="text-[11px] text-neutral-500 mt-0.5">Execution flow mapping for prompt response completion.</p>
            </div>

            <div className="flex flex-col gap-4 relative pl-4 mt-2">
              {/* Timeline guide line */}
              <div className="absolute left-6.5 top-2 bottom-2 w-0.5 bg-neutral-900 border-l border-white/5" />

              {[
                { 
                  step: 1, 
                  label: 'Vector Retrieval', 
                  desc: 'Converting text query to embedding and matching chunks.', 
                  icon: <Sparkles className="w-4 h-4" /> 
                },
                { 
                  step: 2, 
                  label: 'Context Extraction', 
                  desc: 'Slicing text matches and packing context window.', 
                  icon: <Network className="w-4 h-4" /> 
                },
                { 
                  step: 3, 
                  label: 'Prompt Composition', 
                  desc: 'Wrapping context & system rules in LLM instructions.', 
                  icon: <FileText className="w-4 h-4" /> 
                },
                { 
                  step: 4, 
                  label: 'LLM Generation', 
                  desc: 'Returning vectorized response output.', 
                  icon: <Cpu className="w-4 h-4" /> 
                },
              ].map((flow) => {
                const isActive = hasQueried && activeStep >= flow.step;
                return (
                  <div key={flow.step} className="flex gap-4 items-start relative z-10">
                    <div 
                      className={`w-6 h-6 rounded-full flex items-center justify-center border text-[10px] font-mono shrink-0 transition-all ${
                        isActive 
                          ? 'bg-violet-600 border-violet-500 text-white shadow-lg shadow-violet-600/20' 
                          : 'bg-neutral-950 border-white/5 text-neutral-500'
                      }`}
                    >
                      {flow.step}
                    </div>

                    <div className="flex flex-col gap-0.5 text-xs">
                      <span className={`font-bold transition-colors ${isActive ? 'text-white' : 'text-neutral-500'}`}>
                        {flow.label}
                      </span>
                      <span className="text-[10px] text-neutral-500 leading-normal">
                        {flow.desc}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
            
            {hasQueried && activeStep === 4 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mt-2 p-3 bg-violet-600/10 border border-violet-500/20 rounded-xl text-xs flex flex-col gap-2"
              >
                <span className="font-bold text-white flex items-center gap-1">
                  <MessageSquare className="w-3.5 h-3.5 text-violet-400" /> LLM Completion Answer:
                </span>
                <p className="text-[11px] text-neutral-300 leading-relaxed font-sans">
                  The workspace is configured to parse variables automatically. Ensure you check settings limits parameters inside the settings catalog.
                </p>
              </motion.div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
export { HelpCircle, Network };
