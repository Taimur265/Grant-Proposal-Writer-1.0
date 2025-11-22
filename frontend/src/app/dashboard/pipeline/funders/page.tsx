'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export default function FundersPage() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedFunder, setSelectedFunder] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');

  const [newFunder, setNewFunder] = useState({
    name: '',
    funder_type: 'foundation',
    website: '',
    focus_areas: '',
    average_grant_size: '',
    notes: '',
  });

  const { data: fundersData, isLoading } = useQuery({
    queryKey: ['funders', filterType, searchQuery],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filterType) params.append('funder_type', filterType);
      if (searchQuery) params.append('search', searchQuery);
      const response = await api.get(`/funder-research/funders?${params.toString()}`);
      return response.data;
    },
  });

  const { data: funderDetails } = useQuery({
    queryKey: ['funder', selectedFunder],
    queryFn: async () => {
      const response = await api.get(`/funder-research/funders/${selectedFunder}`);
      return response.data;
    },
    enabled: !!selectedFunder,
  });

  const { data: typesData } = useQuery({
    queryKey: ['funder-types'],
    queryFn: async () => {
      const response = await api.get('/funder-research/types');
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/funder-research/funders', {
        ...data,
        focus_areas: data.focus_areas ? data.focus_areas.split(',').map((s: string) => s.trim()) : [],
        average_grant_size: data.average_grant_size ? parseFloat(data.average_grant_size) : null,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['funders'] });
      setShowAddModal(false);
      setNewFunder({
        name: '',
        funder_type: 'foundation',
        website: '',
        focus_areas: '',
        average_grant_size: '',
        notes: '',
      });
    },
  });

  const getFitScoreColor = (score: string) => {
    const colors: Record<string, string> = {
      excellent: 'bg-green-100 text-green-800',
      good: 'bg-blue-100 text-blue-800',
      fair: 'bg-yellow-100 text-yellow-800',
      poor: 'bg-red-100 text-red-800',
    };
    return colors[score] || 'bg-gray-100 text-gray-800';
  };

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
          <h1 className="text-2xl font-bold">Funder Research</h1>
          <p className="text-gray-600">Research and track potential funders for your organization</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>Add Funder</Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search funders..."
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
              {typesData?.funder_types?.map((type: any) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Funders List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Funders ({fundersData?.funders?.length || 0})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 max-h-[600px] overflow-y-auto">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-24 bg-gray-200 rounded animate-pulse" />
                  ))}
                </div>
              ) : fundersData?.funders?.length === 0 ? (
                <p className="text-center text-gray-500 py-4">No funders found</p>
              ) : (
                fundersData?.funders?.map((funder: any) => (
                  <div
                    key={funder.id}
                    onClick={() => setSelectedFunder(funder.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition hover:shadow-md ${
                      selectedFunder === funder.id ? 'border-blue-500 bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <h4 className="font-medium">{funder.name}</h4>
                      {funder.fit_score && (
                        <span className={`px-2 py-0.5 rounded text-xs ${getFitScoreColor(funder.fit_score)}`}>
                          {funder.fit_score}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 capitalize">{funder.funder_type.replace('_', ' ')}</p>
                    {funder.average_grant_size && (
                      <p className="text-sm text-green-600 mt-1">
                        Avg: {formatCurrency(funder.average_grant_size)}
                      </p>
                    )}
                    {funder.focus_areas?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {funder.focus_areas.slice(0, 3).map((area: string, i: number) => (
                          <span key={i} className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">
                            {area}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Funder Details */}
        <div className="lg:col-span-2">
          {selectedFunder && funderDetails ? (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{funderDetails.name}</CardTitle>
                    <p className="text-sm text-gray-500 capitalize mt-1">
                      {funderDetails.funder_type.replace('_', ' ')}
                    </p>
                  </div>
                  {funderDetails.fit_score && (
                    <span className={`px-3 py-1 rounded ${getFitScoreColor(funderDetails.fit_score)}`}>
                      Fit: {funderDetails.fit_score}
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Contact Info */}
                <div className="grid grid-cols-2 gap-4">
                  {funderDetails.website && (
                    <div>
                      <p className="text-sm text-gray-500">Website</p>
                      <a
                        href={funderDetails.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {funderDetails.website}
                      </a>
                    </div>
                  )}
                  {funderDetails.email && (
                    <div>
                      <p className="text-sm text-gray-500">Email</p>
                      <p>{funderDetails.email}</p>
                    </div>
                  )}
                  {funderDetails.program_officer && (
                    <div>
                      <p className="text-sm text-gray-500">Program Officer</p>
                      <p>{funderDetails.program_officer}</p>
                    </div>
                  )}
                </div>

                {/* Funding Info */}
                <div>
                  <h4 className="font-semibold mb-3">Funding Information</h4>
                  <div className="grid grid-cols-3 gap-4">
                    {funderDetails.total_annual_giving && (
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-lg font-bold text-green-600">
                          {formatCurrency(funderDetails.total_annual_giving)}
                        </p>
                        <p className="text-xs text-gray-500">Annual Giving</p>
                      </div>
                    )}
                    {funderDetails.average_grant_size && (
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-lg font-bold text-blue-600">
                          {formatCurrency(funderDetails.average_grant_size)}
                        </p>
                        <p className="text-xs text-gray-500">Avg Grant Size</p>
                      </div>
                    )}
                    {funderDetails.grant_range_max && (
                      <div className="p-3 bg-gray-50 rounded-lg text-center">
                        <p className="text-lg font-bold text-purple-600">
                          {formatCurrency(funderDetails.grant_range_min || 0)} - {formatCurrency(funderDetails.grant_range_max)}
                        </p>
                        <p className="text-xs text-gray-500">Grant Range</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Focus Areas */}
                {funderDetails.focus_areas?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Focus Areas</h4>
                    <div className="flex flex-wrap gap-2">
                      {funderDetails.focus_areas.map((area: string, i: number) => (
                        <span key={i} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                          {area}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Geographic Focus */}
                {funderDetails.geographic_focus?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Geographic Focus</h4>
                    <div className="flex flex-wrap gap-2">
                      {funderDetails.geographic_focus.map((geo: string, i: number) => (
                        <span key={i} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                          {geo}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Application Info */}
                <div>
                  <h4 className="font-semibold mb-2">Application Process</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${funderDetails.accepts_unsolicited ? 'bg-green-500' : 'bg-red-500'}`} />
                      {funderDetails.accepts_unsolicited ? 'Accepts unsolicited proposals' : 'Invitation only'}
                    </div>
                    {funderDetails.loi_required && (
                      <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-yellow-500" />
                        LOI Required
                      </div>
                    )}
                  </div>
                  {funderDetails.application_process && (
                    <p className="mt-2 text-sm text-gray-600">{funderDetails.application_process}</p>
                  )}
                </div>

                {/* Opportunities */}
                {funderDetails.opportunities?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Active Opportunities</h4>
                    <div className="space-y-2">
                      {funderDetails.opportunities.map((opp: any) => (
                        <div key={opp.id} className="p-3 border rounded-lg">
                          <div className="flex justify-between items-start">
                            <h5 className="font-medium">{opp.opportunity_name}</h5>
                            <span className="text-xs text-gray-500">
                              Due: {new Date(opp.application_deadline).toLocaleDateString()}
                            </span>
                          </div>
                          {opp.funding_amount_max && (
                            <p className="text-sm text-green-600">Up to {formatCurrency(opp.funding_amount_max)}</p>
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
                Select a funder to view details
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Add Funder Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Funder</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Funder Name *</label>
                <Input
                  value={newFunder.name}
                  onChange={(e) => setNewFunder({ ...newFunder, name: e.target.value })}
                  placeholder="Foundation name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={newFunder.funder_type}
                  onChange={(e) => setNewFunder({ ...newFunder, funder_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {typesData?.funder_types?.map((type: any) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Website</label>
                <Input
                  type="url"
                  value={newFunder.website}
                  onChange={(e) => setNewFunder({ ...newFunder, website: e.target.value })}
                  placeholder="https://..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Focus Areas (comma-separated)</label>
                <Input
                  value={newFunder.focus_areas}
                  onChange={(e) => setNewFunder({ ...newFunder, focus_areas: e.target.value })}
                  placeholder="education, health, environment"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Average Grant Size</label>
                <Input
                  type="number"
                  value={newFunder.average_grant_size}
                  onChange={(e) => setNewFunder({ ...newFunder, average_grant_size: e.target.value })}
                  placeholder="50000"
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newFunder)}
                  disabled={!newFunder.name}
                >
                  Add Funder
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
