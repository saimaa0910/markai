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
          <label className="text-xs font-semibold text-muted-foreground select-none">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="pointer-events-none absolute left-3 text-muted-foreground">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            ref={ref}
            className={cn(
              'w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground transition-all focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40 disabled:pointer-events-none disabled:opacity-50',
              leftIcon ? 'pl-9' : 'pl-3',
              error ? 'border-destructive focus:border-destructive focus:ring-destructive/40' : 'border-border',
              className
            )}
            {...props}
          />
        </div>
        {error && <span className="text-[11px] font-medium text-destructive">{error}</span>}
        {!error && helperText && <span className="text-[11px] text-muted-foreground">{helperText}</span>}
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
          <label className="text-xs font-semibold text-muted-foreground select-none">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          className={cn(
            'w-full min-h-[80px] resize-y rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground transition-all focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40 disabled:pointer-events-none disabled:opacity-50',
            error ? 'border-destructive focus:border-destructive focus:ring-destructive/40' : 'border-border',
            className
          )}
          {...props}
        />
        {error && <span className="text-[11px] font-medium text-destructive">{error}</span>}
        {!error && helperText && <span className="text-[11px] text-muted-foreground">{helperText}</span>}
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
          <label className="text-xs font-semibold text-muted-foreground select-none">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            className={cn(
              'w-full appearance-none cursor-pointer rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground transition-all focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40 disabled:pointer-events-none disabled:opacity-50',
              error ? 'border-destructive focus:border-destructive focus:ring-destructive/40' : 'border-border',
              className
            )}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-card text-foreground">
                {opt.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
            ▼
          </div>
        </div>
        {error && <span className="text-[11px] font-medium text-destructive">{error}</span>}
        {!error && helperText && <span className="text-[11px] text-muted-foreground">{helperText}</span>}
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
        <label className="inline-flex cursor-pointer select-none items-center gap-2">
          <input
            type="checkbox"
            ref={ref}
            className={cn(
              'h-4 w-4 cursor-pointer rounded border border-border bg-card text-primary focus:ring-1 focus:ring-primary/40 focus:ring-offset-0',
              className
            )}
            {...props}
          />
          <span className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            {label}
          </span>
        </label>
        {error && <span className="pl-6 text-[11px] font-medium text-destructive">{error}</span>}
      </div>
    );
  }
);
Checkbox.displayName = 'Checkbox';
