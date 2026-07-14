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
      theme="dark"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast: 'group toast bg-neutral-900 border border-white/10 text-white rounded-lg shadow-2xl p-4 flex gap-3 items-center',
          title: 'text-sm font-semibold',
          description: 'text-xs text-neutral-400',
          actionButton: 'bg-neutral-800 text-white hover:bg-neutral-700',
          cancelButton: 'bg-transparent text-neutral-400 hover:text-white',
        },
      }}
    />
  );
}
