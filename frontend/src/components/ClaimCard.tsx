import React from 'react';
import type { Claim } from '../types';

interface ClaimCardProps {
  claim: Claim;
  index: number;
}

const ClaimCard: React.FC<ClaimCardProps> = ({ claim, index }) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-50';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'HIGH';
    if (confidence >= 0.6) return 'MEDIUM';
    return 'LOW';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center">
          <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-600 text-sm font-medium rounded-full mr-3">
            {index}
          </span>
          <h4 className="text-gray-900 font-medium">Key Finding</h4>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getConfidenceColor(claim.confidence)}`}>
          {getConfidenceLabel(claim.confidence)} CONFIDENCE
        </span>
      </div>

      <div className="ml-9">
        <p className="text-gray-800 mb-3 leading-relaxed">{claim.text}</p>
        
        {/* Evidence */}
        <div className="bg-gray-50 rounded-md p-3 mb-3">
          <div className="flex items-start">
            <svg className="w-4 h-4 text-gray-400 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-sm font-medium text-gray-700 mb-1">Supporting Evidence:</p>
              <p className="text-sm text-gray-600 italic">"{claim.evidence[0]}"</p>
            </div>
          </div>
        </div>

        {/* Supporting Papers */}
        {claim.supporting_papers && claim.supporting_papers.length > 0 && (
          <div className="flex items-center text-sm text-gray-500">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
            <span>Cited in: {claim.supporting_papers.join(', ')}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClaimCard;
