/** Strip LaTeX preamble and render a simple HTML preview (sections → h2, paragraphs → p). */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function stripComments(text: string): string {
  return text.replace(/%.*$/gm, '');
}

function stripInlineCommands(text: string): string {
  let result = text;
  // Replace common text-formatting commands with their content
  const patterns = [
    /\\textbf\{([^}]*)\}/g,
    /\\textit\{([^}]*)\}/g,
    /\\emph\{([^}]*)\}/g,
    /\\texttt\{([^}]*)\}/g,
    /\\cite\{([^}]*)\}/g,
    /\\ref\{([^}]*)\}/g,
    /\\label\{([^}]*)\}/g,
  ];
  for (const pattern of patterns) {
    result = result.replace(pattern, '$1');
  }
  // Remove remaining commands without args
  result = result.replace(/\\[a-zA-Z@]+\*?(\[[^\]]*\])?/g, ' ');
  // Remove braces used for grouping
  result = result.replace(/[{}]/g, '');
  return result.replace(/\s+/g, ' ').trim();
}

function extractBody(latex: string): string {
  let body = latex;

  const beginMatch = body.match(/\\begin\{document\}/);
  if (beginMatch && beginMatch.index !== undefined) {
    body = body.slice(beginMatch.index + '\\begin{document}'.length);
  }

  const endMatch = body.match(/\\end\{document\}/);
  if (endMatch && endMatch.index !== undefined) {
    body = body.slice(0, endMatch.index);
  }

  return stripComments(body);
}

const SKIP_COMMANDS =
  /^\\(maketitle|tableofcontents|bibliography|bibliographystyle|input|include|usepackage|documentclass|title|author|date|thanks|abstract|begin|end|newpage|clearpage|pagebreak)\b/;

export function latexToPreviewHtml(latex: string): string {
  const body = extractBody(latex);
  const parts: string[] = [];
  const paragraphBuffer: string[] = [];

  const flushParagraph = () => {
    if (paragraphBuffer.length === 0) return;
    const text = stripInlineCommands(paragraphBuffer.join(' '));
    if (text) {
      parts.push(`<p>${escapeHtml(text)}</p>`);
    }
    paragraphBuffer.length = 0;
  };

  for (const rawLine of body.split('\n')) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      continue;
    }

    if (SKIP_COMMANDS.test(line)) {
      continue;
    }

    const sectionMatch = line.match(/^\\section\*?\{(.+)\}$/);
    const subsectionMatch = line.match(/^\\subsection\*?\{(.+)\}$/);

    if (sectionMatch) {
      flushParagraph();
      const title = stripInlineCommands(sectionMatch[1]);
      parts.push(`<h2>${escapeHtml(title)}</h2>`);
      continue;
    }

    if (subsectionMatch) {
      flushParagraph();
      const title = stripInlineCommands(subsectionMatch[1]);
      parts.push(`<h3>${escapeHtml(title)}</h3>`);
      continue;
    }

    if (line.startsWith('\\begin{') || line.startsWith('\\end{')) {
      continue;
    }

    paragraphBuffer.push(line);
  }

  flushParagraph();
  return parts.join('\n');
}