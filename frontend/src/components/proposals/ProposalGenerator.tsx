'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, X, Loader2, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { proposalsApi } from '@/lib/api'

interface ProposalGeneratorProps {
  projectId: string
  projectName: string
  onClose: () => void
  onSuccess: () => void
}

interface GenerateForm {
  title: string
  tone: string
  ai_provider: string
  custom_instructions: string
}

export default function ProposalGenerator({
  projectId,
  projectName,
  onClose,
  onSuccess,
}: ProposalGeneratorProps) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  const { register, handleSubmit } = useForm<GenerateForm>({
    defaultValues: {
      title: `Grant Proposal - ${projectName}`,
      tone: 'professional',
      ai_provider: 'openai',
      custom_instructions: '',
    },
  })

  const generateMutation = useMutation({
    mutationFn: proposalsApi.generate,
    onSuccess: () => {
      toast.success('Proposal generated successfully!')
      onSuccess()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to generate proposal')
    },
  })

  const onSubmit = (data: GenerateForm) => {
    generateMutation.mutate({
      project_id: projectId,
      title: data.title,
      tone: data.tone,
      ai_provider: data.ai_provider || undefined,
      custom_instructions: data.custom_instructions || undefined,
    })
  }

  return (
    <div>
      <div className="flex items-center justify-between p-6 border-b">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Sparkles className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Generate Proposal</h2>
            <p className="text-sm text-gray-600">AI will create a proposal based on your documents</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Proposal Title
          </label>
          <input
            {...register('title')}
            type="text"
            className="input"
            placeholder="Enter proposal title"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Writing Tone
          </label>
          <select {...register('tone')} className="input">
            <option value="professional">Professional</option>
            <option value="academic">Academic</option>
            <option value="conversational">Conversational</option>
            <option value="formal">Formal</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Sets the overall writing style for the proposal
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <Settings className="w-4 h-4 mr-2" />
          {showAdvanced ? 'Hide' : 'Show'} Advanced Options
        </button>

        {showAdvanced && (
          <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AI Provider
              </label>
              <select {...register('ai_provider')} className="input">
                <option value="openai">OpenAI (GPT-4)</option>
                <option value="anthropic">Anthropic (Claude)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Custom Instructions
              </label>
              <textarea
                {...register('custom_instructions')}
                rows={3}
                className="input"
                placeholder="Any specific instructions for the AI (e.g., emphasize sustainability, focus on community impact)..."
              />
            </div>
          </div>
        )}

        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">What happens next?</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>1. AI analyzes your uploaded guidelines and requirements</li>
            <li>2. Organization/beneficiary information is incorporated</li>
            <li>3. A complete proposal is generated with all required sections</li>
            <li>4. You can review, edit, and export the proposal</li>
          </ul>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button type="button" onClick={onClose} className="btn-outline">
            Cancel
          </button>
          <button
            type="submit"
            disabled={generateMutation.isPending}
            className="btn-primary"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating... (this may take a minute)
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generate Proposal
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
