'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { Input, Textarea } from '@/components/ui/Input';
import { EmptyState } from '@/components/ui/EmptyState';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ideasApi, getAuthHeaders } from '@/lib/api';
import { getLlmHeaders } from '@/lib/apiSettings';
import { Idea, GeneratedIdea } from '@/lib/types';
import { formatDate, cn } from '@/lib/utils';
import {
  Lightbulb,
  Plus,
  Play,
  Pause,
  Trash2,
  Edit2,
  Loader2,
  Clock,
  Sparkles,
  Lock,
  Unlock,
} from 'lucide-react';

export default function IdeasPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingIdea, setEditingIdea] = useState<Idea | null>(null);
  const [deletingIdea, setDeletingIdea] = useState<Idea | null>(null);
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [newIdea, setNewIdea] = useState({ text: '' });
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generateTopic, setGenerateTopic] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generateResult, setGenerateResult] = useState<any>(null);

  useEffect(() => {
    loadIdeas();
  }, [projectId]);

  const loadIdeas = async () => {
    try {
      const data = await ideasApi.list(projectId);
      setIdeas(data);
    } catch (error) {
      console.error('Failed to load ideas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newIdea.text.trim()) return;
    setCreating(true);
    try {
      const created = await ideasApi.create(projectId, { text: newIdea.text });
      setShowCreateModal(false);
      setNewIdea({ text: '' });
      await loadIdeas();
    } catch (error) {
      console.error('Failed to create idea:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingIdea || !editingIdea.current_text.trim()) return;
    setUpdating(true);
    try {
      await ideasApi.update(editingIdea.id, { current_text: editingIdea.current_text });
      setEditingIdea(null);
      await loadIdeas();
    } catch (error) {
      console.error('Failed to update idea:', error);
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingIdea) return;
    setDeleting(true);
    try {
      await ideasApi.delete(deletingIdea.id);
      setDeletingIdea(null);
      await loadIdeas();
    } catch (error: any) {
      alert('Failed to delete: ' + (error.message || 'Unknown error'));
    } finally {
      setDeleting(false);
    }
  };

  const handlePause = async (idea: Idea) => {
    setActionLoading(idea.id);
    try {
      await ideasApi.pause(idea.id);
      await loadIdeas();
    } catch (error: any) {
      alert('Failed to pause: ' + (error.message || 'Unknown error'));
    } finally {
      setActionLoading(null);
    }
  };

  const handleResume = async (idea: Idea) => {
    setActionLoading(idea.id);
    try {
      await ideasApi.resume(idea.id);
      await loadIdeas();
    } catch (error: any) {
      alert('Failed to resume: ' + (error.message || 'Unknown error'));
    } finally {
      setActionLoading(null);
    }
  };

  const handleStartResearch = async (idea: Idea) => {
    setActionLoading(idea.id);
    try {
      const response = await fetch(
        '/api/v1/research/run',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
            ...getLlmHeaders(),
          },
          body: JSON.stringify({
            project_id: projectId,
            idea: idea.current_text || idea.initial_text,
            run_type: 'user_directed',
            flexibility: idea.flexibility || 0.6,
          }),
        }
      );
      if (response.ok) {
        const result = await response.json();
        // Stay on page — user can start multiple runs
        alert(`Research started! Run ID: ${result.run_id?.slice(0, 8)}...\n\nGo to Runs page to track progress.`);
      } else {
        const err = await response.json().catch(() => ({}));
        alert('Failed: ' + (err.detail || 'Unknown error'));
      }
    } catch (error: any) {
      alert('Failed to start research: ' + (error.message || 'Unknown error'));
    } finally {
      setActionLoading(null);
    }
  };

  const handleGenerateFromLiterature = async () => {
    if (!generateTopic.trim()) return;
    setGenerating(true);
    setGenerateResult(null);
    try {
      const response = await fetch(
        `/api/v1/ideas/generate?project_id=${projectId}&topic=${encodeURIComponent(generateTopic)}&num_ideas=5`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
            ...getLlmHeaders(),
          },
        }
      );
      if (response.ok) {
        const result = await response.json();
        setGenerateResult(result);
        await loadIdeas();
      } else {
        const err = await response.json().catch(() => ({}));
        alert('Failed: ' + (err.detail || 'Unknown error'));
      }
    } catch (error: any) {
      alert('Failed: ' + (error.message || 'Unknown error'));
    } finally {
      setGenerating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'rejected': return 'danger';
      case 'promoted': return 'info';
      default: return 'default';
    }
  };

  const isActive = (idea: Idea) => idea.status === 'active';
  const isPaused = (idea: Idea) => idea.status === 'paused';

  return (
    <Layout projectId={projectId}>
      <Header
        title="Ideas"
        subtitle={`${ideas.length} ideas · ${ideas.filter(i => i.status === 'active').length} active`}
        actions={
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setShowGenerateModal(true)}>
              <Sparkles size={18} className="mr-2" />
              Generate from Literature
            </Button>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus size={18} className="mr-2" />
              New Idea
            </Button>
          </div>
        }
      />

      <div className="p-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
          </div>
        ) : ideas.length === 0 ? (
          <EmptyState
            icon={<Lightbulb className="w-8 h-8 text-gray-400" />}
            title="No ideas yet"
            description="Add a research idea to start the autonomous research pipeline."
            action={
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus size={18} className="mr-2" />
                Add First Idea
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {ideas.map((idea) => (
              <Card key={idea.id} hover className="group">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        'w-10 h-10 rounded-xl flex items-center justify-center shadow-inner transition-colors duration-500',
                        isActive(idea) ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground/40'
                      )}>
                        <Lightbulb size={20} className={isActive(idea) ? 'animate-pulse' : ''} />
                      </div>
                      <Badge variant={getStatusColor(idea.status)} className={cn(
                        'uppercase text-[10px] font-bold tracking-widest',
                        idea.status === 'active' && 'bg-success/10'
                      )}>
                        {idea.status}
                      </Badge>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-[-4px] group-hover:translate-y-0">
                      {/* Start Research — only for active ideas */}
                      {isActive(idea) && (
                        <button
                          onClick={() => handleStartResearch(idea)}
                          disabled={actionLoading === idea.id}
                          className="p-2 rounded-lg hover:bg-success/10 text-success transition-all duration-300 hover:scale-110"
                          title="Start Research Run"
                        >
                          {actionLoading === idea.id ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Play size={16} fill="currentColor" className="opacity-20" />
                          )}
                        </button>
                      )}
                      {/* Pause/Resume */}
                      {isActive(idea) && (
                        <button
                          onClick={() => handlePause(idea)}
                          disabled={actionLoading === idea.id}
                          className="p-2 rounded-lg hover:bg-warning/10 text-warning transition-all duration-300 hover:scale-110"
                          title="Pause"
                        >
                          {actionLoading === idea.id ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Pause size={16} fill="currentColor" className="opacity-20" />
                          )}
                        </button>
                      )}
                      {isPaused(idea) && (
                        <button
                          onClick={() => handleResume(idea)}
                          disabled={actionLoading === idea.id}
                          className="p-2 rounded-lg hover:bg-success/10 text-success transition-all duration-300 hover:scale-110"
                          title="Resume"
                        >
                          {actionLoading === idea.id ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Play size={16} fill="currentColor" className="opacity-20" />
                          )}
                        </button>
                      )}
                      {/* Edit — only when paused */}
                      {isPaused(idea) && (
                        <button
                          onClick={() => setEditingIdea(idea)}
                          className="p-2 rounded-lg hover:bg-primary/10 text-primary transition-all duration-300 hover:scale-110"
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                      )}
                      {/* Delete — only when paused */}
                      {isPaused(idea) && (
                        <button
                          onClick={() => setDeletingIdea(idea)}
                          className="p-2 rounded-lg hover:bg-error/10 text-error transition-all duration-300 hover:scale-110"
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </div>

                  <p className="text-foreground/80 text-sm font-medium leading-relaxed mb-6 line-clamp-3 group-hover:line-clamp-none transition-all duration-500">
                    {idea.current_text || idea.initial_text}
                  </p>

                  <div className="flex items-center justify-between pt-4 border-t border-border/5">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground/40 uppercase tracking-widest">
                        <Clock size={12} />
                        {formatDate(idea.created_at)}
                      </span>
                    </div>
                    {idea.overall_score != null && (
                      <div className="flex items-center gap-2 px-2 py-0.5 bg-primary/5 rounded-full border border-primary/10">
                        <Sparkles size={12} className="text-primary animate-pulse" />
                        <span className="text-[10px] font-bold text-primary">{(idea.overall_score * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </div>

                  {(idea.classification || idea.parent_idea_id) && (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {idea.classification && (
                        <Badge variant="info" size="sm" className="bg-primary/5 text-[9px] uppercase tracking-widest font-bold">
                          {idea.classification}
                        </Badge>
                      )}
                      {idea.parent_idea_id && (
                        <Badge variant="default" size="sm" className="bg-muted text-[9px] uppercase tracking-widest font-bold">
                          sub-idea
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => !creating && setShowCreateModal(false)}
        title="Add Research Idea"
      >
        <div className="space-y-4">
          <Textarea
            label="Research Idea"
            placeholder="Describe your research idea..."
            rows={4}
            value={newIdea.text}
            onChange={(e) => setNewIdea({ text: e.target.value })}
          />
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowCreateModal(false)} disabled={creating}>
            Cancel
          </Button>
          <Button onClick={handleCreate} loading={creating} disabled={!newIdea.text.trim()}>
            Add Idea
          </Button>
        </ModalFooter>
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingIdea}
        onClose={() => !updating && setEditingIdea(null)}
        title="Edit Idea"
      >
        <div className="space-y-4">
          <Textarea
            label="Research Idea"
            rows={4}
            value={editingIdea?.current_text || ''}
            onChange={(e) => editingIdea && setEditingIdea({ ...editingIdea, current_text: e.target.value })}
          />
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setEditingIdea(null)} disabled={updating}>
            Cancel
          </Button>
          <Button onClick={handleUpdate} loading={updating}>
            Save Changes
          </Button>
        </ModalFooter>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingIdea}
        onClose={() => !deleting && setDeletingIdea(null)}
        title="Delete Idea"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to delete this idea? This action cannot be undone.
          </p>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-sm text-gray-800 line-clamp-2">
              {deletingIdea?.current_text || deletingIdea?.initial_text}
            </p>
          </div>
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setDeletingIdea(null)} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete} loading={deleting}>
            Delete Idea
          </Button>
        </ModalFooter>
      </Modal>

      {/* Generate from Literature Modal */}
      <Modal
        isOpen={showGenerateModal}
        onClose={() => !generating && setShowGenerateModal(false)}
        title="Generate Ideas from Literature"
        size="lg"
      >
        {generateResult ? (
          <div className="space-y-6 animate-in fade-in duration-700">
            <div className="bg-success/10 border border-success/20 rounded-xl p-5 text-sm text-success flex items-start gap-4 shadow-inner">
               <Sparkles className="shrink-0 animate-pulse" size={20} />
               <div>
                  <p className="font-bold uppercase tracking-wider text-[10px]">Synthesis Complete</p>
                  <p className="mt-1 font-medium">Generated {generateResult.ideas_generated} insights from {generateResult.papers_analyzed} research papers. They have been integrated into your laboratory.</p>
               </div>
            </div>
            <div className="grid gap-4">
              {generateResult.ideas.map((idea: GeneratedIdea, i: number) => (
                <div key={i} className="bg-white/40 backdrop-blur-sm border border-border/10 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-300">
                  <p className="font-bold text-foreground tracking-tight">{idea.title}</p>
                  <p className="text-muted-foreground text-sm mt-2 leading-relaxed">{idea.description}</p>
                  <div className="flex items-center gap-3 mt-4">
                    {idea.novelty && <Badge variant="info" size="sm" className="bg-primary/5 uppercase text-[9px] font-bold tracking-widest">Novelty: {idea.novelty}</Badge>}
                    {idea.importance && <span className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest">{idea.importance}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : generating ? (
          <div className="flex flex-col items-center py-16 animate-pulse">
            <div className="relative mb-8">
               <Loader2 size={64} className="animate-spin text-primary opacity-20" />
               <Sparkles size={32} className="absolute inset-0 m-auto text-primary animate-bounce" />
            </div>
            <h3 className="text-xl font-bold text-foreground tracking-tight uppercase">Synthesizing Literature...</h3>
            <p className="text-sm text-muted-foreground mt-2 font-medium">Identifying frontier opportunities and mapping cognitive gaps.</p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-primary/5 border border-primary/10 rounded-xl p-5 text-sm text-primary flex items-start gap-4 shadow-inner">
               <Lightbulb className="shrink-0" size={20} />
               <p className="font-medium">Enter a research vector. The system will ingest recent publications, detect scientific tensions, and propose high-novelty directions.</p>
            </div>
            <div className="space-y-2">
              <Input
                label="Research Vector / Field"
                placeholder="e.g. quantum neural architectures, CRISPR efficiency in vivo..."
                value={generateTopic}
                onChange={(e) => setGenerateTopic(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleGenerateFromLiterature()}
              />
            </div>
          </div>
        )}
        <ModalFooter>
          {generateResult ? (
            <Button onClick={() => { setShowGenerateModal(false); setGenerateResult(null); setGenerateTopic(''); }}>
              Done
            </Button>
          ) : (
            <>
              <Button variant="secondary" onClick={() => setShowGenerateModal(false)} disabled={generating}>
                Cancel
              </Button>
              <Button onClick={handleGenerateFromLiterature} loading={generating} disabled={!generateTopic.trim()}>
                <Sparkles size={16} className="mr-2" /> Generate Ideas
              </Button>
            </>
          )}
        </ModalFooter>
      </Modal>
    </Layout>
  );
}
