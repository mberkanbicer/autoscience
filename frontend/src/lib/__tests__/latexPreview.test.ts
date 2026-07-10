import { describe, it, expect } from 'vitest';
import { latexToPreviewHtml } from '../latexPreview';

describe('latexToPreviewHtml', () => {
  it('strips preamble and renders sections and paragraphs', () => {
    const latex = `
\\documentclass{article}
\\usepackage{amsmath}
\\begin{document}
\\title{Test}
\\maketitle

\\section{Introduction}
This is the first paragraph.

\\section{Methods}
We used a novel approach.
\\end{document}
`;

    const html = latexToPreviewHtml(latex);

    expect(html).toContain('<h2>Introduction</h2>');
    expect(html).toContain('<h2>Methods</h2>');
    expect(html).toContain('<p>This is the first paragraph.</p>');
    expect(html).toContain('<p>We used a novel approach.</p>');
    expect(html).not.toContain('documentclass');
    expect(html).not.toContain('usepackage');
  });

  it('returns empty string for empty input', () => {
    expect(latexToPreviewHtml('')).toBe('');
  });
});