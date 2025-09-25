import React from 'react';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  onClear: () => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
  loading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onSearch,
  onClear,
  onKeyPress,
  loading
}) => {
  return (
    <div className="relative">
      {/* Search Input - Google-style */}
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder="Search BCI literature..."
          className="w-full px-6 py-4 text-lg border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent hover:shadow-md transition-shadow duration-200"
          disabled={loading}
        />
        
        {/* Search Icon */}
        <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          ) : (
            <svg 
              className="w-5 h-5 text-gray-400 cursor-pointer hover:text-gray-600" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              onClick={onSearch}
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </div>
      </div>

      {/* Action Buttons - Google-style */}
      <div className="flex justify-center mt-6 space-x-4">
        <button
          onClick={onSearch}
          disabled={loading || !value.trim()}
          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          {loading ? 'Searching...' : 'Search Literature'}
        </button>
        
        {value && (
          <button
            onClick={onClear}
            disabled={loading}
            className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            Clear
          </button>
        )}
      </div>

      {/* Quick Search Suggestions */}
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-500 mb-2">Quick searches:</p>
        <div className="flex flex-wrap justify-center gap-2">
          {[
            'SSVEP non-invasive',
            'motor imagery EEG',
            'P300 brain interface',
            'neural prosthesis',
            'BCI classification'
          ].map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => onChange(suggestion)}
              disabled={loading}
              className="px-3 py-1 text-xs bg-gray-50 text-gray-600 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-colors duration-200"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SearchBar;
