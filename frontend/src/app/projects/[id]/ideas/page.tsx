'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { Textarea } from '@/components/ui/Input';
import { EmptyState } from '@/components/ui/EmptyState';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ideasApi } from '@/lib/api';
import { Idea } from '@/lib/types';
import { formatDate } from '@/lib/utils';
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
      const apiSettings = JSON.parse(localStorage.getItem('autoscience_api_settings') || '{}');
      const response = await fetch(
        `/api/v1/research/run?project_id=${projectId}&idea=${encodeURIComponent(idea.current_text || idea.initial_text)}&run_type=user_directed`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-OpenRouter-API-Key': apiSettings.openrouter_api_key || '',
            'X-OpenRouter-Model': apiSettings.openrouter_model || 'openai/gpt-4o',
            'X-Default-Provider': apiSettings.default_provider || 'openrouter',
          },
        }
      );
      if (response.ok) {
        router.push(`/projects/${projectId}/runs`);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'rejected': return 'error';
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
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus size={18} className="mr-2" />
            New Idea
          </Button>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ideas.map((idea) => (
              <Card key={idea.id} hover>
                <div className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Lightbulb size={18} className={isActive(idea) ? 'text-yellow-500' : 'text-gray-400'} />
                      <Badge variant={getStatusColor(idea.status)}>
                        {idea.status}
                      </Badge>
                    </div>
                    <div className="flex gap-1">
                      {/* Start Research — only for active ideas */}
                      {isActive(idea) && (
                        <button
                          onClick={() => handleStartResearch(idea)}
                          disabled={actionLoading === idea.id}
                          className="p-1.5 rounded-lg hover:bg-green-50 text-green-600 transition-colors"
                          title="Start Research Run"
                        >
                          {actionLoading === idea.id ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Play size={16} />
                          )}
                        </button>
                      )}
                      {/* Pause/Resume */}
                      {isActive(idea) && (
                        <button
                          onClick={() => handlePause(idea)}
                          disabled={actionLoading === idea.id}
                          className="p-1.5 rounded-lg hover:bg-amber-50 text-amber-600 transition-colors"
                          title="Pause (stops research, allows editing)"
                        >
                          {actionLoading === idea.id ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Pause size={16} />
                          )}
                        </button>
                      )}
                      {isPaused(idea) && (
                        <button
                          onClick={() => handleResume(idea)}
                          disabled={actionLoading === idea.id}
                          className="p-1.5 rounded-lg hover:bg-green-50 text-green-600 transition-colors"
                          title="Resume (restarting research)"
                        >
                          {actionLoading === idea.id ? (
                            <Loader2 size={16} className="animate-spin" />
                          ) : (
                            <Play size={16} />
                          )}
                        </button>
                      )}
                      {/* Edit — only when paused */}
                      {isPaused(idea) && (
                        <button
                          onClick={() => setEditingIdea(idea)}
                          className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-600 transition-colors"
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                      )}
                      {isActive(idea) && (
                        <span className="p-1.5 text-gray-300" title="Pause the idea to edit">
                          <Lock size={16} />
                        </span>
                      )}
                      {/* Delete — only when paused */}
                      {isPaused(idea) && (
                        <button
                          onClick={() => setDeletingIdea(idea)}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-red-600 transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                      {isActive(idea) && (
                        <span className="p-1.5 text-gray-300" title="Pause the idea to delete">
                          <Lock size={16} />
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="text-gray-800 text-sm mb-3 line-clamp-3">
                    {idea.current_text || idea.initial_text}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {formatDate(idea.created_at)}
                    </span>
                    {idea.overall_score != null && (
                      <span className="flex items-center gap-1">
                        <Sparkles size={12} className="text-yellow-500" />
                        Score: {(idea.overall_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  {idea.classification && (
                    <div className="mt-3">
                      <Badge variant="info" size="sm">
                        {idea.classification}
                      </Badge>
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
    </Layout>
  );
}
