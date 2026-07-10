---
name: Autoscience
version: 1.2.0
soul: "Persistent Scientific Cognition — Architectural Minimalism meet Intellectual Gravitas."
colors:
  primary: "#d97706"      # Intellectual Amber (Thought, Synthesis)
  secondary: "#44403c"    # Stone Charcoal (Authority, Infrastructure)
  tertiary: "#c2410c"     # Burnt Terracotta (Action, Validation)
  background:
    light: "#fdfaf6"      # Warm Bone/Paper
    dark: "#1c1917"       # Stone Obsidian
  foreground:
    light: "#1c1917"      # Deep Stone
    dark: "#fdfaf6"       # Soft Paper
  success: "#15803d"      # Forest Green
  error: "#b91c1c"        # Crimson Earth
  warning: "#b45309"      # Ochre Glow
typography:
  headings:
    fontFamily: "Inter, system-ui"
    weight: 800
  body:
    fontFamily: "Inter, system-ui"
    weight: 500
  mono:
    fontFamily: "Monaco, Menlo, monospace"
    weight: 400
rounded:
  sm: 6px
  md: 10px
  lg: 16px
spacing:
  unit: 4px
  container: 24px
  gutter: 20px
glass:
  blur: "12px"
  opacity: "0.5"
  border: "rgba(68, 64, 60, 0.1)"
---

# Autoscience: Comprehensive System Design

## 1. Design Philosophy: The "Scientific Hearth" (Amber Edition)
Autoscience is a **Cognitive Laboratory**. The visual language uses the **Amber Synthesis** system to foster deep, long-horizon focus with a warm, readable aesthetic.

- **Readability:** High-contrast but softened tones (Stone vs Amber) reduce ocular fatigue during 8+ hour research cycles.
- **Warmth:** Moves away from "Silicon Blue" towards "Intellectual Amber," signaling a space for human-AI collaboration.
- **Clarity:** Enhanced spacing and larger radii create a softer, more organic interface that feels approachable yet rigorous.

## 2. Visual System (Tokens Rationale)
### 2.1 The Amber Palette
- **Intellectual Amber (Primary):** The color of focused neurons. Used for active states and primary synthesis triggers.
- **Stone Charcoal (Secondary):** The grounding element. Used for navigation and structural borders to signal permanence.
- **Burnt Terracotta (Tertiary):** Used for **Hypotheses** and **Validation**, representing the heat of testing and empirical "firing."
- **Semantic Feedback:** Low-saturation Forest and Crimson tones ensure alerts are clear without being visually aggressive.

### 2.2 Glass & Texture
- **The Parchment Layer:** UI surfaces use lower glass opacities and warm backdrops to mimic the feel of digital parchment.
- **Radii:** Increased to `10px` and `16px` for a modern, friendly, and cohesive feel.

### 2.3 Calm Motion
- **Hearth Glow:** Transitions are slightly slower (400ms) with ease-in-out curves to maintain a sense of laboratory calm.
- **Ambient Sweeps:** Background glows use deep warm tints (`amber/primary`) to simulate a living, breathing thought environment.

### 2.4 Typography
- **Inter:** Chosen for its neutral, highly readable character in data-dense tables.
- **Monaco/Menlo:** Used for LaTeX artifacts, code sandboxes, and raw search queries to signal "System Level" interaction.

## 3. Core Architectural Design

### 3.1 Persistence: Database-First State
Contrary to typical LLM apps, Autoscience treats the database as the **Source of Truth**, not the prompt history.
- **Design Pattern:** The `ResearchState` object is mirrored in PostgreSQL.
- **Benefit:** Allows "Temporal Navigation"—the user can rewind to any step in a research cycle and pivot from there.

### 3.2 Orchestration: Handoff-Driven Autonomy
The system uses a **Handoff Model** between 15 specialized agents.
- **The Orchestrator:** Acts as the "Chief of Staff," managing the `ResearchWorkflow`.
- **The Agents:** Stateless workers that consume a task, perform tool calls, and update the global state.
- **Strengthening Move:** Implement **Strict Protocol Validation** between agent handoffs to prevent "Hallucination Drift."

### 3.3 Intelligence: The Evidence Ledger
The system doesn't just "read" papers; it "extracts and links."
- **Conflict Engine:** Compares extracted claims across multiple papers to find "Scientific Friction."
- **Scoring Engine:** Uses a **Weighted Utility Function** (defined in `scoring.py`) to provide an objective value to every idea.

## 4. Strengthening the System: Design Evolutions

### 4.1 Cognitive Health Dashboard
**Analysis:** Currently, the system shows "what it's doing," but not "how healthy its research direction is."
**Design Fix:** Introduce a **Research Entropy** metric. 
- High Entropy = Broad exploration (Frontier scan).
- Low Entropy = Deep exploitation (Validation planning).
- Visualize this in the Project Dashboard to show the system's "Cognitive Mode."

### 4.2 The "Decision Gate" Pattern
**Analysis:** Full autonomy can lead to high costs and irrelevant directions.
**Design Fix:** Formalize the **Approval Request** system.
- Mandatory gates for: `Spend > $1.00`, `External Publish`, `Major Pivot`.
- Use the **Warning Amber Glow** token to highlight these in the UI.

### 4.3 Federated Knowledge Connectors
**Analysis:** Hardcoding academic connectors limits growth.
**Design Fix:** Implement a **Connector Registry**.
- Define a standard `AcademicConnector` interface.
- Allow dynamic loading of new sources (e.g., proprietary datasets, niche journals) via the `manager.py`.

### 4.4 Real-time Observability (SSE)
**Analysis:** Scientific research is slow; users need to see "life" in the system.
**Design Fix:** Enhance the `LivePreview.tsx` with a **Thinking Tree** visualization—showing how the LLM is branching its search strategy in real-time.

## 5. Security & Safety
- **Sandbox Execution:** All data analysis (Python scripts) must run in the Docker Sandbox. No host access.
- **Provider Redundancy:** The `LLMRouter` must maintain a "Local Fallback" (e.g., Llama 3 on Ollama) to ensure research continues even if cloud APIs are down or restricted.
- **Audit Tamper-Proofing:** Audit logs are written in the same transaction as state changes.

## 6. Implementation Roadmap
1.  [X] Phase 1-2: Core Backend/Frontend Foundation.
2.  [X] Phase 3-15: Complete Research Engine (Literature, Scoring, Conflicts).
3.  [X] Phase 16-24: Knowledge Base & Artifacts (LaTeX Prism).
4.  [ ] **Next (Strengthening):** Implement the Cognitive Health metrics and Thinking Tree visualization.
5.  [ ] Phase 25-32: Scaling and E2E Benchmarking.

---
*Created following Google Stitch DESIGN.md Standards.*
