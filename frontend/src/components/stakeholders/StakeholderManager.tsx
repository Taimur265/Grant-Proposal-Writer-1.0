'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface Stakeholder {
  id: string;
  name: string;
  organization?: string;
  title?: string;
  stakeholder_type: string;
  email?: string;
  engagement_level: string;
  influence_level: string;
  interest_level: string;
  relationship_status?: string;
  tags?: string[];
}

interface StakeholderManagerProps {
  projectId?: string;
}

export function StakeholderManager({ projectId }: StakeholderManagerProps) {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedStakeholder, setSelectedStakeholder] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'matrix'>('list');
  const [filterType, setFilterType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const [newStakeholder, setNewStakeholder] = useState({
    name: '',
    organization: '',
    title: '',
    stakeholder_type: 'partner',
    email: '',
    phone: '',
    engagement_level: 'medium',
    influence_level: 'medium',
    interest_level: 'medium',
    notes: '',
  });

  const { data: stakeholdersData, isLoading } = useQuery({
    queryKey: ['stakeholders', projectId, filterType, searchQuery],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (projectId) params.append('project_id', projectId);
      if (filterType) params.append('stakeholder_type', filterType);
      if (searchQuery) params.append('search', searchQuery);
      const response = await api.get(`/stakeholders?${params.toString()}`);
      return response.data;
    },
  });

  const { data: matrixData } = useQuery({
    queryKey: ['stakeholder-matrix', projectId],
    queryFn: async () => {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/stakeholders/matrix${params}`);
      return response.data;
    },
    enabled: viewMode === 'matrix',
  });

  const { data: typesData } = useQuery({
    queryKey: ['stakeholder-types'],
    queryFn: async () => {
      const response = await api.get('/stakeholders/types');
      return response.data;
    },
  });

  const { data: stakeholderDetails } = useQuery({
    queryKey: ['stakeholder', selectedStakeholder],
    queryFn: async () => {
      const response = await api.get(`/stakeholders/${selectedStakeholder}`);
      return response.data;
    },
    enabled: !!selectedStakeholder,
  });

  const createMutation = useMutation({
    mutationFn: async (data: typeof newStakeholder) => {
      const response = await api.post('/stakeholders/', {
        ...data,
        project_id: projectId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stakeholders'] });
      queryClient.invalidateQueries({ queryKey: ['stakeholder-matrix'] });
      setShowAddModal(false);
      setNewStakeholder({
        name: '',
        organization: '',
        title: '',
        stakeholder_type: 'partner',
        email: '',
        phone: '',
        engagement_level: 'medium',
        influence_level: 'medium',
        interest_level: 'medium',
        notes: '',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/stakeholders/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stakeholders'] });
      queryClient.invalidateQueries({ queryKey: ['stakeholder-matrix'] });
      setSelectedStakeholder(null);
    },
  });

  const getEngagementColor = (level: string) => {
    const colors: Record<string, string> = {
      high: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-red-100 text-red-800',
    };
    return colors[level] || 'bg-gray-100 text-gray-800';
  };

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      funder: '💰',
      partner: '🤝',
      beneficiary: '👥',
      government: '🏛️',
      community: '🏘️',
      media: '📰',
      board_member: '👔',
      staff: '👤',
      volunteer: '🙋',
      other: '📌',
    };
    return icons[type] || '📌';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Stakeholder Management</h2>
        <div className="flex gap-2">
          <div className="flex border rounded-lg">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 text-sm ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'bg-white'}`}
            >
              List
            </button>
            <button
              onClick={() => setViewMode('matrix')}
              className={`px-3 py-1.5 text-sm ${viewMode === 'matrix' ? 'bg-blue-500 text-white' : 'bg-white'}`}
            >
              Matrix
            </button>
          </div>
          <Button onClick={() => setShowAddModal(true)}>Add Stakeholder</Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search stakeholders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border rounded-lg"
            >
              <option value="">All Types</option>
              {typesData?.types?.map((type: any) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {viewMode === 'list' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stakeholder List */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Stakeholders ({stakeholdersData?.total || 0})</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="animate-pulse space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-20 bg-gray-200 rounded" />
                    ))}
                  </div>
                ) : stakeholdersData?.stakeholders?.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No stakeholders found</p>
                ) : (
                  <div className="space-y-3">
                    {stakeholdersData?.stakeholders?.map((stakeholder: Stakeholder) => (
                      <div
                        key={stakeholder.id}
                        onClick={() => setSelectedStakeholder(stakeholder.id)}
                        className={`p-4 border rounded-lg cursor-pointer transition hover:shadow-md ${
                          selectedStakeholder === stakeholder.id ? 'border-blue-500 bg-blue-50' : ''
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex gap-3">
                            <span className="text-2xl">{getTypeIcon(stakeholder.stakeholder_type)}</span>
                            <div>
                              <h4 className="font-medium">{stakeholder.name}</h4>
                              {stakeholder.organization && (
                                <p className="text-sm text-gray-500">{stakeholder.organization}</p>
                              )}
                              {stakeholder.title && (
                                <p className="text-xs text-gray-400">{stakeholder.title}</p>
                              )}
                            </div>
                          </div>
                          <span className={`px-2 py-1 rounded text-xs ${getEngagementColor(stakeholder.engagement_level)}`}>
                            {stakeholder.engagement_level}
                          </span>
                        </div>
                        <div className="flex gap-2 mt-2">
                          <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                            Influence: {stakeholder.influence_level}
                          </span>
                          <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                            Interest: {stakeholder.interest_level}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Stakeholder Details */}
          <div className="lg:col-span-1">
            {selectedStakeholder && stakeholderDetails ? (
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle>{stakeholderDetails.name}</CardTitle>
                    <button
                      onClick={() => deleteMutation.mutate(selectedStakeholder)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Organization</p>
                    <p className="font-medium">{stakeholderDetails.organization || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Title</p>
                    <p className="font-medium">{stakeholderDetails.title || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium">{stakeholderDetails.email || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Phone</p>
                    <p className="font-medium">{stakeholderDetails.phone || '-'}</p>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-xs text-gray-500">Engagement</p>
                      <p className="font-medium text-sm">{stakeholderDetails.engagement_level}</p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-xs text-gray-500">Influence</p>
                      <p className="font-medium text-sm">{stakeholderDetails.influence_level}</p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-xs text-gray-500">Interest</p>
                      <p className="font-medium text-sm">{stakeholderDetails.interest_level}</p>
                    </div>
                  </div>

                  {stakeholderDetails.recent_interactions?.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-500 mb-2">Recent Interactions</p>
                      <div className="space-y-2">
                        {stakeholderDetails.recent_interactions.map((interaction: any) => (
                          <div key={interaction.id} className="p-2 bg-gray-50 rounded text-sm">
                            <p className="font-medium">{interaction.subject}</p>
                            <p className="text-xs text-gray-500">
                              {new Date(interaction.date).toLocaleDateString()}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {stakeholderDetails.commitments?.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-500 mb-2">Commitments</p>
                      <div className="space-y-2">
                        {stakeholderDetails.commitments.map((commitment: any) => (
                          <div key={commitment.id} className="p-2 bg-blue-50 rounded text-sm">
                            <p className="font-medium">{commitment.description}</p>
                            {commitment.amount && (
                              <p className="text-xs text-blue-600">
                                ${commitment.amount.toLocaleString()}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="py-12 text-center text-gray-500">
                  Select a stakeholder to view details
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      ) : (
        /* Matrix View */
        <Card>
          <CardHeader>
            <CardTitle>Stakeholder Analysis Matrix</CardTitle>
            <p className="text-sm text-gray-500">Influence vs Interest</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              {/* High Influence, High Interest */}
              <div className="p-4 bg-green-50 border-2 border-green-200 rounded-lg min-h-[200px]">
                <h4 className="font-semibold text-green-800 mb-2">Key Players</h4>
                <p className="text-xs text-green-600 mb-3">High Influence, High Interest - Engage Closely</p>
                <div className="space-y-2">
                  {matrixData?.matrix?.high_influence_high_interest?.map((s: any) => (
                    <div key={s.id} className="p-2 bg-white rounded shadow-sm">
                      <p className="font-medium text-sm">{s.name}</p>
                      <p className="text-xs text-gray-500">{s.organization}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* High Influence, Low Interest */}
              <div className="p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg min-h-[200px]">
                <h4 className="font-semibold text-yellow-800 mb-2">Keep Satisfied</h4>
                <p className="text-xs text-yellow-600 mb-3">High Influence, Low Interest - Keep Satisfied</p>
                <div className="space-y-2">
                  {matrixData?.matrix?.high_influence_low_interest?.map((s: any) => (
                    <div key={s.id} className="p-2 bg-white rounded shadow-sm">
                      <p className="font-medium text-sm">{s.name}</p>
                      <p className="text-xs text-gray-500">{s.organization}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Low Influence, High Interest */}
              <div className="p-4 bg-blue-50 border-2 border-blue-200 rounded-lg min-h-[200px]">
                <h4 className="font-semibold text-blue-800 mb-2">Keep Informed</h4>
                <p className="text-xs text-blue-600 mb-3">Low Influence, High Interest - Keep Informed</p>
                <div className="space-y-2">
                  {matrixData?.matrix?.low_influence_high_interest?.map((s: any) => (
                    <div key={s.id} className="p-2 bg-white rounded shadow-sm">
                      <p className="font-medium text-sm">{s.name}</p>
                      <p className="text-xs text-gray-500">{s.organization}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Low Influence, Low Interest */}
              <div className="p-4 bg-gray-50 border-2 border-gray-200 rounded-lg min-h-[200px]">
                <h4 className="font-semibold text-gray-800 mb-2">Monitor</h4>
                <p className="text-xs text-gray-600 mb-3">Low Influence, Low Interest - Monitor</p>
                <div className="space-y-2">
                  {matrixData?.matrix?.low_influence_low_interest?.map((s: any) => (
                    <div key={s.id} className="p-2 bg-white rounded shadow-sm">
                      <p className="font-medium text-sm">{s.name}</p>
                      <p className="text-xs text-gray-500">{s.organization}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Stakeholder Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Add Stakeholder</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <Input
                  value={newStakeholder.name}
                  onChange={(e) => setNewStakeholder({ ...newStakeholder, name: e.target.value })}
                  placeholder="Stakeholder name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Organization</label>
                <Input
                  value={newStakeholder.organization}
                  onChange={(e) => setNewStakeholder({ ...newStakeholder, organization: e.target.value })}
                  placeholder="Organization name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <Input
                  value={newStakeholder.title}
                  onChange={(e) => setNewStakeholder({ ...newStakeholder, title: e.target.value })}
                  placeholder="Job title"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Email</label>
                  <Input
                    type="email"
                    value={newStakeholder.email}
                    onChange={(e) => setNewStakeholder({ ...newStakeholder, email: e.target.value })}
                    placeholder="Email address"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Phone</label>
                  <Input
                    value={newStakeholder.phone}
                    onChange={(e) => setNewStakeholder({ ...newStakeholder, phone: e.target.value })}
                    placeholder="Phone number"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={newStakeholder.stakeholder_type}
                  onChange={(e) => setNewStakeholder({ ...newStakeholder, stakeholder_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {typesData?.types?.map((type: any) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Engagement</label>
                  <select
                    value={newStakeholder.engagement_level}
                    onChange={(e) => setNewStakeholder({ ...newStakeholder, engagement_level: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Influence</label>
                  <select
                    value={newStakeholder.influence_level}
                    onChange={(e) => setNewStakeholder({ ...newStakeholder, influence_level: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Interest</label>
                  <select
                    value={newStakeholder.interest_level}
                    onChange={(e) => setNewStakeholder({ ...newStakeholder, interest_level: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={newStakeholder.notes}
                  onChange={(e) => setNewStakeholder({ ...newStakeholder, notes: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="Additional notes"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createMutation.mutate(newStakeholder)}
                  disabled={!newStakeholder.name || createMutation.isPending}
                >
                  {createMutation.isPending ? 'Adding...' : 'Add Stakeholder'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
