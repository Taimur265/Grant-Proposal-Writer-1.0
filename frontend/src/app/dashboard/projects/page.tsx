'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { projectsApi } from '@/lib/api'
import { formatDate, getStatusColor } from '@/lib/utils'
import {
  Plus,
  FolderOpen,
  Search,
  Filter,
  Loader2,
  ArrowRight,
} from 'lucide-react'

export default function ProjectsPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['projects', { page, search, status: statusFilter }],
    queryFn: () =>
      projectsApi.list({
        page,
        page_size: 10,
        search: search || undefined,
        status: statusFilter || undefined,
      }),
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600 mt-1">Manage your grant proposal projects</p>
        </div>
        <Link href="/dashboard/projects/new" className="btn-primary">
          <Plus className="w-5 h-5 mr-2" />
          New Project
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input w-full sm:w-48"
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="in_progress">In Progress</option>
            <option value="review">Review</option>
            <option value="submitted">Submitted</option>
            <option value="approved">Approved</option>
          </select>
        </div>
      </div>

      {/* Projects list */}
      <div className="card">
        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-400" />
            <p className="text-gray-500 mt-2">Loading projects...</p>
          </div>
        ) : data?.items?.length > 0 ? (
          <>
            <div className="divide-y">
              {data.items.map((project: any) => (
                <Link
                  key={project.id}
                  href={`/dashboard/projects/${project.id}`}
                  className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-gray-100 rounded-lg">
                      <FolderOpen className="w-6 h-6 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{project.name}</h3>
                      <div className="flex items-center space-x-3 mt-1 text-sm text-gray-500">
                        {project.funding_agency && (
                          <>
                            <span>{project.funding_agency}</span>
                            <span>•</span>
                          </>
                        )}
                        <span>{project.document_count} documents</span>
                        <span>•</span>
                        <span>{project.proposal_count} proposals</span>
                      </div>
                      {project.description && (
                        <p className="text-sm text-gray-600 mt-1 line-clamp-1">
                          {project.description}
                        </p>
                      )}
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
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        Updated {formatDate(project.updated_at)}
                      </p>
                      {project.deadline && (
                        <p className="text-xs text-gray-400">
                          Due: {formatDate(project.deadline)}
                        </p>
                      )}
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-between p-4 border-t">
                <p className="text-sm text-gray-500">
                  Showing {(page - 1) * 10 + 1} to{' '}
                  {Math.min(page * 10, data.total)} of {data.total} projects
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="btn-outline"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page === data.total_pages}
                    className="btn-outline"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="p-8 text-center">
            <FolderOpen className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects found</h3>
            <p className="text-gray-500 mb-4">
              {search || statusFilter
                ? 'Try adjusting your filters'
                : 'Get started by creating your first project'}
            </p>
            {!search && !statusFilter && (
              <Link href="/dashboard/projects/new" className="btn-primary">
                <Plus className="w-4 h-4 mr-2" />
                Create Project
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
