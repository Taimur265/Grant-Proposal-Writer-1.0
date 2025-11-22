'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface Risk {
  id: string;
  title: string;
  category: string;
  likelihood: string;
  impact: string;
  risk_score: number;
  status: string;
  owner_name?: string;
}

const LIKELIHOOD_LEVELS = ['rare', 'unlikely', 'possible', 'likely', 'almost_certain'];
const IMPACT_LEVELS = ['insignificant', 'minor', 'moderate', 'major', 'catastrophic'];

export function RiskMatrix({ projectId }: { projectId?: string }) {
  const queryClient = useQueryClient();
  const [showAddRisk, setShowAddRisk] = useState(false);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);
  const [newRisk, setNewRisk] = useState({
    title: '',
    description: '',
    category: 'operational',
    likelihood: 'possible',
    impact: 'moderate',
    owner_name: '',
  });

  const { data: matrixData, isLoading: matrixLoading } = useQuery({
    queryKey: ['risk-matrix', projectId],
    queryFn: async () => {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/risks/matrix${params}`);
      return response.data;
    },
  });

  const { data: summaryData } = useQuery({
    queryKey: ['risk-summary', projectId],
    queryFn: async () => {
      const params = projectId ? `?project_id=${projectId}` : '';
      const response = await api.get(`/risks/summary${params}`);
      return response.data;
    },
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['risk-categories'],
    queryFn: async () => {
      const response = await api.get('/risks/categories');
      return response.data;
    },
  });

  const createRiskMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/risks', {
        ...data,
        project_id: projectId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['risk-matrix'] });
      queryClient.invalidateQueries({ queryKey: ['risk-summary'] });
      setShowAddRisk(false);
      setNewRisk({
        title: '',
        description: '',
        category: 'operational',
        likelihood: 'possible',
        impact: 'moderate',
        owner_name: '',
      });
    },
  });

  const getCellColor = (likelihood: string, impact: string) => {
    const l = LIKELIHOOD_LEVELS.indexOf(likelihood) + 1;
    const i = IMPACT_LEVELS.indexOf(impact) + 1;
    const score = l * i;

    if (score >= 15) return 'bg-red-200 hover:bg-red-300';
    if (score >= 10) return 'bg-orange-200 hover:bg-orange-300';
    if (score >= 5) return 'bg-yellow-200 hover:bg-yellow-300';
    return 'bg-green-200 hover:bg-green-300';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 15) return 'bg-red-600 text-white';
    if (score >= 10) return 'bg-orange-500 text-white';
    if (score >= 5) return 'bg-yellow-500 text-white';
    return 'bg-green-500 text-white';
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summaryData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{summaryData.total_risks}</p>
              <p className="text-sm text-gray-500">Total Risks</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-red-600">{summaryData.high_risk_count}</p>
              <p className="text-sm text-gray-500">High Risks</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-3xl font-bold text-purple-600">{summaryData.avg_risk_score.toFixed(1)}</p>
              <p className="text-sm text-gray-500">Avg Score</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <Button className="w-full" onClick={() => setShowAddRisk(true)}>Add Risk</Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Risk Matrix */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Matrix</CardTitle>
        </CardHeader>
        <CardContent>
          {matrixLoading ? (
            <div className="animate-pulse h-64 bg-gray-200 rounded" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className="p-2 border bg-gray-100"></th>
                    {IMPACT_LEVELS.map(impact => (
                      <th key={impact} className="p-2 border bg-gray-100 text-xs capitalize">
                        {impact.replace('_', ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[...LIKELIHOOD_LEVELS].reverse().map(likelihood => (
                    <tr key={likelihood}>
                      <td className="p-2 border bg-gray-100 text-xs capitalize font-medium">
                        {likelihood.replace('_', ' ')}
                      </td>
                      {IMPACT_LEVELS.map(impact => {
                        const key = `${likelihood}_${impact}`;
                        const risks = matrixData?.matrix?.[key] || [];
                        return (
                          <td
                            key={key}
                            className={`p-2 border min-w-[100px] h-20 align-top ${getCellColor(likelihood, impact)}`}
                          >
                            {risks.length > 0 && (
                              <div className="space-y-1">
                                {risks.map((risk: any) => (
                                  <div
                                    key={risk.id}
                                    className="text-xs p-1 bg-white rounded cursor-pointer hover:shadow"
                                    onClick={() => setSelectedRisk(risk)}
                                  >
                                    <span className={`px-1 rounded ${getScoreBadge(risk.score)}`}>
                                      {risk.score}
                                    </span>
                                    <span className="ml-1 truncate">{risk.title}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Legend */}
          <div className="mt-4 flex gap-4 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-green-200 rounded"></span> Low (1-4)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-yellow-200 rounded"></span> Medium (5-9)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-orange-200 rounded"></span> High (10-14)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-red-200 rounded"></span> Critical (15-25)
            </span>
          </div>
        </CardContent>
      </Card>

      {/* High Risks List */}
      {summaryData?.high_risks?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>High Priority Risks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {summaryData.high_risks.map((risk: any) => (
                <div key={risk.id} className="flex justify-between items-center p-3 bg-red-50 rounded border border-red-200">
                  <div>
                    <p className="font-medium">{risk.title}</p>
                    <p className="text-sm text-gray-500">{risk.category}</p>
                  </div>
                  <span className={`px-2 py-1 rounded font-bold ${getScoreBadge(risk.score)}`}>
                    {risk.score}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Risk Modal */}
      {showAddRisk && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg">
            <CardHeader>
              <CardTitle>Add Risk</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <Input
                  value={newRisk.title}
                  onChange={(e) => setNewRisk({ ...newRisk, title: e.target.value })}
                  placeholder="Risk title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newRisk.description}
                  onChange={(e) => setNewRisk({ ...newRisk, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="Describe the risk"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Category</label>
                  <select
                    value={newRisk.category}
                    onChange={(e) => setNewRisk({ ...newRisk, category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {categoriesData?.categories?.map((cat: any) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Owner</label>
                  <Input
                    value={newRisk.owner_name}
                    onChange={(e) => setNewRisk({ ...newRisk, owner_name: e.target.value })}
                    placeholder="Risk owner"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Likelihood</label>
                  <select
                    value={newRisk.likelihood}
                    onChange={(e) => setNewRisk({ ...newRisk, likelihood: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {categoriesData?.likelihood_levels?.map((l: any) => (
                      <option key={l.value} value={l.value}>{l.label} ({l.score})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Impact</label>
                  <select
                    value={newRisk.impact}
                    onChange={(e) => setNewRisk({ ...newRisk, impact: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {categoriesData?.impact_levels?.map((i: any) => (
                      <option key={i.value} value={i.value}>{i.label} ({i.score})</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowAddRisk(false)}>Cancel</Button>
                <Button onClick={() => createRiskMutation.mutate(newRisk)}>Add Risk</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
