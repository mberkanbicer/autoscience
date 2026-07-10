'use client';

import { useEffect, useState } from 'react';
import { collaborationApi } from '@/lib/api';
import type { Comment } from '@/lib/types';
import { formatDate } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Loader2, MessageSquare } from 'lucide-react';

interface CommentThreadProps {
  projectId: string;
  entityType: string;
  entityId: string;
}

export function CommentThread({ projectId, entityType, entityId }: CommentThreadProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState(false);

  const loadComments = async () => {
    setLoading(true);
    try {
      const data = await collaborationApi.listComments(projectId, entityType, entityId);
      setComments(data);
    } catch (error) {
      console.error('Failed to load comments:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComments();
  }, [projectId, entityType, entityId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!body.trim()) return;
    setPosting(true);
    try {
      await collaborationApi.createComment({
        project_id: projectId,
        entity_type: entityType,
        entity_id: entityId,
        body: body.trim(),
      });
      setBody('');
      await loadComments();
    } catch (error) {
      console.error('Failed to post comment:', error);
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="space-y-4 border-t border-border/10 pt-6 mt-6">
      <div className="flex items-center gap-2">
        <MessageSquare size={16} className="text-primary" />
        <h4 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
          Discussion ({comments.length})
        </h4>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <Textarea
          label="Add comment"
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Share feedback on this node..."
          rows={2}
        />
        <Button type="submit" size="sm" disabled={posting || !body.trim()}>
          {posting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
          Post
        </Button>
      </form>

      {loading ? (
        <div className="flex justify-center py-6">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      ) : comments.length === 0 ? (
        <p className="text-sm text-muted-foreground">No comments yet.</p>
      ) : (
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="p-3 rounded-xl border border-border/10 bg-white/30"
            >
              <div className="flex items-center justify-between mb-1">
                <p className="font-bold text-sm">{comment.author_name}</p>
                <span className="text-[10px] text-muted-foreground">
                  {formatDate(comment.created_at)}
                </span>
              </div>
              <Badge variant="default" className="mb-2 text-[9px]">
                {comment.status}
              </Badge>
              <p className="text-sm text-muted-foreground">{comment.body}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}