'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

export default function GoalsObjectivesPage() {
  const queryClient = useQueryClient();
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [showAddGoalModal, setShowAddGoalModal] = useState(false);
  const [showAddObjectiveModal, setShowAddObjectiveModal] = useState(false);

  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    goal_type: 'programmatic',
    target_date: '',
  });

  const [newObjective, setNewObjective] = useState({
    title: '',
    specific_statement: '',
    baseline_value: '',
    target_value: '',
    unit_of_measure: '',
    start_date: '',
    end_date: '',
    responsible_person: '',
  });

  const { data: goalsData, isLoading } = useQuery({
    queryKey: ['goals'],
    queryFn: async () => {
      const response = await api.get('/goals');
      return response.data;
    },
  });

  const { data: goalDetails } = useQuery({
    queryKey: ['goal', selectedGoal],
    queryFn: async () => {
      const response = await api.get(`/goals/${selectedGoal}`);
      return response.data;
    },
    enabled: !!selectedGoal,
  });

  const createGoalMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/goals/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      setShowAddGoalModal(false);
      setNewGoal({ title: '', description: '', goal_type: 'programmatic', target_date: '' });
    },
  });

  const createObjectiveMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/goals/objectives', {
        ...data,
        goal_id: selectedGoal,
        baseline_value: data.baseline_value ? parseFloat(data.baseline_value) : null,
        target_value: data.target_value ? parseFloat(data.target_value) : null,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['goal', selectedGoal] });
      setShowAddObjectiveModal(false);
      setNewObjective({
        title: '',
        specific_statement: '',
        baseline_value: '',
        target_value: '',
        unit_of_measure: '',
        start_date: '',
        end_date: '',
        responsible_person: '',
      });
    },
  });

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      not_started: 'bg-gray-100 text-gray-800',
      in_progress: 'bg-blue-100 text-blue-800',
      on_track: 'bg-green-100 text-green-800',
      at_risk: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-purple-100 text-purple-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">SMART Goals & Objectives</h1>
          <p className="text-gray-600">Define specific, measurable, achievable, relevant, and time-bound objectives</p>
        </div>
        <Button onClick={() => setShowAddGoalModal(true)}>Add Goal</Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Goals List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Goals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-20 bg-gray-200 rounded animate-pulse" />
                  ))}
                </div>
              ) : goalsData?.goals?.length === 0 ? (
                <p className="text-center text-gray-500 py-4">No goals yet</p>
              ) : (
                goalsData?.goals?.map((goal: any) => (
                  <div
                    key={goal.id}
                    onClick={() => setSelectedGoal(goal.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition hover:shadow-md ${
                      selectedGoal === goal.id ? 'border-blue-500 bg-blue-50' : ''
                    }`}
                  >
                    <h4 className="font-medium">{goal.title}</h4>
                    <p className="text-sm text-gray-500 capitalize">{goal.goal_type}</p>
                    <div className="flex justify-between items-center mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${goal.progress_percentage}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 ml-2">{goal.progress_percentage}%</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {goal.objectives_count} objective{goal.objectives_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Goal Details & Objectives */}
        <div className="lg:col-span-2">
          {selectedGoal && goalDetails ? (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{goalDetails.title}</CardTitle>
                    <p className="text-sm text-gray-500 mt-1">{goalDetails.description}</p>
                  </div>
                  <Button size="sm" onClick={() => setShowAddObjectiveModal(true)}>
                    Add Objective
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <h4 className="font-semibold mb-4">SMART Objectives</h4>
                {goalDetails.objectives?.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">No objectives yet. Add your first SMART objective.</p>
                ) : (
                  <div className="space-y-4">
                    {goalDetails.objectives?.map((obj: any) => (
                      <div key={obj.id} className="p-4 border rounded-lg">
                        <div className="flex justify-between items-start">
                          <h5 className="font-medium">{obj.title}</h5>
                          <span className={`px-2 py-1 rounded text-xs ${getStatusColor(obj.status)}`}>
                            {obj.status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-2">{obj.specific_statement}</p>

                        {/* SMART Components */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-sm">
                          {obj.baseline_value !== null && (
                            <div className="p-2 bg-gray-50 rounded">
                              <p className="text-xs text-gray-500">Baseline</p>
                              <p className="font-medium">{obj.baseline_value} {obj.unit_of_measure}</p>
                            </div>
                          )}
                          {obj.target_value !== null && (
                            <div className="p-2 bg-blue-50 rounded">
                              <p className="text-xs text-gray-500">Target</p>
                              <p className="font-medium">{obj.target_value} {obj.unit_of_measure}</p>
                            </div>
                          )}
                          {obj.current_value !== null && (
                            <div className="p-2 bg-green-50 rounded">
                              <p className="text-xs text-gray-500">Current</p>
                              <p className="font-medium">{obj.current_value} {obj.unit_of_measure}</p>
                            </div>
                          )}
                          {obj.end_date && (
                            <div className="p-2 bg-purple-50 rounded">
                              <p className="text-xs text-gray-500">Target Date</p>
                              <p className="font-medium">{new Date(obj.end_date).toLocaleDateString()}</p>
                            </div>
                          )}
                        </div>

                        {/* Progress Bar */}
                        {obj.target_value && obj.current_value !== null && (
                          <div className="mt-4">
                            <div className="flex justify-between text-xs text-gray-500 mb-1">
                              <span>Progress</span>
                              <span>{Math.round((obj.current_value / obj.target_value) * 100)}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${Math.min((obj.current_value / obj.target_value) * 100, 100)}%` }}
                              />
                            </div>
                          </div>
                        )}

                        {/* Indicators */}
                        {obj.indicators?.length > 0 && (
                          <div className="mt-4">
                            <p className="text-xs font-medium text-gray-500 mb-2">Performance Indicators</p>
                            <div className="flex flex-wrap gap-2">
                              {obj.indicators.map((ind: any) => (
                                <span key={ind.id} className="px-2 py-1 bg-gray-100 rounded text-xs">
                                  {ind.indicator_name}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                Select a goal to view and manage its SMART objectives
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Add Goal Modal */}
      {showAddGoalModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add Goal</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Goal Title *</label>
                <Input
                  value={newGoal.title}
                  onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                  placeholder="Enter goal title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newGoal.description}
                  onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="Describe the goal"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Goal Type</label>
                <select
                  value={newGoal.goal_type}
                  onChange={(e) => setNewGoal({ ...newGoal, goal_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="strategic">Strategic</option>
                  <option value="programmatic">Programmatic</option>
                  <option value="operational">Operational</option>
                  <option value="financial">Financial</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Target Date</label>
                <Input
                  type="date"
                  value={newGoal.target_date}
                  onChange={(e) => setNewGoal({ ...newGoal, target_date: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddGoalModal(false)}>Cancel</Button>
                <Button
                  onClick={() => createGoalMutation.mutate(newGoal)}
                  disabled={!newGoal.title}
                >
                  Add Goal
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Add Objective Modal */}
      {showAddObjectiveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Add SMART Objective</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Objective Title *</label>
                <Input
                  value={newObjective.title}
                  onChange={(e) => setNewObjective({ ...newObjective, title: e.target.value })}
                  placeholder="Brief objective title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Specific Statement * <span className="text-gray-400 font-normal">(What exactly will be accomplished?)</span>
                </label>
                <textarea
                  value={newObjective.specific_statement}
                  onChange={(e) => setNewObjective({ ...newObjective, specific_statement: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="By [date], [target population] will [action/change] as measured by [indicator]"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Baseline</label>
                  <Input
                    type="number"
                    value={newObjective.baseline_value}
                    onChange={(e) => setNewObjective({ ...newObjective, baseline_value: e.target.value })}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Target *</label>
                  <Input
                    type="number"
                    value={newObjective.target_value}
                    onChange={(e) => setNewObjective({ ...newObjective, target_value: e.target.value })}
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Unit</label>
                  <Input
                    value={newObjective.unit_of_measure}
                    onChange={(e) => setNewObjective({ ...newObjective, unit_of_measure: e.target.value })}
                    placeholder="people, %, etc."
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Start Date</label>
                  <Input
                    type="date"
                    value={newObjective.start_date}
                    onChange={(e) => setNewObjective({ ...newObjective, start_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">End Date</label>
                  <Input
                    type="date"
                    value={newObjective.end_date}
                    onChange={(e) => setNewObjective({ ...newObjective, end_date: e.target.value })}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Responsible Person</label>
                <Input
                  value={newObjective.responsible_person}
                  onChange={(e) => setNewObjective({ ...newObjective, responsible_person: e.target.value })}
                  placeholder="Name of person responsible"
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddObjectiveModal(false)}>Cancel</Button>
                <Button
                  onClick={() => createObjectiveMutation.mutate(newObjective)}
                  disabled={!newObjective.title || !newObjective.specific_statement}
                >
                  Add Objective
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
