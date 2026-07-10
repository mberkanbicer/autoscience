'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Layout } from '@/components/layout/Layout';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input, Textarea } from '@/components/ui/Input';
import { Select } from '@/components/ui/Input';
import { authApi, collaborationApi, projectsApi, setAuthSession, clearAuthSession } from '@/lib/api';
import type {
  ActivityItem,
  Comment,
  ProjectMember,
  CollaborationUser,
  ReviewProposal,
  PeerReviewSimulation,
  ReviewNotification,
} from '@/lib/types';
import { formatDate } from '@/lib/utils';
import {
  Users,
  MessageSquare,
  UserPlus,
  Loader2,
  ClipboardList,
  Activity,
  Download,
  LogIn,
  Bot,
} from 'lucide-react';
import { NotificationBell } from '@/components/layout/NotificationBell';

const USER_EMAIL_KEY = 'autoscience_user_email';
const USER_NAME_KEY = 'autoscience_user_name';

export default function TeamPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [reviews, setReviews] = useState<ReviewProposal[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [currentUser, setCurrentUser] = useState<CollaborationUser | null>(null);
  const [loading, setLoading] = useState(true);

  const [userEmail, setUserEmail] = useState('');
  const [userName, setUserName] = useState('');
  const [signingIn, setSigningIn] = useState(false);

  const [memberEmail, setMemberEmail] = useState('');
  const [memberName, setMemberName] = useState('');
  const [memberRole, setMemberRole] = useState('editor');
  const [addingMember, setAddingMember] = useState(false);

  const [commentBody, setCommentBody] = useState('');
  const [commentEntityType, setCommentEntityType] = useState('paper');
  const [commentEntityId, setCommentEntityId] = useState('');
  const [postingComment, setPostingComment] = useState(false);

  const [reviewTitle, setReviewTitle] = useState('');
  const [reviewDescription, setReviewDescription] = useState('');
  const [reviewEntityType, setReviewEntityType] = useState('paper');
  const [reviewEntityId, setReviewEntityId] = useState('');
  const [reviewAssigneeId, setReviewAssigneeId] = useState('');
  const [creatingReview, setCreatingReview] = useState(false);
  const [simulatingReviewId, setSimulatingReviewId] = useState<string | null>(null);
  const [simulationByReview, setSimulationByReview] = useState<
    Record<string, PeerReviewSimulation>
  >({});
  const [notifications, setNotifications] = useState<ReviewNotification[]>([]);
  const [oauthProviders, setOauthProviders] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserEmail(localStorage.getItem(USER_EMAIL_KEY) || '');
      setUserName(localStorage.getItem(USER_NAME_KEY) || '');
    }
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [membersData, commentsData, reviewsData, activityData, me, notifData, oauthData] =
        await Promise.all([
          collaborationApi.listMembers(projectId),
          collaborationApi.listComments(projectId),
          collaborationApi.listReviews(projectId),
          collaborationApi.activity(projectId),
          collaborationApi.me(),
          collaborationApi.notifications(projectId).catch(() => []),
          authApi.oauthProviders().catch(() => ({ providers: [] })),
        ]);
      setMembers(membersData);
      setComments(commentsData);
      setReviews(reviewsData);
      setActivity(activityData);
      setCurrentUser(me);
      setNotifications(notifData);
      setOauthProviders(oauthData.providers);
    } catch (error) {
      console.error('Failed to load team data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  const handleSignIn = async () => {
    if (!userEmail.trim()) return;
    setSigningIn(true);
    try {
      const response = await authApi.token(userEmail.trim(), userName.trim() || undefined);
      setAuthSession(response.access_token, response.user);
      setCurrentUser(response.user);
      await loadData();
    } catch (error) {
      console.error('Sign in failed:', error);
    } finally {
      setSigningIn(false);
    }
  };

  const handleSignOut = () => {
    clearAuthSession();
    setCurrentUser(null);
  };

  const handleOAuthSignIn = async (provider: string) => {
    try {
      const { url, state } = await authApi.oauthAuthorize(provider);
      localStorage.setItem('oauth_provider', provider);
      localStorage.setItem('oauth_state', state);
      localStorage.setItem('oauth_return_to', `/projects/${projectId}/team`);
      window.location.href = url;
    } catch (error) {
      console.error('OAuth redirect failed:', error);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!memberEmail.trim()) return;
    setAddingMember(true);
    try {
      await collaborationApi.addMember({
        project_id: projectId,
        email: memberEmail.trim(),
        display_name: memberName.trim() || undefined,
        role: memberRole,
      });
      setMemberEmail('');
      setMemberName('');
      await loadData();
    } catch (error) {
      console.error('Failed to add member:', error);
    } finally {
      setAddingMember(false);
    }
  };

  const handleCreateComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentBody.trim() || !commentEntityId.trim()) return;
    setPostingComment(true);
    try {
      await collaborationApi.createComment({
        project_id: projectId,
        entity_type: commentEntityType,
        entity_id: commentEntityId.trim(),
        body: commentBody.trim(),
      });
      setCommentBody('');
      await loadData();
    } catch (error) {
      console.error('Failed to post comment:', error);
    } finally {
      setPostingComment(false);
    }
  };

  const handleCreateReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewTitle.trim()) return;
    setCreatingReview(true);
    try {
      await collaborationApi.createReview({
        project_id: projectId,
        title: reviewTitle.trim(),
        description: reviewDescription.trim() || undefined,
        entity_type: reviewEntityType,
        entity_id: reviewEntityId.trim() || undefined,
        assignee_id: reviewAssigneeId || undefined,
      });
      setReviewTitle('');
      setReviewDescription('');
      setReviewEntityId('');
      setReviewAssigneeId('');
      await loadData();
    } catch (error) {
      console.error('Failed to create review:', error);
    } finally {
      setCreatingReview(false);
    }
  };

  const handleSimulateReview = async (proposalId: string) => {
    setSimulatingReviewId(proposalId);
    try {
      const result = await collaborationApi.simulateReview(proposalId);
      setSimulationByReview((prev) => ({ ...prev, [proposalId]: result }));
      await loadData();
    } catch (error) {
      console.error('Failed to simulate review:', error);
    } finally {
      setSimulatingReviewId(null);
    }
  };

  const handleReviewStatus = async (proposalId: string, status: string) => {
    try {
      await collaborationApi.updateReview(proposalId, { status });
      await loadData();
    } catch (error) {
      console.error('Failed to update review:', error);
    }
  };

  const roleVariant = (role: string) => {
    if (role === 'owner') return 'purple' as const;
    if (role === 'editor') return 'info' as const;
    return 'default' as const;
  };

  const reviewStatusVariant = (status: string) => {
    if (status === 'approved') return 'success' as const;
    if (status === 'rejected') return 'danger' as const;
    if (status === 'in_review') return 'info' as const;
    return 'default' as const;
  };

  return (
    <Layout projectId={projectId}>
      <Header
        title="Team Collaboration"
        subtitle={`${members.length} member${members.length !== 1 ? 's' : ''} · ${reviews.length} review${reviews.length !== 1 ? 's' : ''}`}
        actions={
          <div className="hidden lg:flex items-center gap-3">
            <NotificationBell projectId={projectId} />
            <a href={projectsApi.auditExportUrl(projectId, 'json')} download>
              <Button variant="secondary" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export Audit
              </Button>
            </a>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        <Card className="glass p-6">
          <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-4">
            Sign In
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            <Input
              label="Email"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              placeholder="you@example.com"
            />
            <Input
              label="Display Name"
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="Your Name"
            />
            <Button onClick={handleSignIn} disabled={signingIn}>
              {signingIn ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <LogIn className="h-4 w-4 mr-2" />
              )}
              Get Token
            </Button>
            {currentUser && (
              <Button variant="secondary" onClick={handleSignOut}>
                Sign Out
              </Button>
            )}
          </div>
          {oauthProviders.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {oauthProviders.map((provider) => (
                <Button
                  key={provider}
                  variant="secondary"
                  size="sm"
                  onClick={() => handleOAuthSignIn(provider)}
                >
                  Sign in with {provider === 'google' ? 'Google' : 'GitHub'}
                </Button>
              ))}
            </div>
          )}
          {currentUser && (
            <p className="text-xs text-muted-foreground mt-3">
              Signed in as {currentUser.display_name} ({currentUser.email})
            </p>
          )}
        </Card>

        {notifications.length > 0 && (
          <Card className="glass p-6 border-primary/20">
            <h3 className="text-sm font-bold uppercase tracking-widest text-primary mb-4">
              Your Review Assignments ({notifications.length})
            </h3>
            <div className="space-y-2">
              {notifications.map((n) => (
                <div
                  key={n.id}
                  className="flex items-center justify-between p-3 rounded-xl border border-primary/10 bg-primary/5"
                >
                  <div>
                    <p className="text-sm font-medium">{n.title}</p>
                    <p className="text-[10px] text-muted-foreground">{n.status}</p>
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {formatDate(n.created_at)}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <>
            <Card className="glass p-6">
              <div className="flex items-center gap-2 mb-6">
                <Activity size={18} className="text-primary" />
                <h3 className="text-lg font-bold">Activity Feed</h3>
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {activity.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No activity yet.</p>
                ) : (
                  activity.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start justify-between p-3 rounded-xl border border-border/10 bg-white/30"
                    >
                      <div>
                        <p className="text-sm font-medium">{item.summary}</p>
                        <p className="text-[10px] text-muted-foreground">
                          {item.actor} · {item.type}
                        </p>
                      </div>
                      <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {formatDate(item.created_at)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass p-6">
                <div className="flex items-center gap-2 mb-6">
                  <Users size={18} className="text-primary" />
                  <h3 className="text-lg font-bold">Members</h3>
                </div>

                <div className="space-y-3 mb-6">
                  {members.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No members yet. Add yourself as the first member to become owner.
                    </p>
                  ) : (
                    members.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between p-4 rounded-xl border border-border/10 bg-white/30"
                      >
                        <div>
                          <p className="font-bold">{member.display_name}</p>
                          <p className="text-xs text-muted-foreground">{member.email}</p>
                        </div>
                        <Badge variant={roleVariant(member.role)}>{member.role}</Badge>
                      </div>
                    ))
                  )}
                </div>

                <form onSubmit={handleAddMember} className="space-y-4 border-t border-border/10 pt-6">
                  <div className="flex items-center gap-2">
                    <UserPlus size={16} className="text-primary" />
                    <h4 className="font-bold text-sm">Add Member</h4>
                  </div>
                  <Input
                    label="Email"
                    value={memberEmail}
                    onChange={(e) => setMemberEmail(e.target.value)}
                    placeholder="collaborator@example.com"
                    required
                  />
                  <Input
                    label="Display Name"
                    value={memberName}
                    onChange={(e) => setMemberName(e.target.value)}
                    placeholder="Optional"
                  />
                  <Select
                    label="Role"
                    value={memberRole}
                    onChange={(e) => setMemberRole(e.target.value)}
                    options={[
                      { value: 'editor', label: 'Editor' },
                      { value: 'viewer', label: 'Viewer' },
                      { value: 'owner', label: 'Owner' },
                    ]}
                  />
                  <Button type="submit" disabled={addingMember}>
                    {addingMember ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <UserPlus className="h-4 w-4 mr-2" />
                    )}
                    Add Member
                  </Button>
                </form>
              </Card>

              <Card className="glass p-6">
                <div className="flex items-center gap-2 mb-6">
                  <ClipboardList size={18} className="text-primary" />
                  <h3 className="text-lg font-bold">Review Queue</h3>
                </div>

                <form onSubmit={handleCreateReview} className="space-y-4 mb-6">
                  <Input
                    label="Title"
                    value={reviewTitle}
                    onChange={(e) => setReviewTitle(e.target.value)}
                    placeholder="Review manuscript draft"
                    required
                  />
                  <Textarea
                    label="Description"
                    value={reviewDescription}
                    onChange={(e) => setReviewDescription(e.target.value)}
                    rows={2}
                  />
                  <Select
                    label="Entity Type"
                    value={reviewEntityType}
                    onChange={(e) => setReviewEntityType(e.target.value)}
                    options={[
                      { value: 'paper', label: 'Paper' },
                      { value: 'hypothesis', label: 'Hypothesis' },
                      { value: 'manuscript', label: 'Manuscript' },
                      { value: 'idea', label: 'Idea' },
                      { value: 'run', label: 'Run' },
                    ]}
                  />
                  <Input
                    label="Entity ID (optional)"
                    value={reviewEntityId}
                    onChange={(e) => setReviewEntityId(e.target.value)}
                    placeholder="UUID"
                  />
                  <Select
                    label="Assignee (optional)"
                    value={reviewAssigneeId}
                    onChange={(e) => setReviewAssigneeId(e.target.value)}
                    options={[
                      { value: '', label: 'Unassigned' },
                      ...members.map((member) => ({
                        value: member.user_id,
                        label: member.display_name,
                      })),
                    ]}
                  />
                  <Button type="submit" disabled={creatingReview}>
                    {creatingReview ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : null}
                    Create Review
                  </Button>
                </form>

                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {reviews.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No review proposals yet.</p>
                  ) : (
                    reviews.map((review) => (
                      <div
                        key={review.id}
                        className="p-4 rounded-xl border border-border/10 bg-white/30"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-bold text-sm">{review.title}</p>
                          <Badge variant={reviewStatusVariant(review.status)}>
                            {review.status}
                          </Badge>
                        </div>
                        {review.description && (
                          <p className="text-sm text-muted-foreground mb-2">{review.description}</p>
                        )}
                        <p className="text-[10px] text-muted-foreground">
                          by {review.created_by_name} · {formatDate(review.created_at)}
                        </p>
                        {simulationByReview[review.id] && (
                          <div className="mt-3 p-3 rounded-lg border border-border/10 bg-white/20 text-sm space-y-2">
                            <p className="font-medium">{simulationByReview[review.id].summary}</p>
                            <p className="text-[10px] text-muted-foreground uppercase tracking-widest">
                              Recommendation: {simulationByReview[review.id].recommendation}
                            </p>
                          </div>
                        )}
                        {review.status === 'pending' && (
                          <div className="flex flex-wrap gap-2 mt-3">
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => handleSimulateReview(review.id)}
                              disabled={simulatingReviewId === review.id}
                            >
                              {simulatingReviewId === review.id ? (
                                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                              ) : (
                                <Bot className="h-4 w-4 mr-1" />
                              )}
                              Simulate
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => handleReviewStatus(review.id, 'in_review')}
                            >
                              Start Review
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => handleReviewStatus(review.id, 'approved')}
                            >
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              onClick={() => handleReviewStatus(review.id, 'rejected')}
                            >
                              Reject
                            </Button>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </Card>
            </div>

            <Card className="glass p-6">
              <div className="flex items-center gap-2 mb-6">
                <MessageSquare size={18} className="text-primary" />
                <h3 className="text-lg font-bold">Comments</h3>
              </div>

              <form onSubmit={handleCreateComment} className="space-y-4 mb-6">
                <Select
                  label="Entity Type"
                  value={commentEntityType}
                  onChange={(e) => setCommentEntityType(e.target.value)}
                  options={[
                    { value: 'paper', label: 'Paper' },
                    { value: 'hypothesis', label: 'Hypothesis' },
                    { value: 'manuscript', label: 'Manuscript' },
                    { value: 'idea', label: 'Idea' },
                    { value: 'wiki', label: 'Wiki' },
                  ]}
                />
                <Input
                  label="Entity ID"
                  value={commentEntityId}
                  onChange={(e) => setCommentEntityId(e.target.value)}
                  placeholder="UUID of the entity"
                  required
                />
                <Textarea
                  label="Comment"
                  value={commentBody}
                  onChange={(e) => setCommentBody(e.target.value)}
                  placeholder="Share feedback or questions..."
                  rows={3}
                  required
                />
                <Button type="submit" disabled={postingComment}>
                  {postingComment ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <MessageSquare className="h-4 w-4 mr-2" />
                  )}
                  Post Comment
                </Button>
              </form>

              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {comments.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No comments yet.</p>
                ) : (
                  comments.map((comment) => (
                    <div
                      key={comment.id}
                      className="p-4 rounded-xl border border-border/10 bg-white/30"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-bold text-sm">{comment.author_name}</p>
                        <span className="text-[10px] text-muted-foreground">
                          {formatDate(comment.created_at)}
                        </span>
                      </div>
                      <div className="flex gap-2 mb-2">
                        <Badge variant="info">{comment.entity_type}</Badge>
                        <Badge variant="default">{comment.status}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{comment.body}</p>
                      <p className="text-[10px] text-muted-foreground/60 mt-2 font-mono">
                        {comment.entity_id}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </>
        )}
      </div>
    </Layout>
  );
}