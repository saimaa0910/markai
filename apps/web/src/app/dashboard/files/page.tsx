'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/services/api-client';
import { PageHeader } from '@/components/ui/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { EmptyState } from '@/components/ui/empty-state';
import { StatCard } from '@/components/ui/stat-card';
import { toast } from '@/components/ui/toast';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FolderOpen, UploadCloud, Trash2, Download, Eye, Search,
  FileText, FileImage, FileVideo, FileCode, File as FileIcon, Clock
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// Types & helpers
// ─────────────────────────────────────────────────────────────────────────────
interface FileRecord {
  id: string;
  filename: string;
  file_type: string;
  mime_type?: string;
  file_size: number;
  storage_url?: string;
  created_at: string;
  organization_id?: string;
}

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return <FileImage className="w-5 h-5 text-sky-400" />;
  if (['mp4', 'webm', 'mov'].includes(ext)) return <FileVideo className="w-5 h-5 text-rose-400" />;
  if (['pdf', 'doc', 'docx', 'txt', 'md'].includes(ext)) return <FileText className="w-5 h-5 text-amber-400" />;
  if (['json', 'ts', 'tsx', 'js', 'py', 'sql'].includes(ext)) return <FileCode className="w-5 h-5 text-emerald-400" />;
  return <FileIcon className="w-5 h-5 text-neutral-400" />;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

// ─────────────────────────────────────────────────────────────────────────────
// File Card
// ─────────────────────────────────────────────────────────────────────────────
function FileCard({ file, onDelete, viewMode }: {
  file: FileRecord;
  onDelete: () => void;
  viewMode: 'grid' | 'list';
}) {
  if (viewMode === 'list') {
    return (
      <motion.div
        layout
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-neutral-950/20 hover:border-violet-500/20 transition-all group"
      >
        <div className="shrink-0">{getFileIcon(file.filename)}</div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-white truncate">{file.filename}</p>
          <p className="text-[10px] text-neutral-500">{formatBytes(file.file_size)} · {new Date(file.created_at).toLocaleDateString()}</p>
        </div>
        <Badge variant="neutral" size="sm">{file.file_type}</Badge>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {file.storage_url && (
            <a href={file.storage_url} target="_blank" rel="noopener noreferrer">
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                <Download className="w-3.5 h-3.5" />
              </Button>
            </a>
          )}
          <Button variant="ghost" size="sm" onClick={onDelete} className="h-7 w-7 p-0 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10">
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-xl border border-white/5 bg-neutral-950/40 p-4 flex flex-col gap-3 hover:border-violet-500/20 transition-all group"
    >
      {/* Preview area */}
      <div className="h-24 rounded-lg bg-neutral-900/60 border border-white/5 flex items-center justify-center">
        {getFileIcon(file.filename)}
      </div>

      <div className="flex flex-col gap-1">
        <p className="text-xs font-semibold text-white truncate" title={file.filename}>{file.filename}</p>
        <div className="flex items-center gap-1.5">
          <Badge variant="neutral" size="sm">{file.file_type || file.filename.split('.').pop()?.toUpperCase()}</Badge>
          <span className="text-[10px] text-neutral-500">{formatBytes(file.file_size)}</span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <div className="flex items-center gap-1 text-[10px] text-neutral-600">
          <Clock className="w-2.5 h-2.5" />
          {new Date(file.created_at).toLocaleDateString()}
        </div>
        <div className="flex items-center gap-1">
          {file.storage_url && (
            <a href={file.storage_url} target="_blank" rel="noopener noreferrer">
              <Button variant="ghost" size="sm" className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100">
                <Eye className="w-3.5 h-3.5" />
              </Button>
            </a>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onDelete}
            className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────
export default function FilesPage() {
  const { activeOrg } = useAuthStore();
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = React.useState('');
  const [viewMode, setViewMode] = React.useState<'grid' | 'list'>('grid');
  const [activeType, setActiveType] = React.useState('all');

  // ── Queries ──────────────────────────────────────────────────────────────
  const { data: files = [], isLoading } = useQuery({
    queryKey: ['files', activeOrg?.id],
    queryFn: async () => {
      const res = await apiClient.get('/files/');
      return res.data || [];
    },
    enabled: !!activeOrg,
  });

  // ── Upload ────────────────────────────────────────────────────────────────
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.post('/files/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      toast.success('Uploaded', 'File uploaded successfully.');
    },
    onError: () => toast.error('Upload Failed', 'Could not upload file.'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/files/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] });
      toast.success('Deleted', 'File removed.');
    },
  });

  const onDrop = React.useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((f) => uploadMutation.mutate(f));
  }, [uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  // ── Derived ───────────────────────────────────────────────────────────────
  const types = ['all', ...new Set((files as FileRecord[]).map((f) => {
    const ext = f.filename.split('.').pop()?.toLowerCase() ?? '';
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return 'images';
    if (['pdf', 'doc', 'docx', 'txt', 'md'].includes(ext)) return 'documents';
    if (['mp4', 'webm', 'mov'].includes(ext)) return 'video';
    return 'other';
  }))];

  const filtered = (files as FileRecord[]).filter((f) => {
    const q = searchTerm.toLowerCase();
    const matchSearch = !q || f.filename.toLowerCase().includes(q);
    const ext = f.filename.split('.').pop()?.toLowerCase() ?? '';
    const category = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext) ? 'images'
      : ['pdf', 'doc', 'docx', 'txt', 'md'].includes(ext) ? 'documents'
      : ['mp4', 'webm', 'mov'].includes(ext) ? 'video' : 'other';
    const matchType = activeType === 'all' || category === activeType;
    return matchSearch && matchType;
  });

  const totalSize = files.reduce((s: number, f: any) => s + (f.file_size || 0), 0);

  return (
    <div className="flex flex-col gap-8 max-w-[1400px] mx-auto pb-12">
      <PageHeader
        title="File Manager"
        description="Upload, organize, and manage all media, documents, and assets for your organization."
        icon={<FolderOpen className="w-5 h-5" />}
        badge={<Badge variant="violet">{files.length} Files</Badge>}
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Files"    value={files.length} icon={<FolderOpen className="w-4 h-4" />} isLoading={isLoading} />
        <StatCard title="Total Size"     value={formatBytes(totalSize)} icon={<FileText className="w-4 h-4" />} iconColor="text-amber-400" isLoading={isLoading} />
        <StatCard title="Images"         value={(files as FileRecord[]).filter((f) => ['jpg','jpeg','png','gif','webp','svg'].includes(f.filename.split('.').pop()?.toLowerCase()??'')).length} icon={<FileImage className="w-4 h-4" />} iconColor="text-sky-400" isLoading={isLoading} />
        <StatCard title="Documents"      value={(files as FileRecord[]).filter((f) => ['pdf','doc','docx','txt','md'].includes(f.filename.split('.').pop()?.toLowerCase()??'')).length} icon={<FileCode className="w-4 h-4" />} iconColor="text-emerald-400" isLoading={isLoading} />
      </div>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-6 flex items-center gap-4 cursor-pointer transition-all ${
          isDragActive ? 'border-violet-500 bg-violet-500/5' : 'border-white/10 hover:border-violet-500/30'
        }`}
      >
        <input {...getInputProps()} />
        <div className={`p-3 rounded-xl border ${isDragActive ? 'bg-violet-500/20 border-violet-500/30' : 'bg-neutral-900 border-white/5'}`}>
          <UploadCloud className={`w-6 h-6 ${isDragActive ? 'text-violet-400' : 'text-neutral-500'}`} />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">
            {isDragActive ? 'Drop files to upload' : 'Drag & drop files, or click to browse'}
          </p>
          <p className="text-xs text-neutral-500 mt-0.5">All file types supported. Max 50MB per file.</p>
        </div>
        {uploadMutation.isPending && (
          <Badge variant="violet" className="ml-auto">Uploading...</Badge>
        )}
      </div>

      {/* Filters + View toggle */}
      <div className="flex items-center gap-3 flex-wrap">
        <Input
          placeholder="Search files..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          leftIcon={<Search className="w-3.5 h-3.5" />}
          className="max-w-xs h-8 text-xs"
        />
        <div className="flex gap-1.5">
          {types.map((type) => (
            <button
              key={type}
              onClick={() => setActiveType(type)}
              className={`text-xs px-2.5 py-1 rounded-full border font-semibold cursor-pointer capitalize transition-all ${
                activeType === type
                  ? 'border-violet-500 bg-violet-500/10 text-violet-400'
                  : 'border-white/10 text-neutral-400 hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-1 border border-white/10 rounded-lg p-0.5">
          {(['grid', 'list'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-2.5 py-1 rounded text-xs font-semibold cursor-pointer transition-all capitalize ${
                viewMode === mode ? 'bg-neutral-800 text-white' : 'text-neutral-500 hover:text-white'
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* File grid/list */}
      {isLoading ? (
        <div className={viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4' : 'flex flex-col gap-2'}>
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className={`bg-neutral-900/40 border border-white/5 animate-pulse rounded-xl ${viewMode === 'grid' ? 'h-44' : 'h-14'}`} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<FolderOpen className="w-8 h-8" />}
          title="No files found"
          description={searchTerm ? 'Try a different search term.' : 'Upload your first file to get started.'}
        />
      ) : (
        <AnimatePresence mode="popLayout">
          <div className={viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4' : 'flex flex-col gap-2'}>
            {filtered.map((file) => (
              <FileCard
                key={file.id}
                file={file}
                viewMode={viewMode}
                onDelete={() => deleteMutation.mutate(file.id)}
              />
            ))}
          </div>
        </AnimatePresence>
      )}
    </div>
  );
}
