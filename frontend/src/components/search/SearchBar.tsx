'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';

interface SearchResult {
  id: string;
  type: 'project' | 'document' | 'proposal';
  name: string;
  highlight?: string;
  project_id?: string;
  created_at: string;
}

interface SearchResponse {
  query: string;
  total_results: number;
  projects: SearchResult[];
  documents: SearchResult[];
  proposals: SearchResult[];
}

interface Suggestion {
  text: string;
  type: string;
}

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const { data: suggestions } = useQuery({
    queryKey: ['search-suggestions', query],
    queryFn: async () => {
      if (query.length < 2) return [];
      const response = await api.get<Suggestion[]>('/search/suggestions', {
        params: { q: query, limit: 5 },
      });
      return response.data;
    },
    enabled: query.length >= 2,
  });

  const { data: results, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      const response = await api.get<SearchResponse>('/search', {
        params: { q: query, limit: 10 },
      });
      return response.data;
    },
    enabled: query.length >= 2,
  });

  const allResults = results
    ? [...results.projects, ...results.documents, ...results.proposals]
    : [];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        inputRef.current?.focus();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
        inputRef.current?.blur();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, allResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, -1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      handleResultClick(allResults[selectedIndex]);
    }
  };

  const handleResultClick = (result: SearchResult) => {
    setIsOpen(false);
    setQuery('');

    switch (result.type) {
      case 'project':
        router.push(`/dashboard/projects/${result.id}`);
        break;
      case 'document':
        router.push(`/dashboard/projects/${result.project_id}?tab=documents`);
        break;
      case 'proposal':
        router.push(`/dashboard/projects/${result.project_id}/proposals/${result.id}`);
        break;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'project':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        );
      case 'document':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
      case 'proposal':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'project':
        return 'bg-blue-100 text-blue-700';
      case 'document':
        return 'bg-green-100 text-green-700';
      case 'proposal':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="relative w-full max-w-lg">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
            setSelectedIndex(-1);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search projects, documents, proposals..."
          className="w-full pl-10 pr-12 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <svg
          className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
          Ctrl+K
        </span>
      </div>

      {isOpen && query.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border max-h-96 overflow-y-auto z-50">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Searching...</div>
          ) : allResults.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No results found</div>
          ) : (
            <div>
              {results?.projects && results.projects.length > 0 && (
                <div>
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50">
                    Projects
                  </div>
                  {results.projects.map((result, index) => (
                    <button
                      key={result.id}
                      onClick={() => handleResultClick(result)}
                      className={`w-full px-4 py-3 flex items-start gap-3 hover:bg-gray-50 text-left ${
                        selectedIndex === index ? 'bg-blue-50' : ''
                      }`}
                    >
                      <span className={`p-1.5 rounded ${getTypeColor(result.type)}`}>
                        {getTypeIcon(result.type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{result.name}</p>
                        {result.highlight && (
                          <p className="text-sm text-gray-500 truncate">{result.highlight}</p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {results?.documents && results.documents.length > 0 && (
                <div>
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50">
                    Documents
                  </div>
                  {results.documents.map((result, index) => (
                    <button
                      key={result.id}
                      onClick={() => handleResultClick(result)}
                      className={`w-full px-4 py-3 flex items-start gap-3 hover:bg-gray-50 text-left ${
                        selectedIndex === (results?.projects?.length || 0) + index ? 'bg-blue-50' : ''
                      }`}
                    >
                      <span className={`p-1.5 rounded ${getTypeColor(result.type)}`}>
                        {getTypeIcon(result.type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{result.name}</p>
                        {result.highlight && (
                          <p className="text-sm text-gray-500 truncate">{result.highlight}</p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {results?.proposals && results.proposals.length > 0 && (
                <div>
                  <div className="px-4 py-2 text-xs font-semibold text-gray-500 bg-gray-50">
                    Proposals
                  </div>
                  {results.proposals.map((result, index) => (
                    <button
                      key={result.id}
                      onClick={() => handleResultClick(result)}
                      className={`w-full px-4 py-3 flex items-start gap-3 hover:bg-gray-50 text-left ${
                        selectedIndex === (results?.projects?.length || 0) + (results?.documents?.length || 0) + index ? 'bg-blue-50' : ''
                      }`}
                    >
                      <span className={`p-1.5 rounded ${getTypeColor(result.type)}`}>
                        {getTypeIcon(result.type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{result.name}</p>
                        {result.highlight && (
                          <p className="text-sm text-gray-500 truncate">{result.highlight}</p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {isOpen && <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />}
    </div>
  );
}
