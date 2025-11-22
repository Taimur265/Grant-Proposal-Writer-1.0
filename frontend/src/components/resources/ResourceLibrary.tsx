'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface Resource {
  id: string;
  title: string;
  description?: string;
  resource_type: string;
  category: string;
  file_path?: string;
  external_url?: string;
  tags: string[];
  is_template: boolean;
  download_count: number;
  created_at: string;
}

interface Checklist {
  id: string;
  name: string;
  description?: string;
  checklist_type: string;
  items: ChecklistItem[];
}

interface ChecklistItem {
  id: string;
  text: string;
  required: boolean;
  order_index: number;
}

export function ResourceLibrary() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'resources' | 'checklists' | 'history'>('resources');
  const [showAddModal, setShowAddModal] = useState(false);
  const [filterCategory, setFilterCategory] = useState('');
  const [filterType, setFilterType] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const [newResource, setNewResource] = useState({
    title: '',
    description: '',
    resource_type: 'document',
    category: 'templates',
    external_url: '',
    is_template: false,
    tags: '',
  });

  const { data: resourcesData, isLoading: resourcesLoading } = useQuery({
    queryKey: ['resources', filterCategory, filterType, searchQuery],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filterCategory) params.append('category', filterCategory);
      if (filterType) params.append('resource_type', filterType);
      if (searchQuery) params.append('search', searchQuery);
      const response = await api.get(`/resources?${params.toString()}`);
      return response.data;
    },
    enabled: activeTab === 'resources',
  });

  const { data: typesData } = useQuery({
    queryKey: ['resource-types'],
    queryFn: async () => {
      const response = await api.get('/resources/types');
      return response.data;
    },
  });

  const { data: checklistsData, isLoading: checklistsLoading } = useQuery({
    queryKey: ['checklists'],
    queryFn: async () => {
      const response = await api.get('/resources/checklists');
      return response.data;
    },
    enabled: activeTab === 'checklists',
  });

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['funding-history'],
    queryFn: async () => {
      const response = await api.get('/resources/funding-history');
      return response.data;
    },
    enabled: activeTab === 'history',
  });

  const createResourceMutation = useMutation({
    mutationFn: async (data: typeof newResource) => {
      const response = await api.post('/resources/', {
        ...data,
        tags: data.tags.split(',').map(t => t.trim()).filter(Boolean),
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources'] });
      setShowAddModal(false);
      setNewResource({
        title: '',
        description: '',
        resource_type: 'document',
        category: 'templates',
        external_url: '',
        is_template: false,
        tags: '',
      });
    },
  });

  const trackUsageMutation = useMutation({
    mutationFn: async (resourceId: string) => {
      await api.post(`/resources/${resourceId}/track-usage`);
    },
  });

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      document: '📄',
      template: '📋',
      guide: '📚',
      video: '🎬',
      link: '🔗',
      spreadsheet: '📊',
      presentation: '📽️',
      image: '🖼️',
    };
    return icons[type] || '📄';
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      templates: 'bg-blue-100 text-blue-800',
      guides: 'bg-green-100 text-green-800',
      samples: 'bg-purple-100 text-purple-800',
      regulations: 'bg-red-100 text-red-800',
      training: 'bg-yellow-100 text-yellow-800',
      tools: 'bg-indigo-100 text-indigo-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Resource Library</h2>
        <Button onClick={() => setShowAddModal(true)}>Add Resource</Button>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { key: 'resources', label: 'Resources', icon: '📚' },
            { key: 'checklists', label: 'Checklists', icon: '✅' },
            { key: 'history', label: 'Funding History', icon: '💰' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`px-4 py-2 border-b-2 font-medium text-sm transition ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="mr-1">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'resources' && (
        <>
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search resources..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="px-3 py-2 border rounded-lg"
                >
                  <option value="">All Categories</option>
                  {typesData?.categories?.map((cat: any) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
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

          {/* Resources Grid */}
          {resourcesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-40 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : resourcesData?.resources?.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                No resources found. Add your first resource to get started.
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {resourcesData?.resources?.map((resource: Resource) => (
                <Card key={resource.id} className="hover:shadow-lg transition">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <span className="text-3xl">{getTypeIcon(resource.resource_type)}</span>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium truncate">{resource.title}</h3>
                        {resource.description && (
                          <p className="text-sm text-gray-500 line-clamp-2 mt-1">
                            {resource.description}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-1 mt-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${getCategoryColor(resource.category)}`}>
                            {resource.category}
                          </span>
                          {resource.is_template && (
                            <span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded text-xs">
                              Template
                            </span>
                          )}
                        </div>
                        {resource.tags?.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {resource.tags.slice(0, 3).map((tag, i) => (
                              <span key={i} className="px-1.5 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        <div className="flex justify-between items-center mt-3 pt-2 border-t">
                          <span className="text-xs text-gray-400">
                            {resource.download_count} downloads
                          </span>
                          {resource.external_url && (
                            <a
                              href={resource.external_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              onClick={() => trackUsageMutation.mutate(resource.id)}
                              className="text-blue-500 hover:text-blue-700 text-sm"
                            >
                              Open →
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === 'checklists' && (
        <div className="space-y-4">
          {checklistsLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : checklistsData?.checklists?.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                No checklists available.
              </CardContent>
            </Card>
          ) : (
            checklistsData?.checklists?.map((checklist: Checklist) => (
              <Card key={checklist.id}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span>✅</span>
                    {checklist.name}
                  </CardTitle>
                  {checklist.description && (
                    <p className="text-sm text-gray-500">{checklist.description}</p>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {checklist.items?.map((item, index) => (
                      <div key={item.id} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                        <span className="text-gray-400 text-sm">{index + 1}.</span>
                        <span className="flex-1">{item.text}</span>
                        {item.required && (
                          <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">
                            Required
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t">
                    <Button size="sm">Start Checklist</Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          {historyLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 bg-gray-200 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : historyData?.funding_history?.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                No funding history recorded yet.
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-green-600">
                      ${(historyData?.summary?.total_awarded || 0).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">Total Awarded</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {historyData?.summary?.total_applications || 0}
                    </p>
                    <p className="text-sm text-gray-500">Applications</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-purple-600">
                      {historyData?.summary?.success_rate || 0}%
                    </p>
                    <p className="text-sm text-gray-500">Success Rate</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4 text-center">
                    <p className="text-2xl font-bold text-orange-600">
                      {historyData?.summary?.unique_funders || 0}
                    </p>
                    <p className="text-sm text-gray-500">Unique Funders</p>
                  </CardContent>
                </Card>
              </div>

              {/* History List */}
              <Card>
                <CardHeader>
                  <CardTitle>Funding History</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b text-left">
                          <th className="pb-2 font-medium">Funder</th>
                          <th className="pb-2 font-medium">Grant Name</th>
                          <th className="pb-2 font-medium">Amount</th>
                          <th className="pb-2 font-medium">Status</th>
                          <th className="pb-2 font-medium">Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historyData?.funding_history?.map((record: any) => (
                          <tr key={record.id} className="border-b">
                            <td className="py-3">{record.funder_name}</td>
                            <td className="py-3">{record.grant_name}</td>
                            <td className="py-3">
                              {record.amount_awarded
                                ? `$${record.amount_awarded.toLocaleString()}`
                                : `$${record.amount_requested?.toLocaleString() || '-'}`}
                            </td>
                            <td className="py-3">
                              <span
                                className={`px-2 py-1 rounded text-xs ${
                                  record.outcome === 'awarded'
                                    ? 'bg-green-100 text-green-800'
                                    : record.outcome === 'rejected'
                                    ? 'bg-red-100 text-red-800'
                                    : record.outcome === 'pending'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {record.outcome}
                              </span>
                            </td>
                            <td className="py-3 text-gray-500 text-sm">
                              {new Date(record.application_date).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

      {/* Add Resource Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-lg">
            <CardHeader>
              <CardTitle>Add Resource</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title *</label>
                <Input
                  value={newResource.title}
                  onChange={(e) => setNewResource({ ...newResource, title: e.target.value })}
                  placeholder="Resource title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newResource.description}
                  onChange={(e) => setNewResource({ ...newResource, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={2}
                  placeholder="Brief description"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Type</label>
                  <select
                    value={newResource.resource_type}
                    onChange={(e) => setNewResource({ ...newResource, resource_type: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {typesData?.types?.map((type: any) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Category</label>
                  <select
                    value={newResource.category}
                    onChange={(e) => setNewResource({ ...newResource, category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {typesData?.categories?.map((cat: any) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">External URL</label>
                <Input
                  type="url"
                  value={newResource.external_url}
                  onChange={(e) => setNewResource({ ...newResource, external_url: e.target.value })}
                  placeholder="https://..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Tags (comma-separated)</label>
                <Input
                  value={newResource.tags}
                  onChange={(e) => setNewResource({ ...newResource, tags: e.target.value })}
                  placeholder="tag1, tag2, tag3"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="isTemplate"
                  checked={newResource.is_template}
                  onChange={(e) => setNewResource({ ...newResource, is_template: e.target.checked })}
                  className="rounded"
                />
                <label htmlFor="isTemplate" className="text-sm">
                  This is a reusable template
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => createResourceMutation.mutate(newResource)}
                  disabled={!newResource.title || createResourceMutation.isPending}
                >
                  {createResourceMutation.isPending ? 'Adding...' : 'Add Resource'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
