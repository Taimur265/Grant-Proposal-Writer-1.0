'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export default function NeedsAssessmentPage() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState<string | null>(null);

  const [newAssessment, setNewAssessment] = useState({
    title: '',
    assessment_type: 'community',
    description: '',
    geographic_area: '',
    target_population: '',
  });

  const { data: assessmentsData, isLoading } = useQuery({
    queryKey: ['needs-assessments'],
    queryFn: async () => {
      const response = await api.get('/needs-assessments');
      return response.data;
    },
  });

  const { data: assessmentDetails } = useQuery({
    queryKey: ['needs-assessment', selectedAssessment],
    queryFn: async () => {
      const response = await api.get(`/needs-assessments/${selectedAssessment}`);
      return response.data;
    },
    enabled: !!selectedAssessment,
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/needs-assessments/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['needs-assessments'] });
      setShowAddModal(false);
    },
  });

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      high: 'bg-red-100 text-red-800 border-red-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-green-100 text-green-800 border-green-200',
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Needs Assessment</h1>
          <p className="text-gray-600">Document community and organizational needs to support your proposals</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>New Assessment</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Assessments List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Assessments</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-20 bg-gray-200 rounded animate-pulse" />
                  ))}
                </div>
              ) : assessmentsData?.assessments?.length === 0 ? (
                <p className="text-center text-gray-500 py-4">No assessments yet</p>
              ) : (
                assessmentsData?.assessments?.map((assessment: any) => (
                  <div
                    key={assessment.id}
                    onClick={() => setSelectedAssessment(assessment.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition hover:shadow-md ${
                      selectedAssessment === assessment.id ? 'border-blue-500 bg-blue-50' : ''
                    }`}
                  >
                    <h4 className="font-medium">{assessment.title}</h4>
                    <p className="text-sm text-gray-500 capitalize">{assessment.assessment_type}</p>
                    {assessment.geographic_area && (
                      <p className="text-xs text-gray-400 mt-1">{assessment.geographic_area}</p>
                    )}
                    <span className={`inline-block mt-2 px-2 py-0.5 rounded text-xs ${
                      assessment.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {assessment.status}
                    </span>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Assessment Details */}
        <div className="lg:col-span-2">
          {selectedAssessment && assessmentDetails ? (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{assessmentDetails.title}</CardTitle>
                  <p className="text-sm text-gray-500">{assessmentDetails.description}</p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-xs text-gray-500">Type</p>
                      <p className="font-medium capitalize">{assessmentDetails.assessment_type}</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-xs text-gray-500">Geographic Area</p>
                      <p className="font-medium">{assessmentDetails.geographic_area || '-'}</p>
                    </div>
                    <div className="p-3 bg-gray-50 rounded">
                      <p className="text-xs text-gray-500">Target Population</p>
                      <p className="font-medium">{assessmentDetails.target_population || '-'}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Identified Needs */}
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle>Identified Needs</CardTitle>
                    <Button size="sm">Add Need</Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {assessmentDetails.identified_needs?.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No needs identified yet</p>
                  ) : (
                    <div className="space-y-4">
                      {assessmentDetails.identified_needs?.map((need: any) => (
                        <div
                          key={need.id}
                          className={`p-4 border-l-4 rounded-r-lg ${getPriorityColor(need.priority)}`}
                        >
                          <div className="flex justify-between items-start">
                            <h4 className="font-medium">{need.need_statement}</h4>
                            <span className="text-xs font-medium uppercase">{need.priority}</span>
                          </div>
                          {need.category && (
                            <span className="inline-block mt-1 px-2 py-0.5 bg-white rounded text-xs">
                              {need.category}
                            </span>
                          )}
                          {need.affected_population && (
                            <p className="text-sm text-gray-600 mt-2">
                              Affected: {need.affected_population}
                            </p>
                          )}
                          {need.proposed_solution && (
                            <div className="mt-3 p-2 bg-white rounded">
                              <p className="text-xs text-gray-500 mb-1">Proposed Solution</p>
                              <p className="text-sm">{need.proposed_solution}</p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Community Assets */}
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle>Community Assets</CardTitle>
                    <Button size="sm">Add Asset</Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {assessmentDetails.community_assets?.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No assets mapped yet</p>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      {assessmentDetails.community_assets?.map((asset: any) => (
                        <div key={asset.id} className="p-4 border rounded-lg">
                          <h4 className="font-medium">{asset.asset_name}</h4>
                          <p className="text-xs text-gray-500 capitalize">{asset.asset_type}</p>
                          {asset.potential_contribution && (
                            <p className="text-sm text-gray-600 mt-2">{asset.potential_contribution}</p>
                          )}
                          {asset.partnership_interest && (
                            <span className="inline-block mt-2 px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs">
                              Partnership Interest
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                Select an assessment to view details
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Add Assessment Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>New Needs Assessment</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title *</label>
                <Input
                  value={newAssessment.title}
                  onChange={(e) => setNewAssessment({ ...newAssessment, title: e.target.value })}
                  placeholder="Assessment title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={newAssessment.assessment_type}
                  onChange={(e) => setNewAssessment({ ...newAssessment, assessment_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="community">Community</option>
                  <option value="organizational">Organizational</option>
                  <option value="program">Program</option>
                  <option value="capacity">Capacity</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newAssessment.description}
                  onChange={(e) => setNewAssessment({ ...newAssessment, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Geographic Area</label>
                <Input
                  value={newAssessment.geographic_area}
                  onChange={(e) => setNewAssessment({ ...newAssessment, geographic_area: e.target.value })}
                  placeholder="City, county, region"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Target Population</label>
                <Input
                  value={newAssessment.target_population}
                  onChange={(e) => setNewAssessment({ ...newAssessment, target_population: e.target.value })}
                  placeholder="Who is affected?"
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button
                  onClick={() => createMutation.mutate(newAssessment)}
                  disabled={!newAssessment.title}
                >
                  Create Assessment
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
