'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';

// ----------------------------------------------------
// 1. INPUT FIELD COMPONENT
// ----------------------------------------------------
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', label, error, helperText, leftIcon, ...props }, ref) => {
    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label className="text-xs font-semibold text-neutral-400 select-none">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 text-neutral-500 pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            ref={ref}
            className={cn(
              'w-full bg-neutral-950/60 border rounded-lg px-3 py-2 text-sm text-white placeholder-neutral-500 transition-all focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 disabled:opacity-50 disabled:pointer-events-none',
              leftIcon ? 'pl-9' : 'pl-3',
              error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50' : 'border-white/10',
              className
            )}
            {...props}
          />
        </div>
        {error && <span className="text-[11px] font-medium text-rose-400">{error}</span>}
        {!error && helperText && <span className="text-[11px] text-neutral-500">{helperText}</span>}
      </div>
    );
  }
);
Input.displayName = 'Input';

// ----------------------------------------------------
// 2. TEXTAREA COMPONENT
// ----------------------------------------------------
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, ...props }, ref) => {
    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label className="text-xs font-semibold text-neutral-400 select-none">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={cn(
            'w-full min-h-[80px] bg-neutral-950/60 border rounded-lg px-3 py-2 text-sm text-white placeholder-neutral-500 transition-all focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 disabled:opacity-50 disabled:pointer-events-none resize-y',
            error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50' : 'border-white/10',
            className
          )}
          {...props}
        />
        {error && <span className="text-[11px] font-medium text-rose-400">{error}</span>}
        {!error && helperText && <span className="text-[11px] text-neutral-500">{helperText}</span>}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';

// ----------------------------------------------------
// 3. SELECT COMPONENT
// ----------------------------------------------------
export interface SelectOption {
  label: string;
  value: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: SelectOption[];
  helperText?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, helperText, ...props }, ref) => {
    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label className="text-xs font-semibold text-neutral-400 select-none">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            className={cn(
              'w-full bg-neutral-950/60 border rounded-lg px-3 py-2 text-sm text-white placeholder-neutral-500 transition-all focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 disabled:opacity-50 disabled:pointer-events-none appearance-none cursor-pointer',
              error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/50' : 'border-white/10',
              className
            )}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-neutral-900 text-white">
                {opt.label}
              </option>
            ))}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-neutral-500 text-xs">
            ▼
          </div>
        </div>
        {error && <span className="text-[11px] font-medium text-rose-400">{error}</span>}
        {!error && helperText && <span className="text-[11px] text-neutral-500">{helperText}</span>}
      </div>
    );
  }
);
Select.displayName = 'Select';

// ----------------------------------------------------
// 4. CHECKBOX COMPONENT
// ----------------------------------------------------
export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  error?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, error, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1">
        <label className="inline-flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            ref={ref}
            className={cn(
              'rounded border border-white/10 bg-neutral-950/60 text-violet-600 focus:ring-violet-500/50 focus:ring-offset-0 focus:ring-1 w-4 h-4 cursor-pointer',
              className
            )}
            {...props}
          />
          <span className="text-sm text-neutral-300 hover:text-white transition-colors">
            {label}
          </span>
        </label>
        {error && <span className="text-[11px] font-medium text-rose-400 pl-6">{error}</span>}
      </div>
    );
  }
);
Checkbox.displayName = 'Checkbox';
