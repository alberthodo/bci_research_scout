import React, { useState } from 'react';
import type { PaperMetadata } from '../types';

interface PaperCardProps {
  paper: PaperMetadata;
  index: number;
}

const PaperCard: React.FC<PaperCardProps> = ({ paper, index }) => {
  const [showAbstract, setShowAbstract] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center">
          <span className="inline-flex items-center justify-center w-6 h-6 bg-gray-100 text-gray-600 text-sm font-medium rounded-full mr-3">
            {index}
          </span>
          <div className="flex-1">
            <h4 className="text-gray-900 font-medium leading-tight mb-1">
              {paper.title}
            </h4>
            <div className="flex items-center text-sm text-gray-500 space-x-4">
              <span>{paper.authors.join(', ')}</span>
              <span>•</span>
              <span>{paper.year}</span>
              <span>•</span>
              <span className="capitalize">{paper.source}</span>
              {paper.citation_count && (
                <>
                  <span>•</span>
                  <span>{paper.citation_count} citations</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Abstract */}
      <div className="ml-9">
        <div className="mb-3">
          <button
            onClick={() => setShowAbstract(!showAbstract)}
            className="flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors duration-200"
          >
            <svg 
              className={`w-4 h-4 mr-1 transition-transform duration-200 ${showAbstract ? 'rotate-180' : ''}`} 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
            {showAbstract ? 'Hide' : 'Show'} Abstract
          </button>
        </div>

        {showAbstract && (
          <div className="bg-gray-50 rounded-md p-3 mb-3">
            <p className="text-sm text-gray-700 leading-relaxed">{paper.abstract}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center space-x-4">
          {paper.url && (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors duration-200"
            >
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
              </svg>
              View Paper
            </a>
          )}
          
          {paper.doi && (
            <a
              href={`https://doi.org/${paper.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-sm text-gray-600 hover:text-gray-800 transition-colors duration-200"
            >
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
              </svg>
              DOI
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default PaperCard;
