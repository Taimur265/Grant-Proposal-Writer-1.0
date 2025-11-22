'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface Metric {
  id: string;
  name: string;
  metric_type: string;
  unit: string;
  baseline_value?: number;
  target_value: number;
  current_value: number;
  progress_percentage: number;
  on_track: boolean;
}

interface Report {
  id: string;
  title: string;
  report_type: string;
  status: string;
  period_start: string;
  period_end: string;
  due_date?: string;
}

export function MetricsDashboard({ projectId }: { projectId?: string }) {
  const queryClient = useQueryClient();
  const [showAddMetric, setShowAddMetric] = useState(false);
  const [newMetric, setNewMetric] = useState({
    name: '',
    metric_type: 'output',
    unit: '',
    target_value: 0,
    baseline_value: 0,
  });

  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['reporting-summary', projectId],
    queryFn: async () => {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/reporting/dashboard/summary${params}`);
      return response.data;
    },
  });

  const { data: metricsData, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics', projectId],
    queryFn: async () => {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/reporting/metrics${params}`);
      return response.data;
    },
  });

  const { data: reportsData } = useQuery({
    queryKey: ['reports', projectId],
    queryFn: async () => {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/reporting/reports${params}`);
      return response.data;
    },
  });

  const createMetricMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/reporting/metrics', {
        ...data,
        project_id: projectId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
      queryClient.invalidateQueries({ queryKey: ['reporting-summary'] });
      setShowAddMetric(false);
      setNewMetric({ name: '', metric_type: 'output', unit: '', target_value: 0, baseline_value: 0 });
    },
  });

  const getProgressColor = (percentage: number, onTrack: boolean) => {
    if (!onTrack) return 'bg-red-500';
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summaryData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{summaryData.metrics.total}</p>
              <p className="text-sm text-gray-500">Total Metrics</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-600">{summaryData.metrics.on_track}</p>
              <p className="text-sm text-gray-500">On Track</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-red-600">{summaryData.metrics.off_track}</p>
              <p className="text-sm text-gray-500">Off Track</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-600">{summaryData.metrics.avg_progress.toFixed(0)}%</p>
              <p className="text-sm text-gray-500">Avg Progress</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Metrics List */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Metrics & Indicators</CardTitle>
            <Button size="sm" onClick={() => setShowAddMetric(true)}>Add Metric</Button>
          </div>
        </CardHeader>
        <CardContent>
          {metricsLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-gray-200 rounded" />
              ))}
            </div>
          ) : metricsData?.metrics?.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No metrics defined yet</p>
          ) : (
            <div className="space-y-4">
              {metricsData?.metrics?.map((metric: Metric) => (
                <div key={metric.id} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-medium">{metric.name}</h4>
                      <p className="text-sm text-gray-500">{metric.metric_type} | {metric.unit}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      metric.on_track ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {metric.on_track ? 'On Track' : 'Off Track'}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span>Progress: {metric.progress_percentage.toFixed(0)}%</span>
                        <span>{metric.current_value} / {metric.target_value} {metric.unit}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getProgressColor(metric.progress_percentage, metric.on_track)}`}
                          style={{ width: `${Math.min(metric.progress_percentage, 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upcoming Reports */}
      {summaryData?.upcoming_reports?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Reports</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {summaryData.upcoming_reports.map((report: any) => (
                <div key={report.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span className="font-medium">{report.title}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    report.days_until <= 7 ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    Due in {report.days_until} days
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Metric Modal */}
      {showAddMetric && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Metric</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <Input
                  value={newMetric.name}
                  onChange={(e) => setNewMetric({ ...newMetric, name: e.target.value })}
                  placeholder="e.g., People Trained"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={newMetric.metric_type}
                  onChange={(e) => setNewMetric({ ...newMetric, metric_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="output">Output</option>
                  <option value="outcome">Outcome</option>
                  <option value="impact">Impact</option>
                  <option value="process">Process</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Unit</label>
                <Input
                  value={newMetric.unit}
                  onChange={(e) => setNewMetric({ ...newMetric, unit: e.target.value })}
                  placeholder="e.g., people, sessions, dollars"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Baseline</label>
                  <Input
                    type="number"
                    value={newMetric.baseline_value}
                    onChange={(e) => setNewMetric({ ...newMetric, baseline_value: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Target</label>
                  <Input
                    type="number"
                    value={newMetric.target_value}
                    onChange={(e) => setNewMetric({ ...newMetric, target_value: Number(e.target.value) })}
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowAddMetric(false)}>Cancel</Button>
                <Button onClick={() => createMetricMutation.mutate(newMetric)}>Add</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
