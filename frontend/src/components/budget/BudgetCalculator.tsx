'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

interface LineItem {
  id: string;
  category: string;
  subcategory: string;
  description: string;
  amount: number;
  justification: string;
}

interface BudgetResult {
  by_category: Record<string, { subtotal: number; items: LineItem[] }>;
  total_direct: number;
  indirect_base: number;
  indirect_rate: number;
  indirect_costs: number;
  total: number;
}

const CATEGORIES = [
  { value: 'personnel', label: 'Personnel' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'supplies', label: 'Supplies' },
  { value: 'travel', label: 'Travel' },
  { value: 'contractual', label: 'Contractual/Subawards' },
  { value: 'other', label: 'Other Direct Costs' },
];

export function BudgetCalculator() {
  const [lineItems, setLineItems] = useState<LineItem[]>([]);
  const [indirectRate, setIndirectRate] = useState(0.54);
  const [grantType, setGrantType] = useState('federal');
  const [budgetResult, setBudgetResult] = useState<BudgetResult | null>(null);
  const [narrative, setNarrative] = useState<string>('');

  const [newItem, setNewItem] = useState<Partial<LineItem>>({
    category: 'personnel',
    subcategory: '',
    description: '',
    amount: 0,
    justification: '',
  });

  const calculateMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/budget/calculate', {
        line_items: lineItems.map(({ id, ...item }) => item),
        settings: {
          currency: 'USD',
          indirect_rate: indirectRate,
          indirect_base: 'mtdc',
          exclude_from_indirect: ['equipment'],
        },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setBudgetResult(data);
    },
  });

  const narrativeMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/budget/narrative', {
        line_items: lineItems.map(({ id, ...item }) => item),
        settings: {
          currency: 'USD',
          indirect_rate: indirectRate,
          indirect_base: 'mtdc',
          exclude_from_indirect: ['equipment'],
        },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setNarrative(data.narrative);
      setBudgetResult(data.budget);
    },
  });

  const addLineItem = () => {
    if (!newItem.description || !newItem.amount) return;

    setLineItems([
      ...lineItems,
      {
        id: Date.now().toString(),
        category: newItem.category || 'other',
        subcategory: newItem.subcategory || '',
        description: newItem.description,
        amount: Number(newItem.amount),
        justification: newItem.justification || '',
      },
    ]);

    setNewItem({
      category: 'personnel',
      subcategory: '',
      description: '',
      amount: 0,
      justification: '',
    });
  };

  const removeLineItem = (id: string) => {
    setLineItems(lineItems.filter((item) => item.id !== id));
  };

  const handleGrantTypeChange = (type: string) => {
    setGrantType(type);
    switch (type) {
      case 'federal':
        setIndirectRate(0.54);
        break;
      case 'foundation':
        setIndirectRate(0.15);
        break;
      case 'corporate':
        setIndirectRate(0.10);
        break;
      default:
        setIndirectRate(0);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Budget Calculator</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Grant Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Grant Type
              </label>
              <div className="flex gap-4">
                {['federal', 'foundation', 'corporate', 'custom'].map((type) => (
                  <button
                    key={type}
                    onClick={() => handleGrantTypeChange(type)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium ${
                      grantType === type
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Indirect Rate */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Indirect (F&A) Rate: {(indirectRate * 100).toFixed(1)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={indirectRate * 100}
                onChange={(e) => setIndirectRate(Number(e.target.value) / 100)}
                className="w-full"
              />
            </div>

            {/* Add Line Item Form */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-900 mb-4">Add Budget Item</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Category</label>
                  <select
                    value={newItem.category}
                    onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Description</label>
                  <Input
                    value={newItem.description}
                    onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                    placeholder="Item description"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Amount ($)</label>
                  <Input
                    type="number"
                    value={newItem.amount || ''}
                    onChange={(e) => setNewItem({ ...newItem, amount: Number(e.target.value) })}
                    placeholder="0.00"
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={addLineItem} className="w-full">
                    Add Item
                  </Button>
                </div>
              </div>
              <div className="mt-4">
                <label className="block text-sm text-gray-600 mb-1">Justification (optional)</label>
                <textarea
                  value={newItem.justification}
                  onChange={(e) => setNewItem({ ...newItem, justification: e.target.value })}
                  placeholder="Explain why this cost is necessary..."
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={2}
                />
              </div>
            </div>

            {/* Line Items List */}
            {lineItems.length > 0 && (
              <div>
                <h3 className="font-medium text-gray-900 mb-4">Budget Items</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Category</th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Description</th>
                        <th className="px-4 py-2 text-right text-sm font-medium text-gray-600">Amount</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {lineItems.map((item) => (
                        <tr key={item.id} className="border-b">
                          <td className="px-4 py-3 text-sm capitalize">{item.category}</td>
                          <td className="px-4 py-3 text-sm">{item.description}</td>
                          <td className="px-4 py-3 text-sm text-right">${item.amount.toLocaleString()}</td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => removeLineItem(item.id)}
                              className="text-red-600 hover:text-red-800"
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 flex gap-4">
                  <Button
                    onClick={() => calculateMutation.mutate()}
                    disabled={calculateMutation.isPending}
                  >
                    {calculateMutation.isPending ? 'Calculating...' : 'Calculate Budget'}
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => narrativeMutation.mutate()}
                    disabled={narrativeMutation.isPending}
                  >
                    {narrativeMutation.isPending ? 'Generating...' : 'Generate Narrative'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Budget Result */}
      {budgetResult && (
        <Card>
          <CardHeader>
            <CardTitle>Budget Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(budgetResult.by_category).map(([category, data]) => (
                <div key={category} className="flex justify-between items-center py-2 border-b">
                  <span className="font-medium capitalize">{category}</span>
                  <span>${data.subtotal.toLocaleString()}</span>
                </div>
              ))}
              <div className="flex justify-between items-center py-2 border-b">
                <span className="font-bold">Total Direct Costs</span>
                <span className="font-bold">${budgetResult.total_direct.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b text-gray-600">
                <span>Indirect Base (MTDC)</span>
                <span>${budgetResult.indirect_base.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b text-gray-600">
                <span>Indirect Costs ({(budgetResult.indirect_rate * 100).toFixed(1)}%)</span>
                <span>${budgetResult.indirect_costs.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center py-2 text-lg">
                <span className="font-bold">Total Project Cost</span>
                <span className="font-bold text-blue-600">${budgetResult.total.toLocaleString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Budget Narrative */}
      {narrative && (
        <Card>
          <CardHeader>
            <CardTitle>Budget Narrative</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg">
                {narrative}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
