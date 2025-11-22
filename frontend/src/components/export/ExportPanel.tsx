'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface ExportPanelProps {
  projectId: string;
  proposalId?: string;
}

interface ProjectReport {
  generated_at: string;
  project: {
    name: string;
    description: string;
    status: string;
    grant_type: string;
    deadline: string | null;
  };
  statistics: {
    total_documents: number;
    total_proposals: number;
    documents_by_category: Record<string, number>;
    documents_by_status: Record<string, number>;
    best_compliance_score: number | null;
  };
  recommendations: Array<{
    priority: string;
    message: string;
  }>;
}

export function ExportPanel({ projectId, proposalId }: ExportPanelProps) {
  const [isExporting, setIsExporting] = useState<string | null>(null);

  const { data: report, isLoading } = useQuery({
    queryKey: ['project-report', projectId],
    queryFn: async () => {
      const response = await api.get<ProjectReport>(`/export/projects/${projectId}/report`);
      return response.data;
    },
  });

  const handleExport = async (format: string, type: 'proposal' | 'documents' | 'report') => {
    setIsExporting(format);

    try {
      let endpoint = '';
      let filename = '';

      if (type === 'proposal' && proposalId) {
        endpoint = `/export/proposals/${proposalId}/${format}`;
        filename = `proposal.${format === 'markdown' ? 'md' : format}`;
      } else if (type === 'documents') {
        endpoint = `/export/projects/${projectId}/documents/csv`;
        filename = 'documents.csv';
      } else if (type === 'report') {
        endpoint = `/export/projects/${projectId}/report/json`;
        filename = 'project_report.json';
      }

      const response = await api.get(endpoint, { responseType: 'blob' });

      // Create download link
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Project Report Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Project Report</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
            </div>
          ) : report ? (
            <div className="space-y-6">
              {/* Statistics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold text-blue-600">{report.statistics.total_documents}</p>
                  <p className="text-sm text-blue-700">Documents</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold text-green-600">{report.statistics.total_proposals}</p>
                  <p className="text-sm text-green-700">Proposals</p>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    {report.statistics.best_compliance_score ? `${report.statistics.best_compliance_score}%` : 'N/A'}
                  </p>
                  <p className="text-sm text-purple-700">Best Score</p>
                </div>
                <div className="bg-orange-50 p-4 rounded-lg text-center">
                  <p className="text-2xl font-bold text-orange-600 capitalize">{report.project.status}</p>
                  <p className="text-sm text-orange-700">Status</p>
                </div>
              </div>

              {/* Documents by Category */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Documents by Category</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(report.statistics.documents_by_category).map(([category, count]) => (
                    <span key={category} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                      {category}: <span className="font-medium">{count}</span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Recommendations */}
              {report.recommendations.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Recommendations</h4>
                  <div className="space-y-2">
                    {report.recommendations.map((rec, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg text-sm ${
                          rec.priority === 'high'
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                        }`}
                      >
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mr-2 ${
                          rec.priority === 'high' ? 'bg-red-100' : 'bg-yellow-100'
                        }`}>
                          {rec.priority}
                        </span>
                        {rec.message}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Unable to load report</p>
          )}
        </CardContent>
      </Card>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle>Export Options</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Proposal Export */}
            {proposalId && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Export Proposal</h4>
                <div className="flex flex-wrap gap-3">
                  <Button
                    variant="secondary"
                    onClick={() => handleExport('markdown', 'proposal')}
                    disabled={isExporting === 'markdown'}
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    {isExporting === 'markdown' ? 'Exporting...' : 'Markdown (.md)'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => handleExport('html', 'proposal')}
                    disabled={isExporting === 'html'}
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                    </svg>
                    {isExporting === 'html' ? 'Exporting...' : 'HTML (.html)'}
                  </Button>
                </div>
              </div>
            )}

            {/* Documents Export */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Export Documents List</h4>
              <Button
                variant="secondary"
                onClick={() => handleExport('csv', 'documents')}
                disabled={isExporting === 'csv'}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {isExporting === 'csv' ? 'Exporting...' : 'CSV Spreadsheet (.csv)'}
              </Button>
            </div>

            {/* Full Report Export */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Export Full Report</h4>
              <Button
                variant="secondary"
                onClick={() => handleExport('json', 'report')}
                disabled={isExporting === 'json'}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {isExporting === 'json' ? 'Exporting...' : 'JSON Report (.json)'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report Info */}
      <div className="text-center text-sm text-gray-500">
        <p>Generated: {report?.generated_at ? new Date(report.generated_at).toLocaleString() : 'N/A'}</p>
      </div>
    </div>
  );
}
