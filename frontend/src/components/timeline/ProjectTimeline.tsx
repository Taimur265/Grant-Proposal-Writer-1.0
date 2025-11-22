'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface Milestone {
  id: string;
  title: string;
  description: string;
  status: string;
  planned_start: string | null;
  planned_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  progress_percentage: number;
  task_count: number;
  completed_tasks: number;
}

interface Task {
  id: string;
  title: string;
  description: string;
  priority: string;
  is_completed: boolean;
  due_date: string | null;
}

interface TimelineOverview {
  phases: Array<{
    id: string;
    name: string;
    color: string;
    start_date: string | null;
    end_date: string | null;
  }>;
  milestones_count: number;
  overall_progress: number;
  status_summary: Record<string, number>;
  upcoming_deadlines: Array<{
    id: string;
    title: string;
    deadline: string;
    days_remaining: number;
  }>;
}

const STATUS_COLORS: Record<string, string> = {
  not_started: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  delayed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-300 text-gray-600',
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

export function ProjectTimeline({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();
  const [showMilestoneForm, setShowMilestoneForm] = useState(false);
  const [selectedMilestone, setSelectedMilestone] = useState<string | null>(null);
  const [newMilestone, setNewMilestone] = useState({
    title: '',
    description: '',
    planned_start: '',
    planned_end: '',
  });

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['timeline-overview', projectId],
    queryFn: async () => {
      const response = await api.get<TimelineOverview>(`/timeline/overview/${projectId}`);
      return response.data;
    },
  });

  const { data: milestonesData } = useQuery({
    queryKey: ['milestones', projectId],
    queryFn: async () => {
      const response = await api.get<{ milestones: Milestone[] }>(`/timeline/milestones/project/${projectId}`);
      return response.data;
    },
  });

  const { data: milestoneDetail } = useQuery({
    queryKey: ['milestone', selectedMilestone],
    queryFn: async () => {
      const response = await api.get(`/timeline/milestones/${selectedMilestone}`);
      return response.data;
    },
    enabled: !!selectedMilestone,
  });

  const createMilestoneMutation = useMutation({
    mutationFn: async (data: typeof newMilestone) => {
      const response = await api.post('/timeline/milestones', {
        project_id: projectId,
        ...data,
        planned_start: data.planned_start || null,
        planned_end: data.planned_end || null,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones', projectId] });
      queryClient.invalidateQueries({ queryKey: ['timeline-overview', projectId] });
      setShowMilestoneForm(false);
      setNewMilestone({ title: '', description: '', planned_start: '', planned_end: '' });
    },
  });

  const updateTaskMutation = useMutation({
    mutationFn: async ({ taskId, is_completed }: { taskId: string; is_completed: boolean }) => {
      const response = await api.patch(`/timeline/tasks/${taskId}`, { is_completed });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestone', selectedMilestone] });
      queryClient.invalidateQueries({ queryKey: ['milestones', projectId] });
      queryClient.invalidateQueries({ queryKey: ['timeline-overview', projectId] });
    },
  });

  if (overviewLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-32 bg-gray-200 rounded-lg" />
        <div className="h-64 bg-gray-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Timeline Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{overview?.overall_progress.toFixed(0)}%</p>
              <p className="text-sm text-gray-500">Overall Progress</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">{overview?.milestones_count}</p>
              <p className="text-sm text-gray-500">Milestones</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{overview?.status_summary.completed || 0}</p>
              <p className="text-sm text-gray-500">Completed</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-orange-600">{overview?.upcoming_deadlines.length}</p>
              <p className="text-sm text-gray-500">Upcoming Deadlines</p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progress</span>
              <span>{overview?.overall_progress.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${overview?.overall_progress || 0}%` }}
              />
            </div>
          </div>

          {/* Status summary */}
          <div className="mt-6 flex flex-wrap gap-4">
            {Object.entries(overview?.status_summary || {}).map(([status, count]) => (
              <div key={status} className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[status]}`}>
                  {status.replace('_', ' ')}
                </span>
                <span className="text-sm text-gray-600">{count}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Milestones */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Milestones</CardTitle>
          <Button onClick={() => setShowMilestoneForm(true)}>Add Milestone</Button>
        </CardHeader>
        <CardContent>
          {showMilestoneForm && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-4">New Milestone</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  placeholder="Milestone title"
                  value={newMilestone.title}
                  onChange={(e) => setNewMilestone({ ...newMilestone, title: e.target.value })}
                />
                <Input
                  type="date"
                  placeholder="Planned end"
                  value={newMilestone.planned_end}
                  onChange={(e) => setNewMilestone({ ...newMilestone, planned_end: e.target.value })}
                />
              </div>
              <textarea
                placeholder="Description"
                className="w-full mt-4 px-3 py-2 border rounded-lg"
                value={newMilestone.description}
                onChange={(e) => setNewMilestone({ ...newMilestone, description: e.target.value })}
                rows={2}
              />
              <div className="mt-4 flex gap-2">
                <Button onClick={() => createMilestoneMutation.mutate(newMilestone)}>
                  Create Milestone
                </Button>
                <Button variant="secondary" onClick={() => setShowMilestoneForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Milestone list */}
          <div className="space-y-4">
            {milestonesData?.milestones.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No milestones yet. Create your first milestone to track progress.</p>
            ) : (
              milestonesData?.milestones.map((milestone) => (
                <div
                  key={milestone.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedMilestone === milestone.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedMilestone(selectedMilestone === milestone.id ? null : milestone.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h4 className="font-medium text-gray-900">{milestone.title}</h4>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[milestone.status]}`}>
                          {milestone.status.replace('_', ' ')}
                        </span>
                      </div>
                      {milestone.description && (
                        <p className="text-sm text-gray-500 mt-1">{milestone.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        {milestone.planned_end && (
                          <span>Due: {new Date(milestone.planned_end).toLocaleDateString()}</span>
                        )}
                        <span>{milestone.completed_tasks}/{milestone.task_count} tasks</span>
                      </div>
                    </div>
                    <div className="w-24">
                      <div className="text-right text-sm font-medium text-gray-700 mb-1">
                        {milestone.progress_percentage.toFixed(0)}%
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${milestone.progress_percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Task list */}
                  {selectedMilestone === milestone.id && milestoneDetail?.tasks && (
                    <div className="mt-4 pt-4 border-t">
                      <h5 className="text-sm font-medium text-gray-700 mb-3">Tasks</h5>
                      <div className="space-y-2">
                        {milestoneDetail.tasks.length === 0 ? (
                          <p className="text-sm text-gray-500">No tasks yet</p>
                        ) : (
                          milestoneDetail.tasks.map((task: Task) => (
                            <div key={task.id} className="flex items-center gap-3 p-2 bg-white rounded border">
                              <input
                                type="checkbox"
                                checked={task.is_completed}
                                onChange={(e) => {
                                  e.stopPropagation();
                                  updateTaskMutation.mutate({
                                    taskId: task.id,
                                    is_completed: !task.is_completed,
                                  });
                                }}
                                className="h-4 w-4 text-blue-600 rounded"
                              />
                              <span className={`flex-1 ${task.is_completed ? 'line-through text-gray-400' : 'text-gray-700'}`}>
                                {task.title}
                              </span>
                              <span className={`px-2 py-0.5 rounded text-xs ${PRIORITY_COLORS[task.priority]}`}>
                                {task.priority}
                              </span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Deadlines */}
      {overview?.upcoming_deadlines && overview.upcoming_deadlines.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Deadlines</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {overview.upcoming_deadlines.map((deadline) => (
                <div key={deadline.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{deadline.title}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(deadline.deadline).toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    deadline.days_remaining <= 3
                      ? 'bg-red-100 text-red-700'
                      : deadline.days_remaining <= 7
                      ? 'bg-orange-100 text-orange-700'
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {deadline.days_remaining} days
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
