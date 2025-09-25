import React, { useState } from 'react';
import type { QueryResponse } from '../types';
import ClaimCard from './ClaimCard';
import PaperCard from './PaperCard';
import ExportButtons from './ExportButtons';

interface ResultsDisplayProps {
  results: QueryResponse;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'papers'>('summary');

  const { summary } = results;
  const { claims, papers, trend_summary } = summary;

  return (
    <div className="space-y-6">
      {/* Processing Info */}
      <div className="text-center text-sm text-gray-500">
        <p>Found {papers.length} papers • Generated {claims.length} claims • Processed in {results.processing_time.toFixed(2)}s</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex justify-center border-b border-gray-200">
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-6 py-2 text-sm font-medium border-b-2 transition-colors duration-200 ${
            activeTab === 'summary'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          AI Summary & Claims
        </button>
        <button
          onClick={() => setActiveTab('papers')}
          className={`px-6 py-2 text-sm font-medium border-b-2 transition-colors duration-200 ${
            activeTab === 'papers'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Source Papers ({papers.length})
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'summary' && (
        <div className="space-y-6">
          {/* Trend Summary */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Trend Summary</h3>
            <p className="text-gray-700 leading-relaxed">{trend_summary}</p>
          </div>

          {/* Key Claims */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Claims with Evidence</h3>
            <div className="space-y-4">
              {claims.map((claim, index) => (
                <ClaimCard key={claim.id || index} claim={claim} index={index + 1} />
              ))}
            </div>
          </div>

          {/* Export Options */}
          <ExportButtons results={results} />
        </div>
      )}

      {activeTab === 'papers' && (
        <div className="space-y-4">
          <div className="text-center text-sm text-gray-500 mb-4">
            <p>Papers retrieved and analyzed for the query: "{results.query}"</p>
          </div>
          
          <div className="space-y-4">
            {papers.map((paper, index) => (
              <PaperCard key={paper.id || index} paper={paper} index={index + 1} />
            ))}
          </div>
        </div>
      )}

      {/* Reproducibility Info */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="text-center">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-green-50 text-green-700 text-sm">
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Reproducible Results
          </div>
          <p className="text-xs text-gray-500 mt-2">
            This search can be reproduced using the snapshot data
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResultsDisplay;
