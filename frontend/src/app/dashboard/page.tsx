'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { projectsApi } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import { formatDate, getStatusColor } from '@/lib/utils'
import {
  Plus,
  FolderOpen,
  FileText,
  Clock,
  ArrowRight,
  Loader2,
} from 'lucide-react'

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user)

  const { data: projectsData, isLoading } = useQuery({
    queryKey: ['projects', { page: 1, page_size: 5 }],
    queryFn: () => projectsApi.list({ page: 1, page_size: 5 }),
  })

  return (
    <div className="space-y-8">
      {/* Welcome section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-8 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Welcome back, {user?.full_name || 'User'}!
        </h1>
        <p className="text-primary-100 mb-6">
          Create compelling grant proposals with AI-powered assistance
        </p>
        <Link
          href="/dashboard/projects/new"
          className="inline-flex items-center px-4 py-2 bg-white text-primary-700 rounded-lg font-medium hover:bg-primary-50 transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          New Project
        </Link>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-primary-100 rounded-lg">
              <FolderOpen className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Projects</p>
              <p className="text-2xl font-bold text-gray-900">
                {projectsData?.total || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Proposals Generated</p>
              <p className="text-2xl font-bold text-gray-900">
                {projectsData?.items?.reduce(
                  (acc: number, p: any) => acc + (p.proposal_count || 0),
                  0
                ) || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">In Progress</p>
              <p className="text-2xl font-bold text-gray-900">
                {projectsData?.items?.filter(
                  (p: any) => p.status === 'in_progress'
                ).length || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent projects */}
      <div className="card">
        <div className="p-6 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Projects</h2>
          <Link
            href="/dashboard/projects"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center"
          >
            View all
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-400" />
          </div>
        ) : projectsData?.items?.length > 0 ? (
          <div className="divide-y">
            {projectsData.items.map((project: any) => (
              <Link
                key={project.id}
                href={`/dashboard/projects/${project.id}`}
                className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <FolderOpen className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{project.name}</p>
                    <p className="text-sm text-gray-500">
                      {project.document_count} documents • {project.proposal_count} proposals
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      project.status
                    )}`}
                  >
                    {project.status.replace('_', ' ')}
                  </span>
                  <span className="text-sm text-gray-500">
                    {formatDate(project.updated_at)}
                  </span>
                  <ArrowRight className="w-4 h-4 text-gray-400" />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <FolderOpen className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 mb-4">No projects yet</p>
            <Link href="/dashboard/projects/new" className="btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              Create your first project
            </Link>
          </div>
        )}
      </div>

      {/* Getting started */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold">
              1
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Upload Guidelines</h3>
              <p className="text-sm text-gray-500 mt-1">
                Upload the grant guidelines, RFP, terms & conditions, and eligibility criteria
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold">
              2
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Add Beneficiary Details</h3>
              <p className="text-sm text-gray-500 mt-1">
                Upload organization profiles, project descriptions, and supporting documents
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold">
              3
            </div>
            <div>
              <h3 className="font-medium text-gray-900">Generate Proposal</h3>
              <p className="text-sm text-gray-500 mt-1">
                AI generates a tailored proposal based on all uploaded documents
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
