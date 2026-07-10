'use client';

import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';

const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(255),
  domain: z.string().min(1, 'Domain is required').max(500),
  description: z.string().optional(),
  subject_scope: z.array(z.string()),
  out_of_scope: z.array(z.string()),
  default_flexibility: z.number().min(0).max(1),
});

export type ProjectFormData = z.infer<typeof projectSchema>;

interface ProjectFormProps {
  defaultValues?: Partial<ProjectFormData>;
  onSubmit: (data: ProjectFormData) => void;
  onCancel?: () => void;
}

export function ProjectForm({ defaultValues, onSubmit, onCancel }: ProjectFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: '',
      domain: '',
      description: '',
      subject_scope: [],
      out_of_scope: [],
      default_flexibility: 0.6,
      ...defaultValues,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="p-6 bg-white/40 backdrop-blur-sm rounded-xl border border-border/10 shadow-sm space-y-4">
        <Input
          label="Project Name"
          placeholder="e.g. Quantum Neural Networks"
          error={errors.name?.message}
          {...register('name')}
        />

        <Input
          label="Research Domain"
          placeholder="e.g. Physics, Artificial Intelligence"
          error={errors.domain?.message}
          {...register('domain')}
        />

        <Textarea
          label="Scientific Description"
          placeholder="Describe the research goals and core methodology..."
          rows={4}
          error={errors.description?.message}
          {...register('description')}
        />
      </div>

      <div className="p-6 bg-white/40 backdrop-blur-sm rounded-xl border border-border/10 shadow-sm">
        <label className="block text-sm font-bold text-foreground/80 mb-3 ml-1 uppercase tracking-wider">
          Cognitive Flexibility ({defaultValues?.default_flexibility ?? 0.6})
        </label>
        <div className="px-2">
          <input
            type="range"
            {...register('default_flexibility', { valueAsNumber: true })}
            min="0"
            max="1"
            step="0.1"
            className="w-full h-2 bg-muted rounded-full appearance-none cursor-pointer accent-primary transition-all duration-300 hover:scale-[1.01]"
          />
          <div className="flex justify-between mt-2 px-1 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
            <span>Strict</span>
            <span>Balanced</span>
            <span>Creative</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-2">
        <Button type="submit" disabled={isSubmitting} className="px-8 shadow-lg shadow-primary/20">
          {isSubmitting ? 'Initializing...' : 'Initialize Project'}
        </Button>
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} className="px-8">
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
