import React, { useState } from 'react';
import type { QueryResponse } from '../types';

interface ExportButtonsProps {
  results: QueryResponse;
}

const ExportButtons: React.FC<ExportButtonsProps> = ({ results }) => {
  const [copied, setCopied] = useState<string | null>(null);

  const generateBibTeX = () => {
    const bibtex = results.summary.papers.map((paper, index) => {
      const authors = paper.authors.join(' and ');
      const year = paper.year || 'Unknown';
      const title = paper.title.replace(/[{}]/g, '');
      const journal = paper.source || 'Unknown';
      const url = paper.url || '';
      const doi = paper.doi ? `https://doi.org/${paper.doi}` : '';

      return `@article{${paper.id || `paper${index + 1}`},
    title = {${title}},
    author = {${authors}},
    journal = {${journal}},
    year = {${year}},
    url = {${url}},${doi ? `\n    doi = {${doi}},` : ''}
}`;
    }).join('\n\n');

    return bibtex;
  };

  const generateTLDR = () => {
    const tldr = `BCI Literature Search Results
Query: ${results.query}
Generated: ${new Date(results.timestamp).toLocaleString()}

TREND SUMMARY:
${results.summary.trend_summary}

KEY FINDINGS:
${results.summary.claims.map((claim, index) => 
  `${index + 1}. ${claim.text} (Confidence: ${(claim.confidence * 100).toFixed(0)}%)`
).join('\n')}

SOURCE PAPERS:
${results.summary.papers.map((paper, index) => 
  `${index + 1}. ${paper.title} (${paper.year}) - ${paper.authors.join(', ')}`
).join('\n')}

Reproducibility Snapshot: ${JSON.stringify(results.summary.reproducibility_snapshot, null, 2)}`;

    return tldr;
  };

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleBibTeXExport = () => {
    const bibtex = generateBibTeX();
    downloadFile(bibtex, 'bci_literature.bib', 'text/plain');
  };

  const handleBibTeXCopy = () => {
    const bibtex = generateBibTeX();
    copyToClipboard(bibtex, 'bibtex');
  };

  const handleTLDRCopy = () => {
    const tldr = generateTLDR();
    copyToClipboard(tldr, 'tldr');
  };

  const handleSnapshotExport = () => {
    const snapshot = JSON.stringify(results.summary.reproducibility_snapshot, null, 2);
    downloadFile(snapshot, 'reproducibility_snapshot.json', 'application/json');
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Results</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* BibTeX Export */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">BibTeX References</h4>
          <div className="flex space-x-2">
            <button
              onClick={handleBibTeXExport}
              className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors duration-200"
            >
              Download .bib
            </button>
            <button
              onClick={handleBibTeXCopy}
              className="px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors duration-200"
            >
              {copied === 'bibtex' ? '✓ Copied' : 'Copy'}
            </button>
          </div>
        </div>

        {/* TL;DR Copy */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Summary Copy</h4>
          <button
            onClick={handleTLDRCopy}
            className="w-full px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors duration-200"
          >
            {copied === 'tldr' ? '✓ Copied TL;DR' : 'Copy TL;DR'}
          </button>
        </div>

        {/* Reproducibility Snapshot */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Reproducibility</h4>
          <button
            onClick={handleSnapshotExport}
            className="w-full px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 transition-colors duration-200"
          >
            Download Snapshot
          </button>
        </div>

        {/* Quick Stats */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Search Stats</h4>
          <div className="text-xs text-gray-600 space-y-1">
            <p>Papers: {results.summary.papers.length}</p>
            <p>Claims: {results.summary.claims.length}</p>
            <p>Time: {results.processing_time.toFixed(2)}s</p>
          </div>
        </div>
      </div>

      {/* Reproducibility Badge */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-center">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-green-50 text-green-700 text-sm">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Reproducible Research
          </div>
        </div>
        <p className="text-xs text-gray-500 text-center mt-2">
          This search can be reproduced using the snapshot data
        </p>
      </div>
    </div>
  );
};

export default ExportButtons;
