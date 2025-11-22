'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export default function AwardedGrantsPage() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedGrant, setSelectedGrant] = useState<string | null>(null);

  const [newGrant, setNewGrant] = useState({
    grant_title: '',
    funder_name: '',
    total_award_amount: '',
    award_date: '',
    project_start_date: '',
    project_end_date: '',
    project_director: '',
  });

  const { data: dashboardData } = useQuery({
    queryKey: ['post-award-dashboard'],
    queryFn: async () => {
      const response = await api.get('/post-award/dashboard');
      return response.data;
    },
  });

  const { data: grantsData, isLoading } = useQuery({
    queryKey: ['awarded-grants'],
    queryFn: async () => {
      const response = await api.get('/post-award/grants');
      return response.data;
    },
  });

  const { data: grantDetails } = useQuery({
    queryKey: ['awarded-grant', selectedGrant],
    queryFn: async () => {
      const response = await api.get(`/post-award/grants/${selectedGrant}`);
      return response.data;
    },
    enabled: !!selectedGrant,
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/post-award/grants', {
        ...data,
        total_award_amount: parseFloat(data.total_award_amount),
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['awarded-grants'] });
      queryClient.invalidateQueries({ queryKey: ['post-award-dashboard'] });
      setShowAddModal(false);
    },
  });

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      on_hold: 'bg-yellow-100 text-yellow-800',
      closing: 'bg-orange-100 text-orange-800',
      closed: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Awarded Grants</h1>
          <p className="text-gray-600">Manage post-award grant activities, reporting, and compliance</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>Add Awarded Grant</Button>
      </div>

      {/* Dashboard Summary */}
      {dashboardData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-green-600">
                {dashboardData.summary.active_grants}
              </p>
              <p className="text-sm text-gray-500">Active Grants</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">
                {formatCurrency(dashboardData.summary.total_active_funding || 0)}
              </p>
              <p className="text-sm text-gray-500">Total Funding</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-600">
                {formatCurrency(dashboardData.summary.total_received || 0)}
              </p>
              <p className="text-sm text-gray-500">Received</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-orange-600">
                {dashboardData.summary.pending_reports}
              </p>
              <p className="text-sm text-gray-500">Pending Reports</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Grants List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Grants ({grantsData?.grants?.length || 0})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 max-h-[600px] overflow-y-auto">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-24 bg-gray-200 rounded animate-pulse" />
                  ))}
                </div>
              ) : grantsData?.grants?.length === 0 ? (
                <p className="text-center text-gray-500 py-4">No awarded grants yet</p>
              ) : (
                grantsData?.grants?.map((grant: any) => (
                  <div
                    key={grant.id}
                    onClick={() => setSelectedGrant(grant.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition hover:shadow-md ${
                      selectedGrant === grant.id ? 'border-blue-500 bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <h4 className="font-medium">{grant.grant_title}</h4>
                      <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(grant.status)}`}>
                        {grant.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">{grant.funder_name}</p>
                    <p className="text-lg font-semibold text-green-600 mt-2">
                      {formatCurrency(grant.total_award_amount)}
                    </p>
                    <div className="flex justify-between items-center mt-2 text-xs text-gray-400">
                      <span>Ends: {new Date(grant.project_end_date).toLocaleDateString()}</span>
                      <span className={grant.days_remaining < 90 ? 'text-red-500' : ''}>
                        {grant.days_remaining} days left
                      </span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Grant Details */}
        <div className="lg:col-span-2">
          {selectedGrant && grantDetails ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>{grantDetails.grant_title}</CardTitle>
                      <p className="text-sm text-gray-500">{grantDetails.funder_name}</p>
                      {grantDetails.grant_number && (
                        <p className="text-xs text-gray-400">Grant #: {grantDetails.grant_number}</p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded ${getStatusColor(grantDetails.status)}`}>
                      {grantDetails.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-green-50 rounded-lg text-center">
                      <p className="text-xl font-bold text-green-600">
                        {formatCurrency(grantDetails.total_award_amount)}
                      </p>
                      <p className="text-xs text-gray-500">Total Award</p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg text-center">
                      <p className="text-xl font-bold text-blue-600">
                        {formatCurrency(grantDetails.amount_received)}
                      </p>
                      <p className="text-xs text-gray-500">Received</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg text-center">
                      <p className="text-xl font-bold">
                        {new Date(grantDetails.project_start_date).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500">Start Date</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg text-center">
                      <p className="text-xl font-bold">
                        {new Date(grantDetails.project_end_date).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-gray-500">End Date</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Budget Summary */}
              {grantDetails.budget_summary && (
                <Card>
                  <CardHeader>
                    <CardTitle>Budget Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Total Budgeted</span>
                        <span className="font-semibold">{formatCurrency(grantDetails.budget_summary.total_budgeted)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Total Spent</span>
                        <span className="font-semibold text-blue-600">{formatCurrency(grantDetails.budget_summary.total_spent)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-gray-600">Remaining</span>
                        <span className="font-semibold text-green-600">{formatCurrency(grantDetails.budget_summary.remaining)}</span>
                      </div>
                      <div className="pt-2">
                        <div className="flex justify-between text-sm mb-1">
                          <span>Burn Rate</span>
                          <span>{grantDetails.budget_summary.burn_rate.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className="bg-blue-500 h-3 rounded-full"
                            style={{ width: `${Math.min(grantDetails.budget_summary.burn_rate, 100)}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Reporting Requirements */}
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle>Reporting Requirements</CardTitle>
                    <Button size="sm">Add Requirement</Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {grantDetails.reporting_requirements?.length === 0 ? (
                    <p className="text-center text-gray-500 py-4">No reporting requirements set</p>
                  ) : (
                    <div className="space-y-3">
                      {grantDetails.reporting_requirements?.map((req: any) => (
                        <div key={req.id} className="flex justify-between items-center p-3 border rounded-lg">
                          <div>
                            <h4 className="font-medium">{req.report_name}</h4>
                            <p className="text-xs text-gray-500 capitalize">{req.report_type} - {req.frequency}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm">Due: {new Date(req.due_date).toLocaleDateString()}</p>
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              req.status === 'submitted' ? 'bg-green-100 text-green-800' :
                              req.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {req.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Deliverables */}
              {grantDetails.deliverables?.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Deliverables</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {grantDetails.deliverables?.map((del: any) => (
                        <div key={del.id} className="flex justify-between items-center p-3 border rounded-lg">
                          <div>
                            <h4 className="font-medium">{del.deliverable_name}</h4>
                          </div>
                          <div className="text-right">
                            <p className="text-sm">Due: {new Date(del.due_date).toLocaleDateString()}</p>
                            <span className={`px-2 py-0.5 rounded text-xs ${
                              del.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {del.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                Select an awarded grant to view details and manage post-award activities
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Add Grant Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Awarded Grant</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Grant Title *</label>
                <Input
                  value={newGrant.grant_title}
                  onChange={(e) => setNewGrant({ ...newGrant, grant_title: e.target.value })}
                  placeholder="Grant title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Funder Name *</label>
                <Input
                  value={newGrant.funder_name}
                  onChange={(e) => setNewGrant({ ...newGrant, funder_name: e.target.value })}
                  placeholder="Funder organization"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Award Amount *</label>
                <Input
                  type="number"
                  value={newGrant.total_award_amount}
                  onChange={(e) => setNewGrant({ ...newGrant, total_award_amount: e.target.value })}
                  placeholder="100000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Award Date *</label>
                <Input
                  type="date"
                  value={newGrant.award_date}
                  onChange={(e) => setNewGrant({ ...newGrant, award_date: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Start Date *</label>
                  <Input
                    type="date"
                    value={newGrant.project_start_date}
                    onChange={(e) => setNewGrant({ ...newGrant, project_start_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">End Date *</label>
                  <Input
                    type="date"
                    value={newGrant.project_end_date}
                    onChange={(e) => setNewGrant({ ...newGrant, project_end_date: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Project Director</label>
                <Input
                  value={newGrant.project_director}
                  onChange={(e) => setNewGrant({ ...newGrant, project_director: e.target.value })}
                  placeholder="Name"
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newGrant)}
                  disabled={!newGrant.grant_title || !newGrant.funder_name || !newGrant.total_award_amount}
                >
                  Add Grant
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
