'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import * as Tabs from '@radix-ui/react-tabs'
import {
  ArrowLeft,
  FileText,
  Settings,
  Trash2,
  Loader2,
  Upload,
  Sparkles,
  FolderOpen,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { projectsApi, documentsApi, proposalsApi, getDocumentTypes } from '@/lib/api'
import { formatDate, getStatusColor, cn } from '@/lib/utils'
import DocumentUploader from '@/components/documents/DocumentUploader'
import DocumentList from '@/components/documents/DocumentList'
import ProposalGenerator from '@/components/proposals/ProposalGenerator'
import * as Dialog from '@radix-ui/react-dialog'

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState('guidelines')
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showGenerateDialog, setShowGenerateDialog] = useState(false)

  // Fetch project
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId),
  })

  // Fetch project stats
  const { data: stats } = useQuery({
    queryKey: ['project-stats', projectId],
    queryFn: () => projectsApi.getStats(projectId),
  })

  // Fetch documents
  const { data: guidelinesData, isLoading: guidelinesLoading } = useQuery({
    queryKey: ['documents', projectId, 'guidelines'],
    queryFn: () => documentsApi.list(projectId, { category: 'guidelines' }),
  })

  const { data: beneficiaryData, isLoading: beneficiaryLoading } = useQuery({
    queryKey: ['documents', projectId, 'beneficiary'],
    queryFn: () => documentsApi.list(projectId, { category: 'beneficiary' }),
  })

  // Fetch proposals
  const { data: proposalsData } = useQuery({
    queryKey: ['proposals', projectId],
    queryFn: () => proposalsApi.list({ project_id: projectId }),
  })

  // Fetch document types
  const { data: docTypes } = useQuery({
    queryKey: ['document-types'],
    queryFn: getDocumentTypes,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => projectsApi.delete(projectId),
    onSuccess: () => {
      toast.success('Project deleted')
      router.push('/dashboard/projects')
    },
    onError: () => {
      toast.error('Failed to delete project')
    },
  })

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <FolderOpen className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <h2 className="text-lg font-medium text-gray-900">Project not found</h2>
        <Link href="/dashboard/projects" className="text-primary-600 hover:underline mt-2 inline-block">
          Back to projects
        </Link>
      </div>
    )
  }

  const guidelinesTypes = docTypes?.categories?.guidelines?.types || []
  const beneficiaryTypes = docTypes?.categories?.beneficiary?.types || []

  const canGenerateProposal =
    (guidelinesData?.items?.length > 0) &&
    guidelinesData?.items?.some((d: any) => d.processing_status === 'completed')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            href="/dashboard/projects"
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Projects
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          {project.description && (
            <p className="text-gray-600 mt-1">{project.description}</p>
          )}
          <div className="flex items-center space-x-4 mt-2">
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                project.status
              )}`}
            >
              {project.status.replace('_', ' ')}
            </span>
            {project.funding_agency && (
              <span className="text-sm text-gray-500">{project.funding_agency}</span>
            )}
            {project.deadline && (
              <span className="text-sm text-gray-500">
                Deadline: {formatDate(project.deadline)}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowGenerateDialog(true)}
            disabled={!canGenerateProposal}
            className={cn(
              'btn-primary',
              !canGenerateProposal && 'opacity-50 cursor-not-allowed'
            )}
          >
            <Sparkles className="w-5 h-5 mr-2" />
            Generate Proposal
          </button>
          <button
            onClick={() => setShowDeleteDialog(true)}
            className="btn-outline text-red-600 hover:bg-red-50"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats?.guidelines_documents || 0}</p>
              <p className="text-sm text-gray-500">Guidelines Docs</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <FileText className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats?.beneficiary_documents || 0}</p>
              <p className="text-sm text-gray-500">Beneficiary Docs</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Sparkles className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_proposals || 0}</p>
              <p className="text-sm text-gray-500">Proposals</p>
            </div>
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center space-x-3">
            <div className={cn(
              'p-2 rounded-lg',
              canGenerateProposal ? 'bg-green-100' : 'bg-yellow-100'
            )}>
              {canGenerateProposal ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                {canGenerateProposal ? 'Ready' : 'Not Ready'}
              </p>
              <p className="text-xs text-gray-500">
                {canGenerateProposal ? 'Can generate proposal' : 'Upload guidelines first'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Document Sections */}
      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List className="flex space-x-1 border-b">
          <Tabs.Trigger
            value="guidelines"
            className={cn(
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === 'guidelines'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            Guidelines & Requirements
            <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
              {guidelinesData?.total || 0}
            </span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="beneficiary"
            className={cn(
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === 'beneficiary'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            Beneficiary Information
            <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
              {beneficiaryData?.total || 0}
            </span>
          </Tabs.Trigger>
          <Tabs.Trigger
            value="proposals"
            className={cn(
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === 'proposals'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            <Sparkles className="w-4 h-4 inline mr-2" />
            Proposals
            <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
              {proposalsData?.total || 0}
            </span>
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="guidelines" className="pt-6">
          <div className="card">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Guidelines & Requirements</h2>
              <p className="text-gray-600 mt-1">
                Upload grant guidelines, RFPs, terms & conditions, and eligibility criteria
              </p>
            </div>
            <div className="p-6">
              <DocumentUploader
                projectId={projectId}
                category="guidelines"
                documentTypes={guidelinesTypes}
                onUploadComplete={() => {
                  queryClient.invalidateQueries({ queryKey: ['documents', projectId, 'guidelines'] })
                  queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] })
                }}
              />
            </div>
            <div className="border-t">
              {guidelinesLoading ? (
                <div className="p-8 text-center">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400" />
                </div>
              ) : (
                <DocumentList
                  documents={guidelinesData?.items || []}
                  projectId={projectId}
                />
              )}
            </div>
          </div>
        </Tabs.Content>

        <Tabs.Content value="beneficiary" className="pt-6">
          <div className="card">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Beneficiary Information</h2>
              <p className="text-gray-600 mt-1">
                Upload organization profiles, project descriptions, financial statements, and team CVs
              </p>
            </div>
            <div className="p-6">
              <DocumentUploader
                projectId={projectId}
                category="beneficiary"
                documentTypes={beneficiaryTypes}
                onUploadComplete={() => {
                  queryClient.invalidateQueries({ queryKey: ['documents', projectId, 'beneficiary'] })
                  queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] })
                }}
              />
            </div>
            <div className="border-t">
              {beneficiaryLoading ? (
                <div className="p-8 text-center">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400" />
                </div>
              ) : (
                <DocumentList
                  documents={beneficiaryData?.items || []}
                  projectId={projectId}
                />
              )}
            </div>
          </div>
        </Tabs.Content>

        <Tabs.Content value="proposals" className="pt-6">
          <div className="card">
            <div className="p-6 border-b flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Generated Proposals</h2>
                <p className="text-gray-600 mt-1">
                  AI-generated proposals based on your uploaded documents
                </p>
              </div>
              <button
                onClick={() => setShowGenerateDialog(true)}
                disabled={!canGenerateProposal}
                className={cn(
                  'btn-primary',
                  !canGenerateProposal && 'opacity-50 cursor-not-allowed'
                )}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Generate New
              </button>
            </div>
            <div className="divide-y">
              {proposalsData?.items?.length > 0 ? (
                proposalsData.items.map((proposal: any) => (
                  <Link
                    key={proposal.id}
                    href={`/dashboard/projects/${projectId}/proposals/${proposal.id}`}
                    className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div>
                      <h3 className="font-medium text-gray-900">{proposal.title}</h3>
                      <div className="flex items-center space-x-3 mt-1 text-sm text-gray-500">
                        <span>Version {proposal.version}</span>
                        <span>•</span>
                        <span>{proposal.word_count?.toLocaleString()} words</span>
                        <span>•</span>
                        <span>{formatDate(proposal.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {proposal.compliance_score && (
                        <span className="text-sm text-gray-500">
                          Score: {proposal.compliance_score.toFixed(0)}%
                        </span>
                      )}
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                          proposal.status
                        )}`}
                      >
                        {proposal.status}
                      </span>
                    </div>
                  </Link>
                ))
              ) : (
                <div className="p-8 text-center">
                  <Sparkles className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No proposals yet</h3>
                  <p className="text-gray-500 mb-4">
                    {canGenerateProposal
                      ? 'Generate your first proposal using AI'
                      : 'Upload guidelines documents first to generate proposals'}
                  </p>
                  {canGenerateProposal && (
                    <button
                      onClick={() => setShowGenerateDialog(true)}
                      className="btn-primary"
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Proposal
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </Tabs.Content>
      </Tabs.Root>

      {/* Delete Dialog */}
      <Dialog.Root open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg p-6 w-full max-w-md">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Delete Project
            </Dialog.Title>
            <Dialog.Description className="text-gray-600 mt-2">
              Are you sure you want to delete this project? This will also delete all documents
              and proposals associated with it. This action cannot be undone.
            </Dialog.Description>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowDeleteDialog(false)}
                className="btn-outline"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
                className="btn-destructive"
              >
                {deleteMutation.isPending ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4 mr-2" />
                )}
                Delete Project
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Generate Proposal Dialog */}
      <Dialog.Root open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <ProposalGenerator
              projectId={projectId}
              projectName={project.name}
              onClose={() => setShowGenerateDialog(false)}
              onSuccess={() => {
                setShowGenerateDialog(false)
                setActiveTab('proposals')
                queryClient.invalidateQueries({ queryKey: ['proposals', projectId] })
              }}
            />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  )
}
