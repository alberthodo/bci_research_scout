import React, { useState, useEffect } from 'react';
import { apiService } from './services/api';
import type { QueryRequest, QueryResponse } from './types';
import SearchBar from './components/SearchBar';
import ResultsDisplay from './components/ResultsDisplay';
import LoadingSpinner from './components/LoadingSpinner';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Removed Sprint 5 state - keeping interface clean

  // Debug: Log when component mounts
  useEffect(() => {
    console.log('App component mounted');
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const request: QueryRequest = {
        query: query.trim(),
        max_results: 8
      };

      const response = await apiService.queryLiterature(request);
      setResults(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setError(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // Removed Sprint 5 functions - keeping interface clean

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header - Google-style, hidden when results exist */}
      {!results && !loading && !error && (
        <header className="pt-8 pb-4">
          <div className="text-center">
            <h1 className="text-6xl font-normal text-gray-900 mb-2 tracking-tight">
              BCI Literature Scout
            </h1>
            <p className="text-lg text-gray-600 font-light">
              Research Brain-Computer Interface papers with AI-powered insights
            </p>
          </div>
        </header>
      )}

      {/* Main Search Area */}
      <main className={`max-w-2xl mx-auto px-4 flex-1 ${results || loading || error ? 'pt-4' : 'flex flex-col justify-center'}`}>
        <div className={`${results || loading || error ? 'mb-4' : 'mb-8'}`}>
          <SearchBar
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            onClear={handleClear}
            onKeyPress={handleKeyPress}
            loading={loading}
          />
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <LoadingSpinner />
            <p className="text-gray-500 mt-4">Searching BCI literature...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center py-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 max-w-md mx-auto">
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {results && !loading && (
          <ResultsDisplay results={results} />
        )}

        {/* Empty State */}
        {!results && !loading && !error && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
        )}
      </main>

      {/* Footer - Always at bottom */}
      <footer className="py-4 mt-auto">
        <div className="text-center text-sm text-gray-500">
          <p>Powered by sedem oasis • Built for BCI researchers</p>
        </div>
      </footer>
    </div>
  );
}

export default App;