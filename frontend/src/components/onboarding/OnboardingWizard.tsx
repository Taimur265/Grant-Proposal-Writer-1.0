'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface OnboardingData {
  organizationName: string;
  organizationType: string;
  projectName: string;
  grantType: string;
  deadline: string;
  targetAmount: string;
}

const STEPS = [
  { id: 'welcome', title: 'Welcome' },
  { id: 'organization', title: 'Organization' },
  { id: 'project', title: 'Project' },
  { id: 'complete', title: 'Get Started' },
];

const ORGANIZATION_TYPES = [
  { value: 'nonprofit', label: 'Non-Profit Organization' },
  { value: 'academic', label: 'Academic Institution' },
  { value: 'government', label: 'Government Agency' },
  { value: 'ngo', label: 'NGO' },
  { value: 'social_enterprise', label: 'Social Enterprise' },
  { value: 'other', label: 'Other' },
];

const GRANT_TYPES = [
  { value: 'federal', label: 'Federal Grant', description: 'Government grants from federal agencies' },
  { value: 'foundation', label: 'Foundation Grant', description: 'Grants from private foundations' },
  { value: 'corporate', label: 'Corporate Grant', description: 'Corporate social responsibility funding' },
  { value: 'international', label: 'International', description: 'International development funding' },
  { value: 'research', label: 'Research Grant', description: 'Academic and scientific research funding' },
];

export function OnboardingWizard({ onComplete }: { onComplete?: () => void }) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    organizationName: '',
    organizationType: '',
    projectName: '',
    grantType: '',
    deadline: '',
    targetAmount: '',
  });

  const createProjectMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/projects', {
        name: data.projectName,
        description: `Grant proposal project for ${data.organizationName}`,
        grant_type: data.grantType,
        deadline: data.deadline || null,
        target_amount: data.targetAmount ? parseFloat(data.targetAmount) : null,
      });
      return response.data;
    },
    onSuccess: (project) => {
      if (onComplete) {
        onComplete();
      }
      router.push(`/dashboard/projects/${project.id}`);
    },
  });

  const nextStep = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    createProjectMutation.mutate();
  };

  const renderStep = () => {
    switch (STEPS[currentStep].id) {
      case 'welcome':
        return (
          <div className="text-center py-8">
            <div className="mb-6">
              <svg className="w-20 h-20 mx-auto text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Welcome to Grant Proposal Writer
            </h2>
            <p className="text-gray-600 max-w-md mx-auto mb-8">
              Let's get you started with creating your first grant proposal. We'll guide you through setting up your project in just a few steps.
            </p>
            <div className="space-y-4 text-left max-w-md mx-auto">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">1</div>
                <div>
                  <p className="font-medium text-gray-900">Upload Documents</p>
                  <p className="text-sm text-gray-500">Upload grant guidelines and your organization documents</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">2</div>
                <div>
                  <p className="font-medium text-gray-900">AI Analysis</p>
                  <p className="text-sm text-gray-500">Our AI analyzes requirements and your capabilities</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-medium">3</div>
                <div>
                  <p className="font-medium text-gray-900">Generate Proposal</p>
                  <p className="text-sm text-gray-500">Get a complete, compliant proposal in minutes</p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'organization':
        return (
          <div className="py-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Tell us about your organization</h2>
            <p className="text-gray-600 mb-6">This helps us tailor the proposal to your specific needs.</p>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Name
                </label>
                <Input
                  value={data.organizationName}
                  onChange={(e) => setData({ ...data, organizationName: e.target.value })}
                  placeholder="Enter your organization name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Type
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {ORGANIZATION_TYPES.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setData({ ...data, organizationType: type.value })}
                      className={`p-3 border rounded-lg text-left transition-colors ${
                        data.organizationType === type.value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span className="text-sm font-medium">{type.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'project':
        return (
          <div className="py-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Set up your project</h2>
            <p className="text-gray-600 mb-6">Tell us about the grant you're applying for.</p>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Project Name
                </label>
                <Input
                  value={data.projectName}
                  onChange={(e) => setData({ ...data, projectName: e.target.value })}
                  placeholder="e.g., Community Health Initiative 2024"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Grant Type
                </label>
                <div className="space-y-3">
                  {GRANT_TYPES.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setData({ ...data, grantType: type.value })}
                      className={`w-full p-4 border rounded-lg text-left transition-colors ${
                        data.grantType === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span className="font-medium text-gray-900">{type.label}</span>
                      <p className="text-sm text-gray-500 mt-1">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Deadline (optional)
                  </label>
                  <Input
                    type="date"
                    value={data.deadline}
                    onChange={(e) => setData({ ...data, deadline: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Amount (optional)
                  </label>
                  <Input
                    type="number"
                    value={data.targetAmount}
                    onChange={(e) => setData({ ...data, targetAmount: e.target.value })}
                    placeholder="$0.00"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 'complete':
        return (
          <div className="text-center py-8">
            <div className="mb-6">
              <svg className="w-20 h-20 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              You're all set!
            </h2>
            <p className="text-gray-600 max-w-md mx-auto mb-8">
              We'll create your project and you can start uploading documents right away. Our AI will help you create a compelling grant proposal.
            </p>

            <div className="bg-gray-50 rounded-lg p-6 max-w-md mx-auto text-left">
              <h3 className="font-medium text-gray-900 mb-4">Project Summary</h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Organization</dt>
                  <dd className="font-medium text-gray-900">{data.organizationName || 'Not specified'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Project</dt>
                  <dd className="font-medium text-gray-900">{data.projectName || 'Not specified'}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Grant Type</dt>
                  <dd className="font-medium text-gray-900 capitalize">{data.grantType || 'Not specified'}</dd>
                </div>
                {data.deadline && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">Deadline</dt>
                    <dd className="font-medium text-gray-900">{new Date(data.deadline).toLocaleDateString()}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg max-w-2xl mx-auto">
      {/* Progress indicator */}
      <div className="px-6 pt-6">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  index < currentStep
                    ? 'bg-blue-600 text-white'
                    : index === currentStep
                    ? 'bg-blue-100 text-blue-600 border-2 border-blue-600'
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                {index < currentStep ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              {index < STEPS.length - 1 && (
                <div className={`w-16 h-1 mx-2 ${index < currentStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-8">{renderStep()}</div>

      {/* Navigation */}
      <div className="px-6 pb-6 flex justify-between">
        <Button
          variant="secondary"
          onClick={prevStep}
          disabled={currentStep === 0}
          className={currentStep === 0 ? 'invisible' : ''}
        >
          Back
        </Button>
        {currentStep < STEPS.length - 1 ? (
          <Button onClick={nextStep}>
            Continue
          </Button>
        ) : (
          <Button
            onClick={handleComplete}
            disabled={createProjectMutation.isPending || !data.projectName}
          >
            {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
          </Button>
        )}
      </div>
    </div>
  );
}
