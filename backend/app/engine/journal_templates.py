"""Journal LaTeX template presets for the publication pipeline."""

from typing import Any

TEMPLATES: dict[str, dict[str, Any]] = {
    "ieee": {
        "id": "ieee",
        "name": "IEEE Conference",
        "documentclass": "\\documentclass[conference]{IEEEtran}",
        "packages": ["\\usepackage{cite}", "\\usepackage{amsmath,amssymb,amsfonts}"],
        "bibliographystyle": "IEEEtran",
        "checklist": [
            "Abstract ≤ 250 words",
            "Index terms included",
            "Figures at 300 DPI minimum",
            "References in IEEE numeric style",
        ],
    },
    "nature": {
        "id": "nature",
        "name": "Nature Research Article",
        "documentclass": "\\documentclass{article}",
        "packages": ["\\usepackage[margin=1in]{geometry}", "\\usepackage{natbib}"],
        "bibliographystyle": "naturemag",
        "checklist": [
            "Structured abstract (Background, Methods, Results, Conclusions)",
            "Main text ≤ 3,000 words",
            "Methods section after references",
            "Data availability statement",
        ],
    },
    "acl": {
        "id": "acl",
        "name": "ACL Anthology",
        "documentclass": "\\documentclass[11pt]{article}",
        "packages": ["\\usepackage{acl2023}", "\\usepackage{times}", "\\usepackage{latexsym}"],
        "bibliographystyle": "acl_natbib",
        "checklist": [
            "Limitations section required",
            "Ethics statement if human subjects",
            "Appendix for reproducibility details",
            "Anonymous submission mode for review",
        ],
    },
}


def list_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "checklist": t["checklist"],
        }
        for t in TEMPLATES.values()
    ]


def apply_template(template_id: str, latex_body: str) -> str:
    template = TEMPLATES.get(template_id)
    if not template:
        return latex_body
    preamble = "\n".join(
        [template["documentclass"], *template.get("packages", []), ""],
    )
    if "\\documentclass" in latex_body:
        return latex_body
    return f"{preamble}\\begin{{document}}\n{latex_body}\n\\end{{document}}\n"
