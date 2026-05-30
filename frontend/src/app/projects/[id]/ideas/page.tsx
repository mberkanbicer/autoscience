'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { Textarea, Select } from '@/components/ui/Input';
import { Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from '@/components/ui/Table';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ideasApi } from '@/lib/api';
import { Idea } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { Lightbulb, Plus, TrendingUp } from 'lucide-react';

export default function IdeasPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newIdea, setNewIdea] = useState({
    text: '',
    origin: 'user_prompt',
  });

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
      await ideasApi.create(projectId, {
        initial_text: newIdea.text,
        current_text: newIdea.text,
        origin: newIdea.origin,
      });
      setShowCreateModal(false);
      setNewIdea({ text: '', origin: 'user_prompt' });
      loadIdeas();
    } catch (error) {
      console.error('Failed to create idea:', error);
    } finally {
      setCreating(false);
    }
  };

  const filteredIdeas = ideas.filter((idea) => {
    if (filter === 'all') return true;
    return idea.status === filter;
  });

  return (
    <Layout projectId={projectId}>
      <Header
        title="Ideas"
        subtitle={`${ideas.length} research ideas tracked`}
        actions={
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus size={18} className="mr-2" />
            New Idea
          </Button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Filters */}
        <Tabs defaultValue="all" onValueChange={(v) => setFilter(v)}>
          <TabsList>
            <TabsTrigger value="all">All ({ideas.length})</TabsTrigger>
            <TabsTrigger value="active">Active ({ideas.filter(i => i.status === 'active').length})</TabsTrigger>
            <TabsTrigger value="under_validation">Validating ({ideas.filter(i => i.status === 'under_validation').length})</TabsTrigger>
            <TabsTrigger value="promoted">Promoted ({ideas.filter(i => i.status === 'promoted').length})</TabsTrigger>
            <TabsTrigger value="rejected">Rejected ({ideas.filter(i => i.status === 'rejected').length})</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Ideas Table */}
        {loading ? (
          <SkeletonTable />
        ) : filteredIdeas.length === 0 ? (
          <EmptyState
            icon={<Lightbulb className="w-8 h-8 text-gray-400" />}
            title="No ideas yet"
            description="Click 'New Idea' to add your first research idea."
            action={
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus size={18} className="mr-2" />
                Create Idea
              </Button>
            }
          />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Idea</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Origin</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredIdeas.map((idea) => (
                <TableRow key={idea.id}>
                  <TableCell>
                    <div className="max-w-md">
                      <p className="font-medium text-gray-900 truncate">{idea.current_text}</p>
                      {idea.classification_reason && (
                        <p className="text-xs text-gray-500 truncate mt-1">{idea.classification_reason}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={idea.status} />
                  </TableCell>
                  <TableCell>
                    {idea.classification ? (
                      <Badge variant={
                        idea.classification === 'high_value' ? 'success' :
                        idea.classification === 'promising' ? 'info' :
                        idea.classification === 'weak' ? 'danger' : 'default'
                      }>
                        {idea.classification}
                      </Badge>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {idea.overall_score ? (
                      <div className="flex items-center gap-2">
                        <TrendingUp size={14} className="text-green-500" />
                        <span className="font-medium">{idea.overall_score.toFixed(1)}</span>
                      </div>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant="default">{idea.origin.replace('_', ' ')}</Badge>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm text-gray-500">{formatDate(idea.created_at)}</span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Create Idea Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="New Research Idea"
        size="lg"
      >
        <div className="space-y-4">
          <Textarea
            label="Research Idea"
            placeholder="Describe your research idea in detail..."
            rows={6}
            value={newIdea.text}
            onChange={(e) => setNewIdea({ ...newIdea, text: e.target.value })}
          />
          <Select
            label="Origin"
            value={newIdea.origin}
            onChange={(e) => setNewIdea({ ...newIdea, origin: e.target.value })}
            options={[
              { value: 'user_prompt', label: 'User Prompt' },
              { value: 'idle_generated', label: 'Idle Generated' },
              { value: 'literature_gap', label: 'Literature Gap' },
              { value: 'skill_generated', label: 'Skill Generated' },
            ]}
          />
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} loading={creating} disabled={!newIdea.text.trim()}>
            Create Idea
          </Button>
        </ModalFooter>
      </Modal>
    </Layout>
  );
}
