'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface Report {
  id: string;
  title: string;
  report_type: string;
  status: string;
  created_at: string;
  period_start?: string;
  period_end?: string;
}

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newReport, setNewReport] = useState({
    title: '',
    report_type: 'progress',
    period_start: '',
    period_end: '',
  });

  const { data: reportsData, isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await api.get('/reports');
      return response.data;
    },
  });

  const { data: typesData } = useQuery({
    queryKey: ['report-types'],
    queryFn: async () => {
      const response = await api.get('/reports/types');
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof newReport) => {
      const response = await api.post('/reports/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      setShowCreateModal(false);
      setNewReport({
        title: '',
        report_type: 'progress',
        period_start: '',
        period_end: '',
      });
    },
  });

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      in_progress: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      submitted: 'bg-blue-100 text-blue-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      progress: '📊',
      financial: '💰',
      impact: '🎯',
      narrative: '📝',
      final: '📋',
    };
    return icons[type] || '📄';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-gray-600">Generate and manage project reports for funders and stakeholders.</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create Report</Button>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : reportsData?.reports?.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-3xl">📊</span>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">No Reports Yet</h3>
            <p className="text-sm text-gray-500 mb-4">
              Create your first report to track project progress and outcomes.
            </p>
            <Button onClick={() => setShowCreateModal(true)}>Create Report</Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {reportsData?.reports?.map((report: Report) => (
            <Card key={report.id} className="hover:shadow-lg transition cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <span className="text-3xl">{getTypeIcon(report.report_type)}</span>
                  <div className="flex-1">
                    <h3 className="font-medium">{report.title}</h3>
                    <p className="text-sm text-gray-500 capitalize">{report.report_type} Report</p>
                    {report.period_start && report.period_end && (
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(report.period_start).toLocaleDateString()} -{' '}
                        {new Date(report.period_end).toLocaleDateString()}
                      </p>
                    )}
                    <div className="flex justify-between items-center mt-3">
                      <span className={`px-2 py-1 rounded text-xs ${getStatusColor(report.status)}`}>
                        {report.status.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(report.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Report Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Create Report</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title *</label>
                <Input
                  value={newReport.title}
                  onChange={(e) => setNewReport({ ...newReport, title: e.target.value })}
                  placeholder="Report title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Report Type</label>
                <select
                  value={newReport.report_type}
                  onChange={(e) => setNewReport({ ...newReport, report_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {typesData?.types?.map((type: any) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Period Start</label>
                  <Input
                    type="date"
                    value={newReport.period_start}
                    onChange={(e) => setNewReport({ ...newReport, period_start: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Period End</label>
                  <Input
                    type="date"
                    value={newReport.period_end}
                    onChange={(e) => setNewReport({ ...newReport, period_end: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createMutation.mutate(newReport)}
                  disabled={!newReport.title || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Report'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
