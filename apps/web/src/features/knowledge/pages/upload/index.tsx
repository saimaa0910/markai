import * as React from 'react';
import { useUpload, useQueueJobs } from '../../hooks';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@eaimos/ui';
import { useDropzone } from 'react-dropzone';
import { 
  UploadCloud, FileText, CheckCircle2, Clock, 
  AlertTriangle, Trash2, ArrowLeft, RefreshCw, XCircle,
  Play, Shield, FileSearch, Layers, Database
} from 'lucide-react';
import { toast } from '@/components/ui/toast';
import { motion, AnimatePresence } from 'framer-motion';

export function UploadPage() {
  const { uploadQueue, clearQueue, uploadBatch, isPending } = useUpload();
  const { jobs, cancelJob, retryJob } = useQueueJobs();

  const onDrop = React.useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      toast.success('Queue processing started', `Injecting ${acceptedFiles.length} files to vectorizer index.`);
      await uploadBatch(acceptedFiles);
    },
    [uploadBatch]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/json': ['.json'],
      'text/csv': ['.csv'],
      'text/markdown': ['.md'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxSize: 15 * 1024 * 1024, // 15MB max file limits
  });

  const getStepIcon = (step: string) => {
    switch (step) {
      case 'VIRUS_SCAN': return <Shield className="w-3.5 h-3.5 text-blue-400" />;
      case 'OCR':
      case 'EXTRACT_TEXT': return <FileSearch className="w-3.5 h-3.5 text-amber-400" />;
      case 'CHUNK': return <Layers className="w-3.5 h-3.5 text-pink-400" />;
      case 'EMBEDDING':
      case 'VECTOR_STORE': return <Database className="w-3.5 h-3.5 text-violet-400" />;
      default: return <FileText className="w-3.5 h-3.5" />;
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto pb-12">
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-white transition-colors">
        <a href="/dashboard/knowledge" className="inline-flex items-center gap-1.5">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </a>
      </div>

      <PageHeader
        title="Ingestion Upload Center"
        description="Drag-and-drop local resource files to generate vector chunk indices automatically."
        icon={<UploadCloud className="w-5 h-5 text-violet-400" />}
        badge={<Badge variant="violet">Ingestion node</Badge>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* DRAG-DROP UPLOAD ZONE (Left 2 columns) */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center text-center gap-4 transition-all cursor-pointer ${
              isDragActive
                ? 'border-violet-500 bg-violet-500/5'
                : 'border-white/5 bg-neutral-950/20 hover:border-white/10'
            }`}
          >
            <input {...getInputProps()} />
            
            <div className="p-4 rounded-full bg-neutral-900 border border-white/5 text-violet-400">
              <UploadCloud className="w-8 h-8 animate-bounce" />
            </div>

            <div className="flex flex-col gap-1">
              <h3 className="text-sm font-bold text-white">
                {isDragActive ? 'Drop your resources here' : 'Drag & drop document files here'}
              </h3>
              <p className="text-[11px] text-neutral-500">
                Supports PDF, DOCX, TXT, CSV, JSON, and Markdown formats (Up to 15MB limit).
              </p>
            </div>

            <Button variant="violet" size="sm" type="button" className="h-8 text-[11px]">
              Select Files
            </Button>
          </div>

          {/* Active Backend Celery Ingestion Jobs */}
          <Card className="flex flex-col gap-4">
            <div>
              <h4 className="font-bold text-white text-sm">Background Workers Ingestion Queue (Celery Cluster)</h4>
              <p className="text-[11px] text-neutral-500 mt-0.5 font-medium">
                Distributed job steps: scanning, parsing, OCR extracting, indexing.
              </p>
            </div>

            <div className="flex flex-col gap-3">
              {jobs.map((job) => {
                const isRunning = job.status === 'RUNNING';
                const isFailed = job.status === 'FAILED';
                const isCompleted = job.status === 'COMPLETED';

                return (
                  <div key={job.id} className="p-4 rounded-xl border border-white/5 bg-neutral-950/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-3.5 min-w-[200px]">
                      <div className="p-2.5 rounded-lg bg-neutral-950 border border-white/5 shrink-0">
                        {getStepIcon(job.step)}
                      </div>
                      <div className="flex flex-col gap-0.5 text-xs truncate">
                        <span className="font-bold text-white truncate">Job #{job.id.slice(0, 8)}</span>
                        <span className="text-[10px] text-neutral-500 font-mono">Stage: {job.step}</span>
                      </div>
                    </div>

                    <div className="flex-1 flex flex-col gap-1.5 max-w-[250px]">
                      <div className="flex items-center justify-between text-[10px] font-mono text-neutral-500">
                        <span>Progress</span>
                        <span>{Math.round(job.progress)}%</span>
                      </div>
                      <div className="w-full bg-neutral-950 border border-white/5 h-2 rounded-full overflow-hidden">
                        <motion.div 
                          className={`h-full ${isFailed ? 'bg-rose-500' : isCompleted ? 'bg-emerald-500' : 'bg-violet-600'}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${job.progress}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge variant={isCompleted ? 'emerald' : isFailed ? 'rose' : isRunning ? 'violet' : 'amber'} className="font-mono text-[9px] uppercase">
                        {job.status}
                      </Badge>

                      {isRunning && (
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => cancelJob.mutate(job.id)}
                          className="h-7 text-[10px] border-white/5 hover:text-rose-400"
                        >
                          Cancel
                        </Button>
                      )}

                      {isFailed && (
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => retryJob.mutate(job.id)}
                          className="h-7 text-[10px] border-white/5 hover:text-violet-400"
                        >
                          Retry
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}

              {jobs.length === 0 && (
                <div className="py-12 flex flex-col items-center justify-center text-center text-neutral-600 border border-dashed border-white/5 rounded-xl">
                  <Clock className="w-6 h-6 mb-2 text-neutral-700" />
                  <span className="text-[11px] font-semibold">No active background celery jobs</span>
                  <p className="text-[9px] text-neutral-500 mt-0.5">
                    Newly uploaded files will spawn distributed workers tasks here.
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* UPLOAD QUEUE & HISTORY (Right 1 column) */}
        <div className="flex flex-col gap-4">
          <Card className="flex flex-col gap-4 min-h-[300px]">
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div>
                <h4 className="font-bold text-white text-sm">Upload Queue</h4>
                <p className="text-[10px] text-neutral-500 mt-0.5">Active files processing status</p>
              </div>

              {uploadQueue.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearQueue}
                  className="h-7 text-[10px] border-white/5 hover:text-rose-400"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1" />
                  Clear Queue
                </Button>
              )}
            </div>

            <div className="flex flex-col gap-3 flex-1 overflow-y-auto max-h-[400px]">
              {uploadQueue.map((item) => {
                const isCompleted = item.status === 'completed';
                const isFailed = item.status === 'failed';
                const isUploading = item.status === 'uploading';

                return (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl border border-white/5 bg-neutral-950/40 flex flex-col gap-2.5 text-xs"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2 truncate">
                        <FileText className="w-3.5 h-3.5 text-violet-400 shrink-0" />
                        <span className="text-white font-semibold truncate" title={item.name}>
                          {item.name}
                        </span>
                      </div>
                      
                      {isCompleted && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                      {isFailed && <XCircle className="w-4 h-4 text-rose-400 shrink-0" />}
                      {isUploading && <RefreshCw className="w-3.5 h-3.5 text-violet-400 animate-spin shrink-0" />}
                      {item.status === 'pending' && <Clock className="w-3.5 h-3.5 text-neutral-500 shrink-0" />}
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-neutral-500">
                      <span>{(item.size / 1024).toFixed(1)} KB</span>
                      <span className="capitalize font-medium">{item.status}</span>
                    </div>

                    {isUploading && (
                      <div className="w-full bg-neutral-900 border border-white/5 h-1.5 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-violet-600 rounded-full"
                          initial={{ width: 0 }}
                          animate={{ width: `${item.progress}%` }}
                          transition={{ duration: 0.2 }}
                        />
                      </div>
                    )}
                  </div>
                );
              })}

              {uploadQueue.length === 0 && (
                <div className="py-20 flex flex-col items-center justify-center text-center text-neutral-600">
                  <UploadCloud className="w-8 h-8 mb-2 text-neutral-700" />
                  <span className="text-xs font-semibold">Queue is empty</span>
                  <p className="text-[10px] text-neutral-500 mt-1 max-w-[180px]">
                    Drag and drop file resources to check queue pipelines.
                  </p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
export { useDropzone };

