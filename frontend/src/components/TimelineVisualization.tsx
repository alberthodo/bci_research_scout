import React, { useEffect, useRef, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import type { TimelineData } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface TimelineVisualizationProps {
  data: TimelineData;
  className?: string;
}

const TimelineVisualization: React.FC<TimelineVisualizationProps> = ({ 
  data, 
  className = '' 
}) => {
  const [selectedKeywords, setSelectedKeywords] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'papers' | 'keywords'>('papers');

  // Prepare papers per year data
  const papersData = {
    labels: Object.keys(data.papers_per_year).sort((a, b) => parseInt(a) - parseInt(b)),
    datasets: [
      {
        label: 'Papers per Year',
        data: Object.keys(data.papers_per_year)
          .sort((a, b) => parseInt(a) - parseInt(b))
          .map(year => data.papers_per_year[parseInt(year)]),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
    ],
  };

  // Prepare keyword trends data
  const keywordData = {
    labels: Object.keys(data.papers_per_year).sort((a, b) => parseInt(a) - parseInt(b)),
    datasets: selectedKeywords.map((keyword, index) => {
      const colors = [
        'rgb(239, 68, 68)',   // red
        'rgb(34, 197, 94)',   // green
        'rgb(168, 85, 247)',  // purple
        'rgb(245, 158, 11)',  // amber
        'rgb(236, 72, 153)',  // pink
        'rgb(14, 165, 233)',  // sky
        'rgb(34, 197, 94)',   // emerald
        'rgb(251, 146, 60)',  // orange
      ];
      
      const keywordTrends = data.keyword_trends[keyword] || [];
      const trendMap = keywordTrends.reduce((acc, item) => {
        acc[item.year] = item.count;
        return acc;
      }, {} as Record<number, number>);

      return {
        label: keyword,
        data: Object.keys(data.papers_per_year)
          .sort((a, b) => parseInt(a) - parseInt(b))
          .map(year => trendMap[parseInt(year)] || 0),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length] + '20',
        tension: 0.1,
      };
    }),
  };

  const papersOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'BCI Papers Published by Year',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y} papers`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Papers'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Year'
        }
      }
    },
  };

  const keywordsOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Keyword Trends Over Time',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y} mentions`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Mentions'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Year'
        }
      }
    },
  };

  const availableKeywords = Object.keys(data.keyword_trends).sort();

  const handleKeywordToggle = (keyword: string) => {
    setSelectedKeywords(prev => 
      prev.includes(keyword) 
        ? prev.filter(k => k !== keyword)
        : [...prev, keyword]
    );
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Timeline Analysis</h3>
          <div className="flex space-x-2">
            <button
              onClick={() => setViewMode('papers')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                viewMode === 'papers'
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Papers per Year
            </button>
            <button
              onClick={() => setViewMode('keywords')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                viewMode === 'keywords'
                  ? 'bg-blue-100 text-blue-700 border border-blue-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Keyword Trends
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-sm text-blue-600 font-medium">Total Papers</div>
            <div className="text-2xl font-bold text-blue-900">{data.total_papers}</div>
          </div>
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-sm text-green-600 font-medium">Year Range</div>
            <div className="text-lg font-bold text-green-900">
              {data.year_range.min} - {data.year_range.max}
            </div>
          </div>
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-sm text-purple-600 font-medium">Keywords Tracked</div>
            <div className="text-2xl font-bold text-purple-900">{availableKeywords.length}</div>
          </div>
        </div>
      </div>

      {viewMode === 'papers' ? (
        <div className="h-96">
          <Bar data={papersData} options={papersOptions} />
        </div>
      ) : (
        <div>
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Select Keywords to Track:</h4>
            <div className="flex flex-wrap gap-2">
              {availableKeywords.slice(0, 20).map((keyword) => (
                <button
                  key={keyword}
                  onClick={() => handleKeywordToggle(keyword)}
                  className={`px-3 py-1 text-xs rounded-full transition-colors ${
                    selectedKeywords.includes(keyword)
                      ? 'bg-blue-100 text-blue-700 border border-blue-200'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {keyword}
                </button>
              ))}
            </div>
            {availableKeywords.length > 20 && (
              <p className="text-xs text-gray-500 mt-2">
                Showing top 20 keywords. Total: {availableKeywords.length}
              </p>
            )}
          </div>
          
          {selectedKeywords.length > 0 ? (
            <div className="h-96">
              <Line data={keywordData} options={keywordsOptions} />
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center">
                <div className="text-gray-400 mb-2">
                  <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <p className="text-gray-500">Select keywords above to view trends</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TimelineVisualization;
