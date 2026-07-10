// TypeScript types for API responses

export interface Project {
  id: string;
  name: string;
  domain: string;
  description?: string;
  subject_scope: string[];
  out_of_scope: string[];
  default_flexibility: number;
  idle_research_enabled: boolean;
  idle_trigger_minutes: number;
  max_idle_cycles_per_day: number;
  max_sources_per_cycle: number;
  approval_required_for_external_actions: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ProjectStats {
  total_ideas: number;
  active_ideas: number;
  rejected_ideas: number;
  total_runs: number;
  active_runs: number;
  total_papers: number;
  total_skills: number;
  total_conflicts: number;
  total_questions: number;
  total_hypotheses: number;
  total_reports: number;
  total_wiki_notes: number;
  total_clusters: number;
  latest_cognitive_entropy?: number;
  latest_cognitive_mode?: string;
  latest_focus_score?: number;
  latest_focus_label?: string;
  active_run_phase?: string | null;
}

export interface Idea {
  id: string;
  project_id: string;
  parent_idea_id?: string | null;
  origin: string;
  initial_text: string;
  current_text: string;
  flexibility?: number;
  status: string;
  classification?: string;
  overall_score?: number;
  classification_reason?: string;
  created_at: string;
  updated_at?: string;
}

export interface IdeaScore {
  novelty: number;
  feasibility: number;
  importance: number;
  evidence_support: number;
  validation_clarity: number;
  differentiation: number;
  data_availability: number;
  skill_leverage: number;
  user_alignment: number;
  prior_art_risk: number;
  safety_risk: number;
  cost_risk: number;
  overall_value: number;
  scoring_rationale?: string;
  cost_usd?: number;
}

export interface ResearchRun {
  id: string;
  project_id: string;
  idea_id?: string;
  run_type: string;
  state: string;
  started_at?: string;
  completed_at?: string;
  max_minutes: number;
  max_sources: number;
  max_cost_usd: number;
  cognitive_entropy?: number;
  cognitive_mode?: string;
  created_at: string;
  updated_at?: string;
}

export interface SemanticSearchResult {
  paper_id: string;
  title: string;
  year?: number;
  doi?: string;
  score: number;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResult[];
}

export interface Paper {
  id: string;
  project_id: string;
  title: string;
  authors: string[];
  year?: number;
  doi?: string;
  abstract?: string;
  venue?: string;
  url?: string;
  citation_count?: number;
  paper_type?: string;
  source_connector?: string;
  source_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface PaperCluster {
  id: string;
  project_id: string;
  name?: string;
  description?: string;
  cluster_type?: string;
  paper_ids: string[];
  representative_paper_id?: string;
  labels: ClusterLabel[];
  created_at: string;
  updated_at?: string;
}

export interface ClusterLabel {
  label: string;
  rationale?: string;
}

export interface ClusterConflict {
  id: string;
  project_id: string;
  cluster_id?: string;
  conflict_type: string;
  description: string;
  supporting_papers: string[];
  opposing_papers: string[];
  research_opportunity?: string;
  severity?: number;
  created_at: string;
  updated_at?: string;
}

export interface ResearchQuestion {
  id: string;
  project_id: string;
  idea_id?: string;
  run_id?: string;
  question: string;
  source_conflicts: string[];
  source_gaps: string[];
  rank?: number;
  status: string;
  rejection_reason?: string;
  created_at: string;
  updated_at?: string;
}

export interface Hypothesis {
  id: string;
  project_id: string;
  idea_id?: string;
  question_id?: string;
  statement: string;
  independent_variable?: string;
  dependent_variable?: string;
  context?: string;
  expected_direction?: string;
  baseline?: string;
  metric?: string;
  dataset_requirement?: string;
  failure_condition?: string;
  confidence?: number;
  version: number;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface ValidationPlan {
  id: string;
  hypothesis_id: string;
  dataset_candidates: DatasetCandidate[];
  benchmark_candidates: string[];
  baselines: string[];
  metrics: string[];
  experimental_design?: string;
  statistical_tests: string[];
  simulation_option?: string;
  expected_artifacts: string[];
  difficulty_estimate?: number;
  cost_estimate?: number;
  feasibility_score?: number;
  created_at: string;
  updated_at?: string;
}

export interface DatasetCandidate {
  name: string;
  [key: string]: unknown;
}

export interface Skill {
  id: string;
  project_id?: string;
  name: string;
  skill_type: string;
  purpose?: string;
  trigger_conditions: string[];
  inputs: string[];
  procedure: string[];
  outputs: string[];
  status: string;
  version: string;
  times_used: number;
  successful_uses: number;
  average_score_improvement?: number;
  failure_cases: string[];
  domains_where_it_works: string[];
  domains_where_it_fails: string[];
  created_at: string;
  updated_at?: string;
}

export interface Manuscript {
  id: string;
  project_id: string;
  run_id?: string;
  title: string;
  content_latex?: string;
  version: number;
  status: string;
  compiled_url?: string;
  bibtex?: string;
  created_at: string;
  updated_at?: string;
}

export interface ResearchReport {
  id: string;
  project_id: string;
  run_id?: string;
  idea_id?: string;
  title?: string;
  content_markdown?: string;
  content_html?: string;
  report_type?: string;
  created_at: string;
  updated_at?: string;
}

export interface KnowledgeNote {
  id: string;
  project_id: string;
  run_id?: string;
  note_type: string;
  entity_id?: string;
  title?: string;
  content?: string;
  linked_notes: string[];
  created_at: string;
  updated_at?: string;
}

export interface GeneratedIdea {
  title: string;
  description: string;
  novelty?: number;
  importance?: number;
}

export interface ApprovalRequest {
  id: string;
  project_id?: string;
  run_id?: string;
  action_type: string;
  action_description?: string;
  action_payload?: Record<string, unknown>;
  status: string;
  reviewer_notes?: string;
  resolved_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface AuditLog {
  id: string;
  project_id?: string;
  run_id?: string;
  event_type: string;
  actor?: string;
  action?: string;
  details?: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

export interface ResearchState {
  run_id: string;
  project_id: string;
  idea_id?: string;
  run_type: string;
  current_phase: string;
  state: string;
  original_idea: string;
  current_idea: string;
  flexibility: number;
  cost_usd: number;
  papers: Paper[];
  clusters: PaperCluster[];
  conflicts: ClusterConflict[];
  questions: ResearchQuestion[];
  hypotheses: Hypothesis[];
  scores: IdeaScore[];
  current_classification?: string;
  skills_used: string[];
  skills_created: string[];
}

export interface AppEvent {
  id: string;
  event_type: string;
  actor?: string;
  timestamp?: string;
  details?: Record<string, unknown>;
}

export interface ToolCall {
  id: string;
  run_id?: string;
  tool_name: string;
  agent_role?: string;
  input_json?: Record<string, unknown>;
  output_json?: Record<string, unknown>;
  duration_ms?: number;
  success: boolean;
  error_message?: string;
  timestamp?: string;
}

export interface PaperComparisonEntry {
  paper_id: string;
  title: string;
  year?: number;
  authors: string[];
  doi?: string;
  abstract?: string;
  problem?: string | null;
  method?: string | null;
  findings: string[];
  limitations: string[];
  assumptions?: string[];
  key_claims?: string[];
  metrics?: string[];
  confidence?: number | null;
}

export interface PaperComparison {
  papers: PaperComparisonEntry[];
  dimensions: string[];
  summary: {
    count: number;
    methods: (string | null | undefined)[];
    shared_limitations: string[];
  };
}

export interface CitationGraphNode {
  id: string;
  label: string;
  year?: number;
  doi?: string;
}

export interface CitationGraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface CitationGraph {
  nodes: CitationGraphNode[];
  edges: CitationGraphEdge[];
}

export interface WikiSemanticResult {
  note_id: string;
  title?: string;
  note_type: string;
  run_id?: string;
  score: number;
  snippet: string;
}

export interface WikiSemanticSearchResponse {
  query: string;
  results: WikiSemanticResult[];
}

export interface Comment {
  id: string;
  project_id: string;
  user_id: string;
  author_name: string;
  entity_type: string;
  entity_id: string;
  body: string;
  status: string;
  created_at: string;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface CollaborationUser {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface ReviewProposal {
  id: string;
  project_id: string;
  created_by_id: string;
  created_by_name: string;
  assignee_id: string | null;
  assignee_name: string | null;
  title: string;
  description: string | null;
  entity_type: string;
  entity_id: string | null;
  status: string;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  type: string;
  actor: string;
  summary: string;
  created_at: string;
  details: Record<string, unknown>;
}

export interface ArxivSearchResult {
  source: string;
  source_id: string;
  title: string;
  authors: string[];
  year: number | null;
  doi: string | null;
  abstract: string | null;
  url: string | null;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: CollaborationUser;
}

export interface ManuscriptTemplate {
  id: string;
  name: string;
  checklist: string[];
}

export interface DomainPack {
  id: string;
  name: string;
  domain_label: string;
  description: string;
  subject_scope: string[];
  validation_methods: string[];
  preferred_connectors: string[];
}

export interface PeerReviewSimulation {
  summary: string;
  strengths: string[];
  weaknesses: string[];
  questions: string[];
  recommendation: string;
  confidence: number;
  simulated: boolean;
  llm_used: boolean;
}

export interface ReviewNotification {
  id: string;
  proposal_id: string;
  project_id: string;
  title: string;
  status: string;
  assignee_id: string;
  created_at: string;
  read: boolean;
}

export interface WikiGraphNode {
  id: string;
  title: string;
  note_type: string;
  run_id: string | null;
  entity_id: string | null;
}

export interface WikiGraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  label?: string;
}

export interface WikiGraph {
  project_id: string;
  nodes: WikiGraphNode[];
  edges: WikiGraphEdge[];
  stats: { note_count: number; edge_count: number; run_count: number };
}

export interface PowerAnalysisResult {
  test_type: string;
  effect_size: number;
  alpha: number;
  power: number;
  sample_size_per_group: number | null;
  total_sample_size: number | null;
  recommendation: string;
}

export interface PlotlySandboxResult {
  title: string;
  html: string;
  duration_ms: number;
}

export interface OAuthProvidersResponse {
  providers: string[];
}

export interface SkillPerformanceStats {
  total_skills_evaluated: number;
  total_usage: number;
  avg_success_rate: number;
  at_risk_count: number;
  min_success_rate_threshold: number;
  min_usage_for_evaluation: number;
  deprecated_grace_days: number;
}

export interface SkillEvaluateResult {
  evaluated_count: number;
  deprecated: string[];
  retired: string[];
  errors: string[];
  summary: string;
  dry_run: boolean;
}

export interface SkillEvalHistoryEntry {
  id: string;
  timestamp: string;
  event_type: string;
  action: string | null;
  details: {
    evaluated_count?: number;
    deprecated_count?: number;
    retired_count?: number;
    error_count?: number;
    dry_run?: boolean;
    summary?: string;
  };
}

export interface PerformanceHistoryEntry {
  timestamp: string;
  skill_id: string;
  rating: number;
  success_rate: number | null;
  avg_score_improvement: number | null;
  times_used: number | null;
  recommendation: string | null;
}

// ── Health ──────────────────────────────────────────────────────────────

export interface HealthResult {
  status: string; // "healthy" | "unhealthy" | "not_configured" | "not_available"
  error?: string | null;
  details: Record<string, any>;
}

export interface OverallHealth {
  status: string; // "healthy" | "degraded" | "unhealthy"
  version: string;
  checks: {
    database: HealthResult;
    redis: HealthResult;
    llm: HealthResult;
    connectors: HealthResult;
  };
}

/** Circuit-breaker state for a single connector endpoint. */
export interface ConnectorCircuitBreaker {
  /** "closed" (normal), "open" (tripped, requests blocked), "half_open" (recovering). */
  state: 'closed' | 'open' | 'half_open';
  /** Consecutive failure count (resets on success). */
  failure_count: number;
  /** Seconds remaining until the circuit transitions from open to half-open. */
  cooldown_remaining: number;
}
