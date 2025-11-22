'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface LogicModelColumn {
  type: 'inputs' | 'activities' | 'outputs' | 'outcomes' | 'impacts';
  title: string;
  color: string;
  items: any[];
}

export function LogicModelBuilder({ projectId, modelId }: { projectId: string; modelId?: string }) {
  const queryClient = useQueryClient();
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);
  const [newItem, setNewItem] = useState({ title: '', description: '' });
  const [showAddModal, setShowAddModal] = useState(false);

  const { data: modelData, isLoading } = useQuery({
    queryKey: ['logic-model', modelId],
    queryFn: async () => {
      if (!modelId) return null;
      const response = await api.get(`/logic-models/${modelId}`);
      return response.data;
    },
    enabled: !!modelId,
  });

  const { data: templateData } = useQuery({
    queryKey: ['logic-model-template'],
    queryFn: async () => {
      const response = await api.get('/logic-models/template');
      return response.data;
    },
  });

  const addItemMutation = useMutation({
    mutationFn: async ({ type, data }: { type: string; data: any }) => {
      const endpoints: Record<string, string> = {
        inputs: '/logic-models/inputs',
        activities: '/logic-models/activities',
        outputs: '/logic-models/outputs',
        outcomes: '/logic-models/outcomes',
        impacts: '/logic-models/impacts',
      };
      const response = await api.post(endpoints[type], {
        logic_model_id: modelId,
        ...data,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['logic-model', modelId] });
      setShowAddModal(false);
      setNewItem({ title: '', description: '' });
    },
  });

  const columns: LogicModelColumn[] = [
    {
      type: 'inputs',
      title: 'Inputs/Resources',
      color: 'bg-blue-100 border-blue-300',
      items: modelData?.inputs || [],
    },
    {
      type: 'activities',
      title: 'Activities',
      color: 'bg-green-100 border-green-300',
      items: modelData?.activities || [],
    },
    {
      type: 'outputs',
      title: 'Outputs',
      color: 'bg-yellow-100 border-yellow-300',
      items: modelData?.outputs || [],
    },
    {
      type: 'outcomes',
      title: 'Outcomes',
      color: 'bg-orange-100 border-orange-300',
      items: modelData?.outcomes || [],
    },
    {
      type: 'impacts',
      title: 'Impacts',
      color: 'bg-purple-100 border-purple-300',
      items: modelData?.impacts || [],
    },
  ];

  const handleAddItem = () => {
    if (!selectedColumn || !newItem.title) return;

    let data: any = {
      title: newItem.title,
      description: newItem.description,
    };

    if (selectedColumn === 'inputs') {
      data = {
        category: 'other',
        description: newItem.description || newItem.title,
      };
    }

    if (selectedColumn === 'outputs' || selectedColumn === 'outcomes') {
      data.indicator = newItem.title;
    }

    if (selectedColumn === 'outcomes') {
      data.timeframe = 'medium_term';
    }

    addItemMutation.mutate({ type: selectedColumn, data });
  };

  if (!modelId) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-100 flex items-center justify-center">
            <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
            </svg>
          </div>
          <h3 className="font-medium text-gray-900 mb-2">Logic Model Builder</h3>
          <p className="text-sm text-gray-500 mb-4">Create a logic model to visualize your project's theory of change</p>
          <Button>Create Logic Model</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      {modelData && (
        <Card>
          <CardContent className="p-4">
            <h2 className="text-lg font-semibold">{modelData.name}</h2>
            {modelData.theory_of_change && (
              <p className="text-sm text-gray-600 mt-2">{modelData.theory_of_change}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Logic Model Grid */}
      <div className="grid grid-cols-5 gap-4">
        {columns.map((column) => (
          <div key={column.type} className={`rounded-lg border-2 ${column.color} p-4 min-h-[400px]`}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-sm">{column.title}</h3>
              <button
                onClick={() => {
                  setSelectedColumn(column.type);
                  setShowAddModal(true);
                }}
                className="w-6 h-6 rounded-full bg-white border flex items-center justify-center hover:bg-gray-100"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>

            <div className="space-y-2">
              {column.items.map((item: any, index: number) => (
                <div key={item.id || index} className="bg-white p-2 rounded shadow-sm border text-sm">
                  <p className="font-medium">{item.title || item.description}</p>
                  {item.indicator && (
                    <p className="text-xs text-gray-500 mt-1">Indicator: {item.indicator}</p>
                  )}
                  {item.timeframe && (
                    <span className="inline-block mt-1 px-1.5 py-0.5 bg-gray-100 rounded text-xs">
                      {item.timeframe.replace('_', ' ')}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Flow Arrows */}
      <div className="flex justify-center items-center gap-4 text-gray-400 text-sm">
        <span>Inputs</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
        <span>Activities</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
        <span>Outputs</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
        <span>Outcomes</span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
        <span>Impacts</span>
      </div>

      {/* Assumptions */}
      {modelData?.assumptions?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Assumptions</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside text-sm text-gray-600">
              {modelData.assumptions.map((assumption: string, i: number) => (
                <li key={i}>{assumption}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Add Item Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add {selectedColumn?.replace('_', ' ')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Title</label>
                <Input
                  value={newItem.title}
                  onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                  placeholder="Enter title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={newItem.description}
                  onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  placeholder="Enter description"
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="secondary" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button onClick={handleAddItem}>Add</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
