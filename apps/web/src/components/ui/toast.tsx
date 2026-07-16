'use client';

import { toast as sonnerToast, Toaster as SonnerToaster } from 'sonner';

export const toast = {
  success: (message: string, description?: string) => {
    sonnerToast.success(message, { description });
  },
  error: (message: string, description?: string) => {
    sonnerToast.error(message, { description });
  },
  info: (message: string, description?: string) => {
    sonnerToast.info(message, { description });
  },
  loading: (message: string) => {
    return sonnerToast.loading(message);
  },
  dismiss: (id?: string | number) => {
    sonnerToast.dismiss(id);
  },
};

export function ToastProvider() {
  return (
    <SonnerToaster
      theme="system"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast: 'group toast rounded-lg border border-border bg-card text-foreground shadow-card p-4 flex gap-3 items-center',
          title: 'text-sm font-semibold',
          description: 'text-xs text-muted-foreground',
          actionButton: 'bg-primary text-primary-foreground hover:bg-primary/90',
          cancelButton: 'bg-transparent text-muted-foreground hover:text-foreground',
        },
      }}
    />
  );
}
