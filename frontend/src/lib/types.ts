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
}

export interface Idea {
  id: string;
  project_id: string;
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
  created_at: string;
  updated_at?: string;
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
  labels: string[];
  created_at: string;
  updated_at?: string;
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
  dataset_candidates: any[];
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
  note_type: string;
  entity_id?: string;
  title?: string;
  content?: string;
  linked_notes: string[];
  created_at: string;
  updated_at?: string;
}

export interface ApprovalRequest {
  id: string;
  project_id?: string;
  run_id?: string;
  action_type: string;
  action_description?: string;
  action_payload?: any;
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
  details?: any;
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
