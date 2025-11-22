'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface Funder {
  id: string;
  name: string;
  short_name: string;
  type: string;
  description: string;
  website: string;
  focus_areas: string[];
  typical_award_min: number;
  typical_award_max: number;
  max_indirect_rate: number;
}

interface Opportunity {
  id: string;
  funder_id: string;
  title: string;
  description: string;
  status: string;
  award_floor: number;
  award_ceiling: number;
  close_date: string;
  days_until_close: number;
  focus_areas: string[];
  is_bookmarked: boolean;
  match_score: number;
}

const FUNDER_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'federal', label: 'Federal' },
  { value: 'foundation', label: 'Foundation' },
  { value: 'corporate', label: 'Corporate' },
  { value: 'state', label: 'State' },
  { value: 'international', label: 'International' },
];

export function FunderSearch() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'funders' | 'opportunities'>('opportunities');
  const [searchQuery, setSearchQuery] = useState('');
  const [funderType, setFunderType] = useState('');
  const [closingWithinDays, setClosingWithinDays] = useState<number | null>(30);

  const { data: fundersData, isLoading: fundersLoading } = useQuery({
    queryKey: ['funders', searchQuery, funderType],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (funderType) params.append('funder_type', funderType);
      const response = await api.get(`/funders?${params.toString()}`);
      return response.data;
    },
    enabled: activeTab === 'funders',
  });

  const { data: opportunitiesData, isLoading: opportunitiesLoading } = useQuery({
    queryKey: ['opportunities', searchQuery, closingWithinDays],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (closingWithinDays) params.append('closing_within_days', closingWithinDays.toString());
      const response = await api.get(`/funders/opportunities/search?${params.toString()}`);
      return response.data;
    },
    enabled: activeTab === 'opportunities',
  });

  const bookmarkMutation = useMutation({
    mutationFn: async (opportunityId: string) => {
      const response = await api.post(`/funders/opportunities/${opportunityId}/bookmark`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
    },
  });

  const formatCurrency = (amount: number | null) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex gap-4 border-b">
        <button
          onClick={() => setActiveTab('opportunities')}
          className={`pb-3 px-1 border-b-2 transition-colors ${
            activeTab === 'opportunities'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Grant Opportunities
        </button>
        <button
          onClick={() => setActiveTab('funders')}
          className={`pb-3 px-1 border-b-2 transition-colors ${
            activeTab === 'funders'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Funders Database
        </button>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <Input
            placeholder={activeTab === 'funders' ? 'Search funders...' : 'Search opportunities...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        {activeTab === 'funders' && (
          <select
            value={funderType}
            onChange={(e) => setFunderType(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            {FUNDER_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        )}
        {activeTab === 'opportunities' && (
          <select
            value={closingWithinDays || ''}
            onChange={(e) => setClosingWithinDays(e.target.value ? Number(e.target.value) : null)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="">All Deadlines</option>
            <option value="7">Closing in 7 days</option>
            <option value="30">Closing in 30 days</option>
            <option value="60">Closing in 60 days</option>
            <option value="90">Closing in 90 days</option>
          </select>
        )}
      </div>

      {/* Results */}
      {activeTab === 'opportunities' && (
        <div className="space-y-4">
          {opportunitiesLoading ? (
            <div className="animate-pulse space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg" />
              ))}
            </div>
          ) : opportunitiesData?.opportunities?.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-gray-500">
                No opportunities found matching your criteria
              </CardContent>
            </Card>
          ) : (
            opportunitiesData?.opportunities?.map((opp: Opportunity) => (
              <Card key={opp.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-lg text-gray-900">{opp.title}</h3>
                        {opp.days_until_close !== null && (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            opp.days_until_close <= 7
                              ? 'bg-red-100 text-red-700'
                              : opp.days_until_close <= 14
                              ? 'bg-orange-100 text-orange-700'
                              : 'bg-green-100 text-green-700'
                          }`}>
                            {opp.days_until_close} days left
                          </span>
                        )}
                      </div>
                      {opp.description && (
                        <p className="text-gray-600 text-sm mb-3">{opp.description}</p>
                      )}
                      <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                        <span>
                          Award: {formatCurrency(opp.award_floor)} - {formatCurrency(opp.award_ceiling)}
                        </span>
                        {opp.close_date && (
                          <span>
                            Deadline: {new Date(opp.close_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      {opp.focus_areas?.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {opp.focus_areas.slice(0, 4).map((area, i) => (
                            <span key={i} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                              {area}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <button
                        onClick={() => bookmarkMutation.mutate(opp.id)}
                        className={`p-2 rounded-full ${
                          opp.is_bookmarked
                            ? 'text-yellow-500 bg-yellow-50'
                            : 'text-gray-400 hover:text-yellow-500 hover:bg-yellow-50'
                        }`}
                      >
                        <svg className="w-5 h-5" fill={opp.is_bookmarked ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                        </svg>
                      </button>
                      <Button size="sm">View Details</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === 'funders' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {fundersLoading ? (
            [...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 rounded-lg animate-pulse" />
            ))
          ) : fundersData?.funders?.length === 0 ? (
            <Card className="col-span-full">
              <CardContent className="py-8 text-center text-gray-500">
                No funders found matching your criteria
              </CardContent>
            </Card>
          ) : (
            fundersData?.funders?.map((funder: Funder) => (
              <Card key={funder.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <h3 className="font-semibold text-gray-900 mb-1">{funder.name}</h3>
                  <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs mb-2 capitalize">
                    {funder.type}
                  </span>
                  {funder.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">{funder.description}</p>
                  )}
                  <div className="text-sm text-gray-500 space-y-1">
                    {(funder.typical_award_min || funder.typical_award_max) && (
                      <p>
                        Typical Award: {formatCurrency(funder.typical_award_min)} - {formatCurrency(funder.typical_award_max)}
                      </p>
                    )}
                    {funder.max_indirect_rate && (
                      <p>Max Indirect: {(funder.max_indirect_rate * 100).toFixed(0)}%</p>
                    )}
                  </div>
                  {funder.focus_areas?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {funder.focus_areas.slice(0, 3).map((area, i) => (
                        <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">
                          {area}
                        </span>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
}
