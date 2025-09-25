import React, { useState } from 'react';
import type { SourceInfo, ReproducibilityInfo } from '../types';

interface AdvancedFeaturesProps {
  sourcesInfo?: Record<string, SourceInfo>;
  reproducibilityInfo?: ReproducibilityInfo;
  className?: string;
}

const AdvancedFeatures: React.FC<AdvancedFeaturesProps> = ({
  sourcesInfo = {},
  reproducibilityInfo,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'sources' | 'reproducibility'>('sources');

  const renderSourcesTab = () => (
    <div className="space-y-4">
      <div className="mb-4">
        <h4 className="text-lg font-medium text-gray-900 mb-2">Data Sources</h4>
        <p className="text-sm text-gray-600">
          Information about the data sources used in this research scout.
        </p>
      </div>

      {Object.entries(sourcesInfo).length > 0 ? (
        <div className="grid gap-4">
          {Object.entries(sourcesInfo).map(([sourceName, sourceInfo]) => (
            <div key={sourceName} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h5 className="font-medium text-gray-900 capitalize">{sourceInfo.name}</h5>
                <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                  {sourceInfo.paper_count} papers
                </span>
              </div>
              
              <p className="text-sm text-gray-600 mb-3">{sourceInfo.description}</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">Year Range</div>
                  <div className="font-medium">
                    {sourceInfo.coverage.year_range.min} - {sourceInfo.coverage.year_range.max}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Total Citations</div>
                  <div className="font-medium">{sourceInfo.coverage.total_citations}</div>
                </div>
                <div>
                  <div className="text-gray-500">Avg Citations</div>
                  <div className="font-medium">
                    {sourceInfo.coverage.avg_citations.toFixed(1)}
                  </div>
                </div>
                <div>
                  <div className="text-gray-500">Last Updated</div>
                  <div className="font-medium">
                    {new Date(sourceInfo.last_updated).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm2 6a2 2 0 114 0 2 2 0 01-4 0zm8 0a2 2 0 114 0 2 2 0 01-4 0z" clipRule="evenodd" />
            </svg>
          </div>
          <p>No source information available</p>
        </div>
      )}
    </div>
  );


  const renderReproducibilityTab = () => (
    <div className="space-y-4">
      <div className="mb-4">
        <h4 className="text-lg font-medium text-gray-900 mb-2">Reproducibility</h4>
        <p className="text-sm text-gray-600">
          Information to reproduce this research query and verify results.
        </p>
      </div>

      {reproducibilityInfo ? (
        <div className="space-y-4">
          <div className="border rounded-lg p-4">
            <h5 className="font-medium text-gray-900 mb-2">Snapshot ID</h5>
            <div className="bg-gray-50 p-3 rounded text-sm font-mono text-gray-700">
              {reproducibilityInfo.snapshot_id}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4">
              <h5 className="font-medium text-gray-900 mb-2">Query Details</h5>
              <div className="text-sm space-y-1">
                <div><span className="text-gray-500">Query:</span> {reproducibilityInfo.query}</div>
                <div><span className="text-gray-500">Timestamp:</span> {new Date(reproducibilityInfo.timestamp).toLocaleString()}</div>
              </div>
            </div>

            <div className="border rounded-lg p-4">
              <h5 className="font-medium text-gray-900 mb-2">System Versions</h5>
              <div className="text-sm space-y-1">
                <div><span className="text-gray-500">Data Version:</span> {reproducibilityInfo.data_version}</div>
                <div><span className="text-gray-500">Model Version:</span> {reproducibilityInfo.model_version}</div>
              </div>
            </div>
          </div>

          <div className="border rounded-lg p-4">
            <h5 className="font-medium text-gray-900 mb-2">Parameters Used</h5>
            <div className="bg-gray-50 p-3 rounded text-sm">
              <pre className="whitespace-pre-wrap text-gray-700">
                {JSON.stringify(reproducibilityInfo.parameters, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <p>No reproducibility information available</p>
        </div>
      )}
    </div>
  );


  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {[
            { id: 'sources', label: 'Sources', icon: '📚' },
            { id: 'reproducibility', label: 'Reproducibility', icon: '🔄' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="p-6">
        {activeTab === 'sources' && renderSourcesTab()}
        {activeTab === 'reproducibility' && renderReproducibilityTab()}
      </div>
    </div>
  );
};

export default AdvancedFeatures;
