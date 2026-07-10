"""Prompt templates for paper analysis."""

from app.llm.base import Message


def analyze_paper_prompt(
    paper_title: str,
    paper_abstract: str,
    idea_context: str,
    version: str = "1.0",
) -> list[Message]:
    """Generate prompts for analyzing a paper."""
    system = f"""You are a scientific paper analyst. Version: {version}.

Your task is to extract structured information from a scientific paper.

Output a JSON object with the following fields:
- problem: The research problem addressed (string)
- method: The method or approach used (string)
- dataset_sample: The dataset or sample used (string)
- metrics: List of metrics reported (array of strings)
- findings: List of key findings (array of strings)
- limitations: List of limitations acknowledged (array of strings)
- future_work: List of future work directions (array of strings)
- assumptions: List of key assumptions (array of strings)
- relation_to_idea: How this paper relates to the given idea (string)
- key_claims: List of key claims with type and confidence (array of objects with "text", "type", "confidence")
- confidence: Your confidence in this analysis (float 0-1)

Be precise and extract only what is explicitly stated in the paper."""

    user = f"""Paper: {paper_title}

Abstract: {paper_abstract}

Idea context: {idea_context}

Extract structured information from this paper as JSON."""

    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]


def detect_conflicts_prompt(
    papers: list[dict],
    version: str = "1.0",
) -> list[Message]:
    """Generate prompts for detecting conflicts between papers."""
    papers_text = "\n\n".join(
        [
            f"Paper {i+1}: {p.get('title', 'Unknown')}\n"
            f"Finding: {p.get('finding', 'N/A')}\n"
            f"Method: {p.get('method', 'N/A')}\n"
            f"Limitations: {p.get('limitations', 'N/A')}"
            for i, p in enumerate(papers)
        ],
    )

    system = f"""You are a scientific conflict detection expert. Version: {version}.

Your task is to identify scientific tensions, conflicts, and gaps across multiple papers.

Analyze the papers and identify:
1. Finding conflicts: Papers reporting different results for similar problems
2. Method conflicts: Different methods solving the same problem
3. Assumption conflicts: Papers relying on incompatible assumptions
4. Scope conflicts: Methods that work only in narrow conditions
5. Theory-practice conflicts: Strong theory but weak deployment evidence

Output a JSON object with:
- conflicts: Array of conflict objects, each with:
  - type: "finding" | "method" | "assumption" | "scope" | "theory_practice"
  - description: Clear description of the conflict
  - paper_indices: List of paper numbers involved (0-indexed)
  - severity: 0-1 float indicating how significant the conflict is
  - research_opportunity: What research could resolve this conflict
- gaps: Array of gap objects, each with:
  - description: What is missing or underexplored
  - type: "missing_baseline" | "limited_validation" | "unexplored_condition" | "other"
  - opportunity: Research opportunity arising from this gap"""

    user = f"""Analyze these papers for conflicts and gaps:

{papers_text}

Identify scientific tensions and research opportunities as JSON."""

    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]


def generate_questions_prompt(
    conflicts: list[dict],
    idea_context: str,
    version: str = "1.0",
) -> list[Message]:
    """Generate prompts for generating research questions from conflicts."""
    conflicts_text = "\n\n".join(
        [
            f"Conflict {i+1}: [{c.get('type', 'unknown')}] {c.get('description', '')}"
            for i, c in enumerate(conflicts)
        ],
    )

    system = f"""You are a research question generator. Version: {version}.

Your task is to generate high-quality research questions from scientific conflicts.

Good research questions:
- Are specific and testable
- Address a clear gap or conflict
- Are motivated by the evidence
- Lead to actionable hypotheses

Output a JSON object with:
- questions: Array of question objects, each with:
  - question: The research question (string)
  - source_conflict_indices: Which conflicts motivated this question (array of ints)
  - novelty: Estimated novelty 0-1 (float)
  - feasibility: Estimated feasibility 0-1 (float)
  - rationale: Why this question is worth investigating (string)

Generate at least 10 diverse questions."""

    user = f"""Idea context: {idea_context}

Conflicts identified:
{conflicts_text}

Generate research questions that could resolve these conflicts and advance understanding."""

    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]


def generate_hypothesis_prompt(
    question: str,
    context: str,
    version: str = "1.0",
) -> list[Message]:
    """Generate prompts for converting a question into a hypothesis."""
    system = f"""You are a hypothesis formation expert. Version: {version}.

Your task is to convert a research question into a testable hypothesis.

A good hypothesis:
- Makes a specific, falsifiable claim
- Identifies independent and dependent variables
- Specifies expected direction of effect
- Defines failure conditions
- Is grounded in the available evidence

Output a JSON object with:
- statement: Clear hypothesis statement (string)
- independent_variable: What is being manipulated or compared (string)
- dependent_variable: What is being measured (string)
- context: The domain and conditions (string)
- expected_direction: Expected relationship (string)
- baseline: What is being compared against (string)
- metric: How to measure success (string)
- dataset_requirement: What data is needed (string)
- failure_condition: What would disprove this hypothesis (string)
- confidence: Your confidence in this hypothesis (float 0-1)"""

    user = f"""Research question: {question}

Context: {context}

Convert this into a testable hypothesis with all required fields as JSON."""

    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]


def score_idea_prompt(
    idea_text: str,
    papers: list[dict] | None = None,
    conflicts: list[dict] | None = None,
    version: str = "1.0",
) -> list[Message]:
    """Generate prompts for scoring an idea."""
    papers_text = ""
    if papers:
        papers_text = "\nRelevant papers:\n" + "\n".join(
            [f"- {p.get('title', 'Unknown')}" for p in papers[:10]],
        )

    conflicts_text = ""
    if conflicts:
        conflicts_text = "\nConflicts identified:\n" + "\n".join(
            [f"- [{c.get('type')}] {c.get('description', '')}" for c in conflicts[:5]],
        )

    system = f"""You are an idea scoring expert. Version: {version}.

Your task is to score a research idea on multiple dimensions.

Score each dimension from 0 to 10:
- novelty: How original is this idea? (0 = well-known, 10 = truly novel)
- feasibility: How realistic is this to implement? (0 = impossible, 10 = straightforward)
- importance: How significant is the problem? (0 = trivial, 10 = critical)
- evidence_support: How well supported by existing literature? (0 = no support, 10 = strong support)
- validation_clarity: How clearly can this be tested? (0 = vague, 10 = crystal clear)
- differentiation: How different from existing work? (0 = duplicate, 10 = unique approach)
- data_availability: How available is the needed data? (0 = unavailable, 10 = freely available)
- skill_leverage: How much can existing skills help? (0 = none, 10 = directly applicable)
- user_alignment: How aligned with user goals? (0 = misaligned, 10 = perfect match)
- prior_art_risk: Risk of overlapping with existing work (0 = high risk, 10 = no risk)
- safety_risk: Risk of negative consequences (0 = high risk, 10 = no risk)
- cost_risk: Resource cost risk (0 = very expensive, 10 = very cheap)

Output a JSON object with all scores and a rationale."""

    user = f"""Idea: {idea_text}
{papers_text}
{conflicts_text}

Score this idea on all dimensions as JSON."""

    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]


def create_skill_prompt(
    workflow_description: str,
    success_cases: list[str],
    version: str = "1.0",
) -> list[Message]:
    """Generate prompts for creating a skill from successful workflows."""
    cases_text = "\n".join([f"- {case}" for case in success_cases])

    system = f"""You are a skill creation expert. Version: {version}.

Your task is to extract a reusable skill from successful research workflows.

A good skill should:
- Have a clear purpose
- Define specific trigger conditions
- List required inputs
- Provide step-by-step procedure
- Specify expected outputs
- Be general enough to apply to new situations

Output a JSON object with:
- name: Short descriptive name (string)
- skill_type: "planning" | "functional" | "atomic" | "domain" (string)
- purpose: What this skill accomplishes (string)
- trigger_conditions: When to use this skill (array of strings)
- inputs: What data is needed (array of strings)
- procedure: Step-by-step instructions (array of strings)
- outputs: What this skill produces (array of strings)"""

    user = f"""Workflow description:
{workflow_description}

Success cases:
{cases_text}

Extract a reusable skill from these examples as JSON."""

    return [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]
