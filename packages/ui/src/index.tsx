import * as React from 'react';
import { cn } from '@eaimos/shared';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, glow = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-6 text-white shadow-xl transition-all duration-300 hover:border-violet-500/30',
          glow && 'shadow-[0_0_20px_rgba(139,92,246,0.15)] border-violet-500/20',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
