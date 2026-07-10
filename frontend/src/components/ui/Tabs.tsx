'use client';

import { ReactNode, createContext, useContext, useState } from 'react';
import { cn } from '@/lib/utils';
import { ChevronDown } from 'lucide-react';

interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | undefined>(undefined);

interface TabsProps {
  defaultValue: string;
  onValueChange?: (value: string) => void;
  children: ReactNode;
  className?: string;
}

export function Tabs({ defaultValue, onValueChange, children, className }: TabsProps) {
  const [value, setValue] = useState(defaultValue);

  const handleChange = (newValue: string) => {
    setValue(newValue);
    onValueChange?.(newValue);
  };

  return (
    <TabsContext.Provider value={{ value, onValueChange: handleChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

interface TabsListProps {
  children: ReactNode;
  className?: string;
}

export function TabsList({ children, className }: TabsListProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 p-1.5 bg-white/20 backdrop-blur-xl border border-white/10 rounded-2xl shadow-inner',
        className
      )}
    >
      {children}
    </div>
  );
}

interface TabsTriggerProps {
  value: string;
  children: ReactNode;
  className?: string;
  onMouseEnter?: () => void;
}

export function TabsTrigger({ value, children, className, onMouseEnter }: TabsTriggerProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('TabsTrigger must be used within Tabs');

  const isActive = context.value === value;

  return (
    <button
      onClick={() => context.onValueChange(value)}
      onMouseEnter={onMouseEnter}
      className={cn(
        'px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl transition-all duration-500 ease-out',
        isActive
          ? 'bg-primary text-white shadow-2xl shadow-primary/40 scale-[1.05]'
          : 'text-muted-foreground/60 hover:text-foreground hover:bg-white/40',
        className
      )}
    >
      {children}
    </button>
  );
}

interface TabsContentProps {
  value: string;
  children: ReactNode;
  className?: string;
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('TabsContent must be used within Tabs');

  if (context.value !== value) return null;

  return <div className={cn('mt-6 animate-in fade-in zoom-in-[0.98] slide-in-from-top-4 duration-700 ease-out', className)}>{children}</div>;
}

// Accordion component
interface AccordionItemProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

export function AccordionItem({ title, children, defaultOpen = false }: AccordionItemProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-white/10 rounded-2xl overflow-hidden glass transition-all duration-500 hover:shadow-2xl">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-6 py-5 bg-white/40 hover:bg-white/60 transition-colors group"
      >
        <span className="font-black text-foreground uppercase tracking-wider text-xs group-hover:text-primary transition-colors">{title}</span>
        <ChevronDown
          size={20}
          className={cn('text-muted-foreground transition-all duration-500', isOpen && 'rotate-180 text-primary')}
        />
      </button>
      {isOpen && (
        <div className="px-8 py-8 animate-in slide-in-from-top-4 duration-700 ease-out border-t border-white/5">
          {children}
        </div>
      )}
    </div>
  );
}
