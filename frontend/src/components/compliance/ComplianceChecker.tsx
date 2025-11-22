'use client';

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface ComplianceResult {
  overall_score: number;
  category_scores: Record<string, {
    name: string;
    score: number;
    passed: Array<{ check: string; message: string }>;
    failed: Array<{ check: string; message: string; severity: string }>;
    warnings: Array<{ check: string; message: string }>;
  }>;
  passed_checks: Array<{ check: string; message: string }>;
  failed_checks: Array<{ check: string; message: string; severity: string }>;
  warnings: Array<{ check: string; message: string }>;
  recommendations: Array<{
    priority: string;
    category: string;
    title: string;
    description: string;
    action: string;
  }>;
}

interface ComplianceCheckerProps {
  proposalId?: string;
  proposalContent?: string;
  guidelinesContent?: string;
  onComplete?: (results: ComplianceResult) => void;
}

export function ComplianceChecker({
  proposalId,
  proposalContent,
  guidelinesContent,
  onComplete,
}: ComplianceCheckerProps) {
  const [results, setResults] = useState<ComplianceResult | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const { data: categoriesData } = useQuery({
    queryKey: ['compliance-categories'],
    queryFn: async () => {
      const response = await api.get('/compliance/categories');
      return response.data;
    },
  });

  const checkMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/compliance/check', {
        proposal_id: proposalId,
        proposal_content: proposalContent,
        guidelines_content: guidelinesContent,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setResults(data.compliance_results);
      if (onComplete) {
        onComplete(data.compliance_results);
      }
    },
  });

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-gray-100 text-gray-800',
    };
    return colors[severity as keyof typeof colors] || colors.medium;
  };

  const getPriorityBadge = (priority: string) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    };
    return colors[priority as keyof typeof colors] || colors.medium;
  };

  return (
    <div className="space-y-6">
      {/* Check Button */}
      {!results && (
        <Card>
          <CardContent className="py-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">Compliance Checker</h3>
            <p className="text-sm text-gray-500 mb-4">
              Check your proposal against grant guidelines and requirements
            </p>
            <Button
              onClick={() => checkMutation.mutate()}
              disabled={checkMutation.isPending || (!proposalId && !proposalContent)}
            >
              {checkMutation.isPending ? 'Checking...' : 'Run Compliance Check'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {results && (
        <>
          {/* Overall Score */}
          <Card>
            <CardHeader>
              <CardTitle>Compliance Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <p className="text-sm text-gray-500">Overall Score</p>
                  <p className={`text-5xl font-bold ${getScoreColor(results.overall_score)}`}>
                    {results.overall_score}%
                  </p>
                </div>
                <div className="text-right">
                  <div className="flex gap-4">
                    <div>
                      <p className="text-2xl font-bold text-green-600">{results.passed_checks.length}</p>
                      <p className="text-xs text-gray-500">Passed</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-red-600">{results.failed_checks.length}</p>
                      <p className="text-xs text-gray-500">Failed</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-yellow-600">{results.warnings.length}</p>
                      <p className="text-xs text-gray-500">Warnings</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Score Bar */}
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className={`h-4 rounded-full ${getScoreBgColor(results.overall_score)}`}
                  style={{ width: `${results.overall_score}%` }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Category Scores */}
          <Card>
            <CardHeader>
              <CardTitle>Category Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(results.category_scores).map(([categoryId, category]) => (
                  <button
                    key={categoryId}
                    onClick={() => setActiveCategory(activeCategory === categoryId ? null : categoryId)}
                    className={`p-4 rounded-lg border text-left transition ${
                      activeCategory === categoryId
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{category.name}</span>
                      <span className={`text-lg font-bold ${getScoreColor(category.score)}`}>
                        {category.score}%
                      </span>
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${getScoreBgColor(category.score)}`}
                        style={{ width: `${category.score}%` }}
                      />
                    </div>
                    <div className="mt-2 flex gap-2 text-xs">
                      <span className="text-green-600">{category.passed.length} passed</span>
                      <span className="text-red-600">{category.failed.length} failed</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Category Details */}
              {activeCategory && results.category_scores[activeCategory] && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium mb-3">{results.category_scores[activeCategory].name} Details</h4>

                  {results.category_scores[activeCategory].passed.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-green-700 mb-2">Passed Checks</p>
                      {results.category_scores[activeCategory].passed.map((check, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-gray-600 py-1">
                          <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {check.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {results.category_scores[activeCategory].failed.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-red-700 mb-2">Failed Checks</p>
                      {results.category_scores[activeCategory].failed.map((check, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-gray-600 py-1">
                          <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                          <span>{check.message}</span>
                          <span className={`px-1.5 py-0.5 rounded text-xs ${getSeverityBadge(check.severity)}`}>
                            {check.severity}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {results.category_scores[activeCategory].warnings.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-yellow-700 mb-2">Warnings</p>
                      {results.category_scores[activeCategory].warnings.map((warning, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-gray-600 py-1">
                          <svg className="w-4 h-4 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          {warning.message}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recommendations */}
          {results.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {results.recommendations.map((rec, index) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${getPriorityBadge(rec.priority)}`}>
                          {rec.priority}
                        </span>
                        <span className="text-xs text-gray-500 capitalize">{rec.category}</span>
                      </div>
                      <p className="font-medium text-gray-900">{rec.title}</p>
                      <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                      <p className="text-xs text-blue-600 mt-2">Action: {rec.action}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Re-check Button */}
          <div className="text-center">
            <Button
              variant="secondary"
              onClick={() => {
                setResults(null);
                setActiveCategory(null);
              }}
            >
              Run New Check
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
