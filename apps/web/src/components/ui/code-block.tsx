'use client';

import * as React from 'react';
import { cn } from '@eaimos/shared';
import { Check, Copy } from 'lucide-react';

export interface CodeBlockProps {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
  copyable?: boolean;
  className?: string;
  maxHeight?: string;
}

export function CodeBlock({
  code,
  language = 'text',
  showLineNumbers = false,
  copyable = true,
  className,
  maxHeight = '400px',
}: CodeBlockProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
    }
  };

  const lines = code.split('\n');

  return (
    <div
      className={cn(
        'relative rounded-xl border border-white/10 bg-neutral-900 overflow-hidden font-mono text-xs',
        className
      )}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-neutral-950/60">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
          {language && (
            <span className="text-[10px] text-neutral-500 font-sans ml-2 uppercase tracking-wide">
              {language}
            </span>
          )}
        </div>
        {copyable && (
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-[10px] text-neutral-500 hover:text-white transition-colors cursor-pointer"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                Copy
              </>
            )}
          </button>
        )}
      </div>

      {/* Code content */}
      <div
        className="overflow-auto"
        style={{ maxHeight }}
      >
        <div className="p-4 leading-relaxed">
          {showLineNumbers ? (
            <table className="w-full border-collapse">
              <tbody>
                {lines.map((line, idx) => (
                  <tr key={idx} className="hover:bg-white/3">
                    <td className="pr-4 text-right select-none text-neutral-600 w-8">
                      {idx + 1}
                    </td>
                    <td>
                      <pre className="text-neutral-200 whitespace-pre">{line || ' '}</pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <pre className="text-neutral-200 whitespace-pre-wrap break-words">{code}</pre>
          )}
        </div>
      </div>
    </div>
  );
}
