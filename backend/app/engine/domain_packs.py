"""Domain specialization packs for physics, biology, and chemistry."""

from __future__ import annotations

from typing import Any

DOMAIN_PACKS: dict[str, dict[str, Any]] = {
    "physics": {
        "id": "physics",
        "name": "Physics & Engineering",
        "domain_label": "Theoretical and experimental physics",
        "description": "Literature discovery, hypothesis validation, and reproducible numerics for physical systems.",
        "subject_scope": [
            "condensed matter",
            "quantum systems",
            "statistical mechanics",
            "computational physics",
        ],
        "out_of_scope": [
            "clinical trials",
            "wet-lab protocols without quantitative models",
        ],
        "preferred_connectors": ["arxiv", "openalex", "semantic_scholar"],
        "literature_keywords": ["simulation", "Hamiltonian", "phase transition", "benchmark"],
        "validation_methods": [
            "numerical reproducibility",
            "dimensional analysis",
            "limit-case sanity checks",
        ],
        "idle_modes": ["frontier_scan", "citation_conflict", "cross_domain"],
        "prompt_context": (
            "Prioritize mechanistic models, error bars, and reproducible simulation artifacts. "
            "Flag claims that lack unit consistency or conservation-law justification."
        ),
    },
    "biology": {
        "id": "biology",
        "name": "Biology & Life Sciences",
        "domain_label": "Molecular and systems biology",
        "description": "Gene-pathway reasoning, dataset discovery, and evidence grading for biological claims.",
        "subject_scope": [
            "genomics",
            "proteomics",
            "cell biology",
            "systems biology",
        ],
        "out_of_scope": [
            "pure software engineering without biological target",
            "non-peer-reviewed preprints as sole evidence",
        ],
        "preferred_connectors": ["pubmed", "semantic_scholar", "openalex"],
        "literature_keywords": ["pathway", "differential expression", "knockout", "organism"],
        "validation_methods": [
            "independent cohort replication",
            "control vs treatment design",
            "batch-effect checks",
        ],
        "idle_modes": ["dataset_discovery", "citation_conflict", "frontier_scan"],
        "prompt_context": (
            "Emphasize experimental controls, organism context, and statistical power. "
            "Highlight confounders such as batch effects and population stratification."
        ),
    },
    "chemistry": {
        "id": "chemistry",
        "name": "Chemistry & Materials",
        "domain_label": "Synthetic and computational chemistry",
        "description": "Reaction discovery, materials characterization, and property prediction workflows.",
        "subject_scope": [
            "organic synthesis",
            "catalysis",
            "materials science",
            "computational chemistry",
        ],
        "out_of_scope": [
            "unrelated pharmaceutical marketing claims",
            "proprietary formulations without published evidence",
        ],
        "preferred_connectors": ["crossref", "openalex", "semantic_scholar"],
        "literature_keywords": ["yield", "selectivity", "DFT", "spectroscopy", "catalyst"],
        "validation_methods": [
            "characterization triangulation (NMR/XRD/IR)",
            "control reactions",
            "computational benchmarking",
        ],
        "idle_modes": ["frontier_scan", "dataset_discovery", "cross_domain"],
        "prompt_context": (
            "Track reaction conditions, characterization evidence, and yield/selectivity trade-offs. "
            "Prefer claims supported by multiple orthogonal characterization methods."
        ),
    },
}


def list_domain_packs() -> list[dict[str, Any]]:
    return [
        {
            "id": pack["id"],
            "name": pack["name"],
            "domain_label": pack["domain_label"],
            "description": pack["description"],
            "subject_scope": pack["subject_scope"],
            "validation_methods": pack["validation_methods"],
            "preferred_connectors": pack["preferred_connectors"],
        }
        for pack in DOMAIN_PACKS.values()
    ]


def get_domain_pack(pack_id: str) -> dict[str, Any] | None:
    return DOMAIN_PACKS.get(pack_id)


def apply_domain_pack(pack_id: str) -> dict[str, Any]:
    pack = get_domain_pack(pack_id)
    if not pack:
        raise ValueError(f"Unknown domain pack: {pack_id}")
    return {
        "domain": pack["domain_label"],
        "description": pack["description"],
        "subject_scope": pack["subject_scope"],
        "out_of_scope": pack["out_of_scope"],
        "pack_id": pack["id"],
        "prompt_context": pack["prompt_context"],
        "preferred_connectors": pack["preferred_connectors"],
        "validation_methods": pack["validation_methods"],
        "idle_modes": pack["idle_modes"],
    }
