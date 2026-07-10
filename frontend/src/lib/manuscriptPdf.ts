import { jsPDF } from 'jspdf';
import type { Manuscript } from '@/lib/types';

const MARGIN = 20;
const LINE_HEIGHT = 6;
const PAGE_WIDTH = 210;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;

function latexToPlainText(latex: string): string {
  return latex
    .replace(/\\documentclass(\[[^\]]*\])?\{[^}]*\}/g, '')
    .replace(/\\usepackage(\[[^\]]*\])?\{[^}]*\}/g, '')
    .replace(/\\begin\{document\}/g, '')
    .replace(/\\end\{document\}/g, '')
    .replace(/\\maketitle/g, '')
    .replace(/\\title\{([^}]*)\}/g, '$1\n')
    .replace(/\\author\{([^}]*)\}/g, '$1\n')
    .replace(/\\date\{([^}]*)\}/g, '$1\n')
    .replace(/\\section\*?\{([^}]*)\}/g, '\n\n$1\n')
    .replace(/\\subsection\*?\{([^}]*)\}/g, '\n\n$1\n')
    .replace(/\\subsubsection\*?\{([^}]*)\}/g, '\n\n$1\n')
    .replace(/\\textbf\{([^}]*)\}/g, '$1')
    .replace(/\\textit\{([^}]*)\}/g, '$1')
    .replace(/\\emph\{([^}]*)\}/g, '$1')
    .replace(/\\cite[pt]?\{[^}]*\}/g, '')
    .replace(/\\ref\{[^}]*\}/g, '')
    .replace(/\\label\{[^}]*\}/g, '')
    .replace(/\\[a-zA-Z@]+\{([^}]*)\}/g, '$1')
    .replace(/\\[a-zA-Z@]+/g, '')
    .replace(/[{}]/g, '')
    .replace(/%\s.*$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function addWrappedText(
  doc: jsPDF,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  fontSize: number,
): number {
  doc.setFontSize(fontSize);
  const lines = doc.splitTextToSize(text, maxWidth) as string[];
  for (const line of lines) {
    if (y > 280) {
      doc.addPage();
      y = MARGIN;
    }
    doc.text(line, x, y);
    y += LINE_HEIGHT;
  }
  return y;
}

export function exportManuscriptPdf(manuscript: Manuscript, latexContent: string): void {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  let y = MARGIN;

  doc.setFont('helvetica', 'bold');
  y = addWrappedText(doc, manuscript.title || 'Untitled Manuscript', MARGIN, y, CONTENT_WIDTH, 16);
  y += 4;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(100);
  doc.text(`Status: ${manuscript.status}  |  Version: ${manuscript.version}`, MARGIN, y);
  doc.setTextColor(0);
  y += 10;

  const body = latexToPlainText(latexContent || manuscript.content_latex || '');
  if (body) {
    y = addWrappedText(doc, body, MARGIN, y, CONTENT_WIDTH, 11);
    y += 8;
  }

  if (manuscript.bibtex) {
    if (y > 250) {
      doc.addPage();
      y = MARGIN;
    }
    doc.setFont('helvetica', 'bold');
    y = addWrappedText(doc, 'References', MARGIN, y, CONTENT_WIDTH, 12);
    y += 2;
    doc.setFont('helvetica', 'normal');
    y = addWrappedText(doc, manuscript.bibtex, MARGIN, y, CONTENT_WIDTH, 9);
  }

  const slug = (manuscript.title || 'manuscript')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 60);

  doc.save(`${slug || 'manuscript'}.pdf`);
}

export function exportManuscriptDocx(manuscript: Manuscript, _latexContent: string): void {
  // Server-side pandoc converts LaTeX → DOCX on the fly
  window.open(`/api/v1/manuscripts/${manuscript.id}/download?format=docx`, '_blank');
}