'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';

interface LetterTemplate {
  type: string;
  name: string;
  description: string;
  required_fields: string[];
}

interface TemplateField {
  name: string;
  label: string;
  required: boolean;
  type?: string;
}

export function LetterGenerator() {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [generatedLetter, setGeneratedLetter] = useState<string | null>(null);

  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['letter-templates'],
    queryFn: async () => {
      const response = await api.get('/letters/templates');
      return response.data;
    },
  });

  const { data: typesData } = useQuery({
    queryKey: ['letter-types'],
    queryFn: async () => {
      const response = await api.get('/letters/types');
      return response.data;
    },
  });

  const { data: templateDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['letter-template', selectedTemplate],
    queryFn: async () => {
      const response = await api.get(`/letters/templates/${selectedTemplate}`);
      return response.data;
    },
    enabled: !!selectedTemplate,
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/letters/generate', {
        template_type: selectedTemplate,
        data: formData,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setGeneratedLetter(data.content);
    },
  });

  const handleFieldChange = (fieldName: string, value: string) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
  };

  const handleCopyToClipboard = () => {
    if (generatedLetter) {
      navigator.clipboard.writeText(generatedLetter);
    }
  };

  const handleDownload = () => {
    if (generatedLetter) {
      const blob = new Blob([generatedLetter], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `letter-${selectedTemplate}-${new Date().toISOString().split('T')[0]}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Letter Generator</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Template Selection */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Choose Template</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {templatesLoading ? (
                <div className="animate-pulse space-y-2">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="h-20 bg-gray-200 rounded" />
                  ))}
                </div>
              ) : (
                typesData?.categories?.map((category: any) => (
                  <div key={category.name} className="space-y-2">
                    <h4 className="font-medium text-sm text-gray-500">{category.name}</h4>
                    {category.types.map((type: any) => (
                      <button
                        key={type.type}
                        onClick={() => {
                          setSelectedTemplate(type.type);
                          setFormData({});
                          setGeneratedLetter(null);
                        }}
                        className={`w-full p-3 rounded-lg text-left transition ${
                          selectedTemplate === type.type
                            ? 'bg-blue-50 border-2 border-blue-500'
                            : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                        }`}
                      >
                        <p className="font-medium text-sm">{type.name}</p>
                      </button>
                    ))}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Form */}
        <div className="lg:col-span-2">
          {selectedTemplate && templateDetails ? (
            <Card>
              <CardHeader>
                <CardTitle>{templateDetails.name}</CardTitle>
                <p className="text-sm text-gray-500">{templateDetails.description}</p>
              </CardHeader>
              <CardContent className="space-y-4">
                {detailsLoading ? (
                  <div className="animate-pulse space-y-4">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="h-12 bg-gray-200 rounded" />
                    ))}
                  </div>
                ) : (
                  <>
                    {templateDetails.fields?.map((field: TemplateField) => (
                      <div key={field.name}>
                        <label className="block text-sm font-medium mb-1">
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </label>
                        {field.type === 'textarea' ? (
                          <textarea
                            value={formData[field.name] || ''}
                            onChange={(e) => handleFieldChange(field.name, e.target.value)}
                            className="w-full px-3 py-2 border rounded-lg"
                            rows={3}
                            placeholder={`Enter ${field.label.toLowerCase()}`}
                          />
                        ) : (
                          <Input
                            value={formData[field.name] || ''}
                            onChange={(e) => handleFieldChange(field.name, e.target.value)}
                            placeholder={`Enter ${field.label.toLowerCase()}`}
                          />
                        )}
                      </div>
                    ))}

                    <div className="flex justify-end gap-2 pt-4">
                      <Button
                        variant="secondary"
                        onClick={() => {
                          setFormData({});
                          setGeneratedLetter(null);
                        }}
                      >
                        Clear
                      </Button>
                      <Button
                        onClick={() => generateMutation.mutate()}
                        disabled={generateMutation.isPending}
                      >
                        {generateMutation.isPending ? 'Generating...' : 'Generate Letter'}
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-gray-500">
                Select a template to get started
              </CardContent>
            </Card>
          )}

          {/* Generated Letter Preview */}
          {generatedLetter && (
            <Card className="mt-6">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Generated Letter</CardTitle>
                  <div className="flex gap-2">
                    <Button size="sm" variant="secondary" onClick={handleCopyToClipboard}>
                      Copy
                    </Button>
                    <Button size="sm" onClick={handleDownload}>
                      Download
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 p-6 rounded-lg font-mono text-sm whitespace-pre-wrap">
                  {generatedLetter}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
