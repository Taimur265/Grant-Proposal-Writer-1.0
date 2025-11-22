'use client';

import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface DashboardStats {
  projects: {
    total: number;
    by_status: Record<string, number>;
    this_month: number;
  };
  documents: {
    total: number;
    by_category: Record<string, number>;
    by_status: Record<string, number>;
    total_size_mb: number;
  };
  proposals: {
    total: number;
    by_status: Record<string, number>;
    avg_compliance_score: number | null;
    total_words: number;
  };
  recent_activity: Array<{
    type: string;
    title: string;
    project_id: string;
    timestamp: string;
  }>;
  upcoming_deadlines: Array<{
    project_id: string;
    project_name: string;
    deadline: string;
    days_remaining: number;
    status: string;
  }>;
}

function StatCard({ title, value, subtitle, icon }: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className="text-blue-500">{icon}</div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-800',
    active: 'bg-green-100 text-green-800',
    in_progress: 'bg-blue-100 text-blue-800',
    completed: 'bg-purple-100 text-purple-800',
    submitted: 'bg-indigo-100 text-indigo-800',
    approved: 'bg-emerald-100 text-emerald-800',
    rejected: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

export function AnalyticsDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get<DashboardStats>('/analytics/dashboard');
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-32 rounded-lg" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-64 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Failed to load dashboard statistics</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Projects"
          value={data.projects.total}
          subtitle={`${data.projects.this_month} this month`}
        />
        <StatCard
          title="Documents"
          value={data.documents.total}
          subtitle={`${data.documents.total_size_mb} MB total`}
        />
        <StatCard
          title="Proposals"
          value={data.proposals.total}
          subtitle={`${data.proposals.total_words.toLocaleString()} words`}
        />
        <StatCard
          title="Avg. Compliance"
          value={data.proposals.avg_compliance_score ? `${data.proposals.avg_compliance_score}%` : 'N/A'}
          subtitle="Score"
        />
      </div>

      {/* Project Status Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Projects by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(data.projects.by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <StatusBadge status={status} />
                    <span className="text-gray-700 capitalize">{status.replace('_', ' ')}</span>
                  </div>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Documents by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(data.documents.by_category).map(([category, count]) => (
                <div key={category} className="flex items-center justify-between">
                  <span className="text-gray-700 capitalize">{category.replace('_', ' ')}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${(count / data.documents.total) * 100}%` }}
                      />
                    </div>
                    <span className="font-semibold w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity and Deadlines */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.recent_activity.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No recent activity</p>
              ) : (
                data.recent_activity.slice(0, 5).map((activity, index) => (
                  <div key={index} className="flex items-start gap-3 pb-3 border-b last:border-0">
                    <div className={`w-2 h-2 mt-2 rounded-full ${
                      activity.type === 'document_uploaded' ? 'bg-green-500' : 'bg-blue-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(activity.timestamp).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Upcoming Deadlines</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.upcoming_deadlines.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No upcoming deadlines</p>
              ) : (
                data.upcoming_deadlines.slice(0, 5).map((deadline) => (
                  <div key={deadline.project_id} className="flex items-center justify-between pb-3 border-b last:border-0">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{deadline.project_name}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(deadline.deadline).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      deadline.days_remaining <= 7
                        ? 'bg-red-100 text-red-800'
                        : deadline.days_remaining <= 14
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {deadline.days_remaining} days
                    </span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
