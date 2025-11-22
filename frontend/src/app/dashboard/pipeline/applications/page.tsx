'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

const STAGES = [
  { key: 'prospect', label: 'Prospect', color: 'bg-gray-100' },
  { key: 'researching', label: 'Researching', color: 'bg-blue-100' },
  { key: 'loi_in_progress', label: 'LOI In Progress', color: 'bg-yellow-100' },
  { key: 'proposal_in_progress', label: 'Proposal In Progress', color: 'bg-orange-100' },
  { key: 'submitted', label: 'Submitted', color: 'bg-purple-100' },
  { key: 'awarded', label: 'Awarded', color: 'bg-green-100' },
  { key: 'declined', label: 'Declined', color: 'bg-red-100' },
];

export default function ApplicationsPage() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [newApplication, setNewApplication] = useState({
    application_name: '',
    funder_name: '',
    amount_requested: '',
    application_deadline: '',
    priority: 'medium',
  });

  const { data: pipelineData, isLoading } = useQuery({
    queryKey: ['pipeline'],
    queryFn: async () => {
      const response = await api.get('/applications/pipeline');
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/applications/', {
        ...data,
        amount_requested: data.amount_requested ? parseFloat(data.amount_requested) : null,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
      setShowAddModal(false);
      setNewApplication({
        application_name: '',
        funder_name: '',
        amount_requested: '',
        application_deadline: '',
        priority: 'medium',
      });
    },
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Grant Applications Pipeline</h1>
          <p className="text-gray-600">Track applications from prospect to award</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>Add Application</Button>
      </div>

      {/* Pipeline Summary */}
      {pipelineData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">
                {pipelineData.summary.total_applications}
              </p>
              <p className="text-sm text-gray-500">Total Applications</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-600">
                {formatCurrency(pipelineData.summary.total_pipeline_value || 0)}
              </p>
              <p className="text-sm text-gray-500">Pipeline Value</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-600">
                {formatCurrency(pipelineData.summary.weighted_pipeline_value || 0)}
              </p>
              <p className="text-sm text-gray-500">Weighted Value</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Kanban Board */}
      {isLoading ? (
        <div className="grid grid-cols-7 gap-4">
          {STAGES.map((stage) => (
            <div key={stage.key} className="h-96 bg-gray-200 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <div className="flex gap-4 min-w-max pb-4">
            {STAGES.map((stage) => (
              <div
                key={stage.key}
                className={`w-72 ${stage.color} rounded-lg p-4 min-h-[500px]`}
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold text-sm">{stage.label}</h3>
                  <span className="px-2 py-0.5 bg-white rounded-full text-xs">
                    {pipelineData?.pipeline?.[stage.key]?.length || 0}
                  </span>
                </div>

                <div className="space-y-3">
                  {pipelineData?.pipeline?.[stage.key]?.map((app: any) => (
                    <Card key={app.id} className="cursor-pointer hover:shadow-md transition">
                      <CardContent className="p-3">
                        <h4 className="font-medium text-sm truncate">{app.application_name}</h4>
                        <p className="text-xs text-gray-500 truncate">{app.funder_name}</p>
                        {app.amount_requested && (
                          <p className="text-sm font-semibold text-green-600 mt-2">
                            {formatCurrency(app.amount_requested)}
                          </p>
                        )}
                        {app.deadline && (
                          <p className="text-xs text-gray-400 mt-1">
                            Due: {new Date(app.deadline).toLocaleDateString()}
                          </p>
                        )}
                        <div className="flex justify-between items-center mt-2">
                          <span className={`px-1.5 py-0.5 rounded text-xs ${
                            app.priority === 'high' ? 'bg-red-100 text-red-700' :
                            app.priority === 'low' ? 'bg-gray-100 text-gray-700' :
                            'bg-yellow-100 text-yellow-700'
                          }`}>
                            {app.priority}
                          </span>
                          {app.probability && (
                            <span className="text-xs text-gray-500">{app.probability}%</span>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Application Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Application</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Application Name *</label>
                <Input
                  value={newApplication.application_name}
                  onChange={(e) => setNewApplication({ ...newApplication, application_name: e.target.value })}
                  placeholder="Grant application name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Funder Name *</label>
                <Input
                  value={newApplication.funder_name}
                  onChange={(e) => setNewApplication({ ...newApplication, funder_name: e.target.value })}
                  placeholder="Funder organization"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Amount Requested</label>
                <Input
                  type="number"
                  value={newApplication.amount_requested}
                  onChange={(e) => setNewApplication({ ...newApplication, amount_requested: e.target.value })}
                  placeholder="50000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Deadline</label>
                <Input
                  type="datetime-local"
                  value={newApplication.application_deadline}
                  onChange={(e) => setNewApplication({ ...newApplication, application_deadline: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Priority</label>
                <select
                  value={newApplication.priority}
                  onChange={(e) => setNewApplication({ ...newApplication, priority: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newApplication)}
                  disabled={!newApplication.application_name || !newApplication.funder_name}
                >
                  Add Application
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
