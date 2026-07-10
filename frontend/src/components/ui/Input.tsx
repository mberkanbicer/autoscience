'use client';

import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="block text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 mb-2 ml-2">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'w-full px-5 py-4 bg-white/40 backdrop-blur-xl border rounded-2xl shadow-lg transition-all duration-500 ease-out',
            'focus:outline-none focus:ring-4 focus:ring-primary/30 focus:border-primary/50 focus:bg-white focus:scale-[1.01]',
            'placeholder:text-muted-foreground/30 font-bold text-foreground/80',
            error ? 'border-error/40 text-error placeholder:text-error/20' : 'border-white/20',
            className
          )}
          {...props}
        />
        {(error || helperText) && (
          <p className={cn('text-[10px] mt-2 ml-2 font-black uppercase tracking-wider', error ? 'text-error animate-pulse' : 'text-muted-foreground/40')}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={textareaId} className="block text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 mb-2 ml-2">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={cn(
            'w-full px-5 py-4 bg-white/40 backdrop-blur-xl border rounded-2xl shadow-lg transition-all duration-500 ease-out resize-none',
            'focus:outline-none focus:ring-4 focus:ring-primary/30 focus:border-primary/50 focus:bg-white focus:scale-[1.01]',
            'placeholder:text-muted-foreground/30 font-bold text-foreground/80 leading-relaxed',
            error ? 'border-error/40 text-error placeholder:text-error/20' : 'border-white/20',
            className
          )}
          {...props}
        />
        {(error || helperText) && (
          <p className={cn('text-[10px] mt-2 ml-2 font-black uppercase tracking-wider', error ? 'text-error animate-pulse' : 'text-muted-foreground/40')}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, id, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={selectId} className="block text-[10px] font-black uppercase tracking-[0.2em] text-foreground/40 mb-2 ml-2">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(
            'w-full px-5 py-4 bg-white/40 backdrop-blur-xl border rounded-2xl shadow-lg transition-all duration-500 ease-out',
            'focus:outline-none focus:ring-4 focus:ring-primary/30 focus:border-primary/50 focus:bg-white focus:scale-[1.01]',
            'font-bold text-foreground/80 appearance-none',
            error ? 'border-error/40 text-error' : 'border-white/20',
            className
          )}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value} className="bg-white text-foreground">
              {option.label}
            </option>
          ))}
        </select>
        {error && <p className="text-[10px] mt-2 ml-2 font-black uppercase tracking-wider text-error animate-pulse">{error}</p>}
      </div>
    );
  }
);

Select.displayName = 'Select';
