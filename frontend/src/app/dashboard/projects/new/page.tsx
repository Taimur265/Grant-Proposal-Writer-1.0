'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Loader2, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import Link from 'next/link'
import { projectsApi } from '@/lib/api'

const projectSchema = z.object({
  name: z.string().min(1, 'Project name is required').max(255),
  description: z.string().optional(),
  grant_type: z.string().optional(),
  funding_agency: z.string().optional(),
  deadline: z.string().optional(),
  target_amount: z.string().optional(),
})

type ProjectForm = z.infer<typeof projectSchema>

export default function NewProjectPage() {
  const router = useRouter()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProjectForm>({
    resolver: zodResolver(projectSchema),
  })

  const createMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: (data) => {
      toast.success('Project created successfully!')
      router.push(`/dashboard/projects/${data.id}`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create project')
    },
  })

  const onSubmit = (data: ProjectForm) => {
    createMutation.mutate(data)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Link
        href="/dashboard/projects"
        className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Projects
      </Link>

      <div className="card">
        <div className="p-6 border-b">
          <h1 className="text-xl font-semibold text-gray-900">Create New Project</h1>
          <p className="text-gray-600 mt-1">
            Set up a new grant proposal project
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              {...register('name')}
              type="text"
              id="name"
              className="input"
              placeholder="e.g., Community Health Initiative 2024"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              {...register('description')}
              id="description"
              rows={3}
              className="input"
              placeholder="Brief description of the project..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="grant_type" className="block text-sm font-medium text-gray-700 mb-1">
                Grant Type
              </label>
              <select {...register('grant_type')} id="grant_type" className="input">
                <option value="">Select type</option>
                <option value="federal">Federal</option>
                <option value="state">State</option>
                <option value="foundation">Foundation</option>
                <option value="corporate">Corporate</option>
                <option value="international">International</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label htmlFor="funding_agency" className="block text-sm font-medium text-gray-700 mb-1">
                Funding Agency
              </label>
              <input
                {...register('funding_agency')}
                type="text"
                id="funding_agency"
                className="input"
                placeholder="e.g., NIH, NSF, Ford Foundation"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-1">
                Deadline
              </label>
              <input
                {...register('deadline')}
                type="datetime-local"
                id="deadline"
                className="input"
              />
            </div>

            <div>
              <label htmlFor="target_amount" className="block text-sm font-medium text-gray-700 mb-1">
                Target Amount
              </label>
              <input
                {...register('target_amount')}
                type="text"
                id="target_amount"
                className="input"
                placeholder="e.g., $50,000"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Link href="/dashboard/projects" className="btn-outline">
              Cancel
            </Link>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Project'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
