'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface ProposalAnalysis {
  overall_score: number;
  section_scores: Record<string, { score: number; issues: string[]; suggestions: string[] }>;
  writing_issues: Array<{
    type: string;
    count: number;
    suggestion: string;
    severity: string;
  }>;
  improvement_suggestions: Array<{
    category: string;
    priority: string;
    title: string;
    description: string;
    impact: string;
  }>;
  readability: {
    score: number;
    level: string;
    avg_sentence_length: number;
    suggestions: string[];
  };
}

interface AISuggestionsPanelProps {
  proposalId?: string;
  content?: string;
}

export function AISuggestionsPanel({ proposalId, content }: AISuggestionsPanelProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<ProposalAnalysis | null>(null);

  const { data: storedAnalysis, isLoading } = useQuery({
    queryKey: ['proposal-analysis', proposalId],
    queryFn: async () => {
      const response = await api.get<{ analysis: ProposalAnalysis }>(`/ai/analyze/${proposalId}`);
      return response.data.analysis;
    },
    enabled: !!proposalId && !content,
  });

  const analyzeContent = async () => {
    if (!content) return;
    setIsAnalyzing(true);
    try {
      const response = await api.post<{ analysis: ProposalAnalysis }>('/ai/analyze', { content });
      setAnalysis(response.data.analysis);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const currentAnalysis = analysis || storedAnalysis;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700';
      default:
        return 'bg-blue-100 text-blue-700';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-orange-100 text-orange-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  if (content && !analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Writing Assistant</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <svg className="w-12 h-12 mx-auto text-blue-500 mb-4\" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <p className="text-gray-600 mb-4">
              Get AI-powered suggestions to improve your proposal
            </p>
            <Button onClick={analyzeContent} disabled={isAnalyzing}>
              {isAnalyzing ? 'Analyzing...' : 'Analyze Proposal'}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading || isAnalyzing) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center gap-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
            <span className="text-gray-600">Analyzing your proposal...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!currentAnalysis) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <Card>
        <CardHeader>
          <CardTitle>Proposal Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Overall Score</p>
              <p className={`text-4xl font-bold ${getScoreColor(currentAnalysis.overall_score)}`}>
                {currentAnalysis.overall_score}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Readability</p>
              <p className="text-lg font-semibold">{currentAnalysis.readability.level}</p>
              <p className="text-sm text-gray-500">
                Avg. sentence: {currentAnalysis.readability.avg_sentence_length} words
              </p>
            </div>
          </div>

          {/* Score gauge */}
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full ${
                  currentAnalysis.overall_score >= 80
                    ? 'bg-green-500'
                    : currentAnalysis.overall_score >= 60
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${currentAnalysis.overall_score}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Writing Issues */}
      {currentAnalysis.writing_issues.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Writing Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {currentAnalysis.writing_issues.map((issue, index) => (
                <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(issue.severity)}`}>
                    {issue.severity}
                  </span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 capitalize">
                      {issue.type.replace(/_/g, ' ')} ({issue.count} occurrences)
                    </p>
                    <p className="text-sm text-gray-600 mt-1">{issue.suggestion}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Improvement Suggestions */}
      {currentAnalysis.improvement_suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Improvement Suggestions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {currentAnalysis.improvement_suggestions.map((suggestion, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(suggestion.priority)}`}>
                      {suggestion.priority}
                    </span>
                    <span className="text-xs text-gray-500 capitalize">{suggestion.category}</span>
                  </div>
                  <p className="font-medium text-gray-900">{suggestion.title}</p>
                  <p className="text-sm text-gray-600 mt-1">{suggestion.description}</p>
                  <p className="text-xs text-blue-600 mt-2">Impact: {suggestion.impact}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Section Scores */}
      {Object.keys(currentAnalysis.section_scores).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Section Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(currentAnalysis.section_scores).map(([section, data]) => (
                <div key={section} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{section}</h4>
                    <span className={`text-lg font-bold ${getScoreColor(data.score)}`}>
                      {data.score}%
                    </span>
                  </div>
                  {data.issues.length > 0 && (
                    <div className="mb-2">
                      <p className="text-sm text-gray-500 mb-1">Issues:</p>
                      <ul className="text-sm text-red-600 list-disc list-inside">
                        {data.issues.map((issue, i) => (
                          <li key={i}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {data.suggestions.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Suggestions:</p>
                      <ul className="text-sm text-blue-600 list-disc list-inside">
                        {data.suggestions.map((suggestion, i) => (
                          <li key={i}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Re-analyze button */}
      {content && (
        <div className="text-center">
          <Button variant="secondary" onClick={analyzeContent} disabled={isAnalyzing}>
            {isAnalyzing ? 'Analyzing...' : 'Re-analyze'}
          </Button>
        </div>
      )}
    </div>
  );
}
