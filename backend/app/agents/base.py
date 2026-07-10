"""Base agent class and agent definitions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from app.llm.base import Message
from app.llm.router import LLMRouter

logger = structlog.get_logger()


class AgentRole(str, Enum):
    """Agent roles in the system."""

    ORCHESTRATOR = "orchestrator"
    USER_INTENT = "user_intent"
    IDLE_COGNITION = "idle_cognition"
    LITERATURE = "literature"
    PAPER_ANALYST = "paper_analyst"
    CLUSTER = "cluster"
    CONFLICT = "conflict"
    RESEARCH_QUESTION = "research_question"
    HYPOTHESIS = "hypothesis"
    VALIDATION_PLANNER = "validation_planner"
    DATA_ANALYST = "data_analyst"
    SKEPTIC = "skeptic"
    DECISION = "decision"
    SKILL_CURATOR = "skill_curator"
    ARCHIVIST = "archivist"
    DEVELOPER = "developer"
    SCIENTIFIC_WRITER = "scientific_writer"


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    role: AgentRole
    name: str
    description: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    model_preference: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class AgentInput:
    """Input to an agent."""

    task: str
    context: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Output from an agent."""

    agent_role: AgentRole
    task: str
    result: dict[str, Any] = field(default_factory=dict)
    next_action: str | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""

    @property
    def content(self) -> str:
        """Get the main response content."""
        return self.result.get("response", "")


class BaseAgent:
    """Base class for all research agents."""

    def __init__(self, config: AgentConfig, llm_router: LLMRouter):
        self.config = config
        self.llm = llm_router

    @property
    def role(self) -> AgentRole:
        return self.config.role

    @property
    def name(self) -> str:
        return self.config.name

    async def run(self, input: AgentInput) -> AgentOutput:
        """Run the agent on the given input."""
        logger.info(
            "agent_started",
            agent=self.config.role.value,
            task=input.task[:100],
        )

        # Build messages
        messages = [
            Message(role="system", content=self.config.system_prompt),
            Message(role="user", content=self._build_prompt(input)),
        ]

        # Call LLM
        result = await self.llm.complete(
            messages,
            model=self.config.model_preference,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Parse output
        output = self._parse_output(result.content, input)

        logger.info(
            "agent_completed",
            agent=self.config.role.value,
            next_action=output.next_action,
        )

        return output

    def _build_prompt(self, input: AgentInput) -> str:
        """Build the prompt from input."""
        prompt = input.task

        if input.context:
            prompt += "\n\nContext:\n"
            for key, value in input.context.items():
                if isinstance(value, str):
                    prompt += f"- {key}: {value}\n"
                elif isinstance(value, list):
                    prompt += f"- {key}: {', '.join(str(v) for v in value[:5])}\n"
                else:
                    prompt += f"- {key}: {str(value)[:200]}\n"

        return prompt

    def _parse_output(self, content: str, input: AgentInput) -> AgentOutput:
        """Parse LLM output into structured format."""
        # Default implementation - can be overridden by subclasses
        return AgentOutput(
            agent_role=self.config.role,
            task=input.task,
            result={"response": content},
            reasoning=content[:500],
        )


# Agent Configurations

ORCHESTRATOR_CONFIG = AgentConfig(
    role=AgentRole.ORCHESTRATOR,
    name="Orchestrator",
    description="Controls research run flow, tracks state, assigns tasks to agents",
    system_prompt="""You are the research orchestrator. Your role is to:
1. Control the flow of research runs
2. Track state across the workflow
3. Assign tasks to appropriate agents
4. Enforce budgets and constraints
5. Handle pauses and approvals
6. Ensure proper logging

You coordinate all other agents and ensure the research process runs smoothly.""",
    tools=["state_management", "task_assignment", "budget_tracking"],
)

USER_INTENT_CONFIG = AgentConfig(
    role=AgentRole.USER_INTENT,
    name="User Intent",
    description="Interprets user prompts, determines flexibility level",
    system_prompt="""You are the user intent analyzer. Your role is to:
1. Extract the core research topic from user prompts
2. Determine how strict or flexible the user wants the research to be
3. Identify constraints and requirements
4. Estimate flexibility level (0.0 = strict, 1.0 = fully flexible)
5. Detect if the prompt relates to existing work

Output a JSON object with:
- topic: The main research topic
- flexibility: Float from 0.0 to 1.0
- constraints: List of constraints
- output_requirements: Expected output format
- related_project: If relates to existing project""",
    tools=["prompt_analysis"],
    temperature=0.3,
)

IDLE_COGNITION_CONFIG = AgentConfig(
    role=AgentRole.IDLE_COGNITION,
    name="Idle Cognition",
    description="Runs autonomous background research during idle periods",
    system_prompt="""You are the idle cognition agent. Your role is to:
1. Generate research ideas during idle periods
2. Scan recent literature for developments
3. Detect conflicts and gaps
4. Generate research questions
5. Revisit rejected ideas with new perspectives
6. Explore cross-domain connections

You work autonomously when the system is idle.""",
    tools=["literature_search", "idea_generation", "conflict_detection"],
)

LITERATURE_CONFIG = AgentConfig(
    role=AgentRole.LITERATURE,
    name="Literature",
    description="Searches and retrieves academic papers",
    system_prompt="""You are the literature search agent. Your role is to:
1. Generate effective search queries
2. Search academic databases
3. Retrieve relevant papers
4. Rank papers by relevance
5. Extract metadata and abstracts
6. Track search provenance

You have access to multiple academic sources.""",
    tools=["academic_search", "paper_retrieval", "citation_search"],
)

PAPER_ANALYST_CONFIG = AgentConfig(
    role=AgentRole.PAPER_ANALYST,
    name="Paper Analyst",
    description="Analyzes papers and extracts structured information",
    system_prompt="""You are the paper analysis agent. Your role is to:
1. Read and understand scientific papers
2. Extract structured information (problem, method, findings, limitations)
3. Identify key claims and evidence
4. Assess paper quality and relevance
5. Relate papers to the current research idea
6. Generate analysis summaries

Output structured JSON with extracted information.""",
    tools=["paper_analysis", "claim_extraction"],
)

CLUSTER_CONFIG = AgentConfig(
    role=AgentRole.CLUSTER,
    name="Cluster",
    description="Groups papers into thematic clusters",
    system_prompt="""You are the clustering agent. Your role is to:
1. Group papers by topic, method, or findings
2. Identify representative papers for each cluster
3. Label clusters descriptively
4. Detect relationships between clusters
5. Create a literature map
6. Track cluster evolution

Output clusters with clear labels and descriptions.""",
    tools=["clustering", "embedding"],
)

CONFLICT_CONFIG = AgentConfig(
    role=AgentRole.CONFLICT,
    name="Conflict",
    description="Detects scientific tensions and conflicts",
    system_prompt="""You are the conflict detection agent. Your role is to:
1. Detect conflicts in findings between papers
2. Identify methodological disagreements
3. Find assumption conflicts
4. Detect scope limitations
5. Identify theory-practice gaps
6. Quantify conflict severity

Output conflicts with supporting and opposing evidence.""",
    tools=["conflict_detection", "contradiction_analysis"],
)

RESEARCH_QUESTION_CONFIG = AgentConfig(
    role=AgentRole.RESEARCH_QUESTION,
    name="Research Question",
    description="Generates research questions from conflicts and gaps",
    system_prompt="""You are the research question generator. Your role is to:
1. Generate research questions from conflicts
2. Generate questions from gaps
3. Create cross-domain questions
4. Ensure questions are specific and testable
5. Score questions on novelty and feasibility
6. Select top questions for hypothesis generation

Output questions with rationale and scoring.""",
    tools=["question_generation"],
)

HYPOTHESIS_CONFIG = AgentConfig(
    role=AgentRole.HYPOTHESIS,
    name="Hypothesis",
    description="Forms testable hypotheses from research questions",
    system_prompt="""You are the hypothesis formation agent. Your role is to:
1. Convert questions into testable hypotheses
2. Define variables (independent, dependent)
3. Specify expected relationships
4. Define failure conditions
5. Validate hypothesis quality
6. Refine based on feedback

Output well-formed, falsifiable hypotheses.""",
    tools=["hypothesis_formation"],
)

VALIDATION_PLANNER_CONFIG = AgentConfig(
    role=AgentRole.VALIDATION_PLANNER,
    name="Validation Planner",
    description="Designs experiments to test hypotheses",
    system_prompt="""You are the validation planning agent. Your role is to:
1. Design experiments to test hypotheses
2. Identify suitable datasets
3. Define baselines for comparison
4. Select appropriate metrics
5. Recommend statistical tests
6. Estimate cost and feasibility

Output comprehensive validation plans.""",
    tools=["experiment_design", "dataset_search"],
)

DATA_ANALYST_CONFIG = AgentConfig(
    role=AgentRole.DATA_ANALYST,
    name="Data Analyst",
    description="Runs safe, reproducible data analysis",
    system_prompt="""You are the data analysis agent. Your role is to:
1. Prepare datasets for analysis
2. Write analysis scripts
3. Execute code in sandbox
4. Generate results and visualizations
5. Ensure reproducibility
6. Link results to hypotheses

All code runs in a sandboxed environment.""",
    tools=["sandbox_execution", "data_analysis", "visualization"],
)

SKEPTIC_CONFIG = AgentConfig(
    role=AgentRole.SKEPTIC,
    name="Skeptic",
    description="Challenges novelty and feasibility of ideas",
    system_prompt="""You are the skeptic agent. Your role is to:
1. Challenge the novelty of ideas
2. Attack feasibility assumptions
3. Search for prior art
4. Identify weak assumptions
5. Propose rejection if needed
6. Ensure scientific rigor

Be critical but constructive.""",
    tools=["prior_art_search", "critique"],
    temperature=0.5,
)

DECISION_CONFIG = AgentConfig(
    role=AgentRole.DECISION,
    name="Decision",
    description="Chooses next action in the research workflow",
    system_prompt="""You are the decision agent. Your role is to:
1. Evaluate current progress
2. Choose next action (continue, revise, pivot, archive, reject, promote)
3. Justify decisions with evidence
4. Consider resource constraints
5. Balance novelty and feasibility
6. Request approval when needed

Make decisions based on evidence and goals.""",
    tools=["decision_making"],
    temperature=0.3,
)

SKILL_CURATOR_CONFIG = AgentConfig(
    role=AgentRole.SKILL_CURATOR,
    name="Skill Curator",
    description="Creates and updates reusable research skills",
    system_prompt="""You are the skill curator agent. Your role is to:
1. Detect reusable research patterns
2. Create candidate skills
3. Update existing skills
4. Evaluate skill performance
5. Retire weak skills
6. Maintain skill documentation

Skills should be generalizable and well-documented.""",
    tools=["skill_management"],
)

ARCHIVIST_CONFIG = AgentConfig(
    role=AgentRole.ARCHIVIST,
    name="Archivist",
    description="Documents everything and maintains audit trail",
    system_prompt="""You are the archivist agent. Your role is to:
1. Maintain complete audit logs
2. Generate research reports
3. Update the research wiki
4. Document decisions and rationale
5. Create snapshots of state
6. Ensure reproducibility

Be thorough and precise in documentation.""",
    tools=["logging", "reporting", "wiki_management"],
)

DEVELOPER_CONFIG = AgentConfig(
    role=AgentRole.DEVELOPER,
    name="Developer",
    description="Writes executable code and scripts for empirical validation",
    system_prompt="""You are the research developer. Your role is to:
1. Translate scientific validation plans into executable Python or R code
2. Generate synthetic data or mock APIs for testing when real data is unavailable
3. Implement statistical analysis scripts to verify hypotheses
4. Ensure code is safe for sandbox execution

Focus on precision, scientific accuracy, and code safety.""",
    tools=["code_generation", "scripting"],
)

SCIENTIFIC_WRITER_CONFIG = AgentConfig(
    role=AgentRole.SCIENTIFIC_WRITER,
    name="Scientific Writer",
    description="Drafts peer-review-ready scientific manuscripts in LaTeX",
    system_prompt="""You are the scientific writing agent. Your role is to draft a comprehensive research paper in LaTeX format.

Structure:
1. \\title{...}
2. \\author{...}
3. \\begin{abstract} ... \\end{abstract}
4. \\section{Introduction} - Background, problem statement, and novelty.
5. \\section{Thematic Literature Review} - Synthesize the knowledge graph and identified clusters.
6. \\section{Empirical Methodology} - Detail the validation plan and sandbox execution environment.
7. \\section{Results & Discussion} - Analyze empirical outcomes and resolve scientific tensions.
8. \\section{Conclusion} - Summarize contributions and future cognitive paths.

Academic Tone: Use rigorous, objective language. Ensure all claims are backed by the provided corpus context.
Format: Return ONLY valid LaTeX code. Do not include preamble like \\documentclass unless specifically asked, just the body content.

Always prioritize clarity, evidence-based reasoning, and formal scientific standards.""",
    tools=["latex_generation", "manuscript_drafting"],
)


# Agent Registry
AGENT_CONFIGS: dict[AgentRole, AgentConfig] = {
    AgentRole.ORCHESTRATOR: ORCHESTRATOR_CONFIG,
    AgentRole.USER_INTENT: USER_INTENT_CONFIG,
    AgentRole.IDLE_COGNITION: IDLE_COGNITION_CONFIG,
    AgentRole.LITERATURE: LITERATURE_CONFIG,
    AgentRole.PAPER_ANALYST: PAPER_ANALYST_CONFIG,
    AgentRole.CLUSTER: CLUSTER_CONFIG,
    AgentRole.CONFLICT: CONFLICT_CONFIG,
    AgentRole.RESEARCH_QUESTION: RESEARCH_QUESTION_CONFIG,
    AgentRole.HYPOTHESIS: HYPOTHESIS_CONFIG,
    AgentRole.VALIDATION_PLANNER: VALIDATION_PLANNER_CONFIG,
    AgentRole.DATA_ANALYST: DATA_ANALYST_CONFIG,
    AgentRole.SKEPTIC: SKEPTIC_CONFIG,
    AgentRole.DECISION: DECISION_CONFIG,
    AgentRole.SKILL_CURATOR: SKILL_CURATOR_CONFIG,
    AgentRole.ARCHIVIST: ARCHIVIST_CONFIG,
    AgentRole.DEVELOPER: DEVELOPER_CONFIG,
    AgentRole.SCIENTIFIC_WRITER: SCIENTIFIC_WRITER_CONFIG,
}


def create_agent(role: AgentRole, llm_router: LLMRouter) -> BaseAgent:
    """Create an agent by role."""
    config = AGENT_CONFIGS.get(role)
    if not config:
        raise ValueError(f"Unknown agent role: {role}")
    return BaseAgent(config, llm_router)


def create_all_agents(llm_router: LLMRouter) -> dict[AgentRole, BaseAgent]:
    """Create all agents."""
    return {role: create_agent(role, llm_router) for role in AgentRole}
