'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import {
  ArrowLeft,
  Download,
  RefreshCw,
  CheckCircle,
  Edit2,
  Save,
  X,
  Loader2,
  FileText,
  Sparkles,
  AlertTriangle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { proposalsApi } from '@/lib/api'
import { formatDate, getStatusColor, downloadBlob, cn } from '@/lib/utils'
import * as Tabs from '@radix-ui/react-tabs'

export default function ProposalDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const projectId = params.id as string
  const proposalId = params.proposalId as string

  const [editingSection, setEditingSection] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [activeTab, setActiveTab] = useState('content')

  // Fetch proposal
  const { data: proposal, isLoading } = useQuery({
    queryKey: ['proposal', proposalId],
    queryFn: () => proposalsApi.get(proposalId),
  })

  // Update section mutation
  const updateSectionMutation = useMutation({
    mutationFn: ({ sectionId, content }: { sectionId: string; content: string }) =>
      proposalsApi.updateSection(proposalId, sectionId, { content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal', proposalId] })
      setEditingSection(null)
      toast.success('Section updated')
    },
    onError: () => {
      toast.error('Failed to update section')
    },
  })

  // Regenerate section mutation
  const regenerateMutation = useMutation({
    mutationFn: ({ sectionId, feedback }: { sectionId: string; feedback?: string }) =>
      proposalsApi.regenerateSection(proposalId, sectionId, feedback),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal', proposalId] })
      toast.success('Section regenerated')
    },
    onError: () => {
      toast.error('Failed to regenerate section')
    },
  })

  // Compliance check mutation
  const complianceMutation = useMutation({
    mutationFn: () => proposalsApi.checkCompliance(proposalId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['proposal', proposalId] })
      toast.success(`Compliance score: ${data.overall_score?.toFixed(0) || 0}%`)
    },
    onError: () => {
      toast.error('Failed to check compliance')
    },
  })

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: (format: string) => proposalsApi.export(proposalId, format),
    onSuccess: (data, format) => {
      const filename = `${proposal?.title || 'proposal'}.${format}`
      downloadBlob(data, filename)
      toast.success('Proposal exported')
    },
    onError: () => {
      toast.error('Failed to export proposal')
    },
  })

  const handleStartEdit = (section: any) => {
    setEditingSection(section.id)
    setEditContent(section.content || '')
  }

  const handleSaveEdit = (sectionId: string) => {
    updateSectionMutation.mutate({ sectionId, content: editContent })
  }

  const handleCancelEdit = () => {
    setEditingSection(null)
    setEditContent('')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!proposal) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <h2 className="text-lg font-medium text-gray-900">Proposal not found</h2>
        <Link
          href={`/dashboard/projects/${projectId}`}
          className="text-primary-600 hover:underline mt-2 inline-block"
        >
          Back to project
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            href={`/dashboard/projects/${projectId}`}
            className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Project
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{proposal.title}</h1>
          <div className="flex items-center space-x-4 mt-2">
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                proposal.status
              )}`}
            >
              {proposal.status}
            </span>
            <span className="text-sm text-gray-500">
              Version {proposal.version}
            </span>
            <span className="text-sm text-gray-500">
              {proposal.word_count?.toLocaleString()} words
            </span>
            {proposal.compliance_score && (
              <span className="text-sm text-gray-500">
                Score: {proposal.compliance_score.toFixed(0)}%
              </span>
            )}
            <span className="text-sm text-gray-500">
              Created {formatDate(proposal.created_at)}
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => complianceMutation.mutate()}
            disabled={complianceMutation.isPending}
            className="btn-outline"
          >
            {complianceMutation.isPending ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4 mr-2" />
            )}
            Check Compliance
          </button>
          <div className="relative group">
            <button className="btn-primary">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
            <div className="absolute right-0 mt-2 w-40 bg-white rounded-lg shadow-lg border py-1 hidden group-hover:block z-10">
              {['docx', 'txt', 'md', 'html'].map((format) => (
                <button
                  key={format}
                  onClick={() => exportMutation.mutate(format)}
                  disabled={exportMutation.isPending}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100"
                >
                  Export as .{format.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Content Tabs */}
      <Tabs.Root value={activeTab} onValueChange={setActiveTab}>
        <Tabs.List className="flex space-x-1 border-b">
          <Tabs.Trigger
            value="content"
            className={cn(
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === 'content'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            Full Proposal
          </Tabs.Trigger>
          <Tabs.Trigger
            value="sections"
            className={cn(
              'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              activeTab === 'sections'
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >
            Edit Sections
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="content" className="pt-6">
          <div className="card p-8 prose prose-lg max-w-none">
            {proposal.executive_summary && (
              <div className="mb-8 p-6 bg-primary-50 rounded-lg">
                <h2 className="text-xl font-bold text-primary-900 mb-4">Executive Summary</h2>
                <p className="text-primary-800">{proposal.executive_summary}</p>
              </div>
            )}
            {proposal.sections?.map((section: any) => (
              <div key={section.id} className="mb-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4">{section.section_name}</h2>
                <ReactMarkdown>{section.content || ''}</ReactMarkdown>
              </div>
            ))}
          </div>
        </Tabs.Content>

        <Tabs.Content value="sections" className="pt-6 space-y-4">
          {proposal.sections?.map((section: any) => (
            <div key={section.id} className="card">
              <div className="p-4 border-b flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{section.section_name}</h3>
                  <div className="flex items-center space-x-3 text-sm text-gray-500 mt-1">
                    <span>{section.word_count?.toLocaleString() || 0} words</span>
                    {section.max_words && (
                      <>
                        <span>•</span>
                        <span
                          className={cn(
                            section.word_count > section.max_words ? 'text-red-600' : ''
                          )}
                        >
                          Max: {section.max_words}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {editingSection !== section.id ? (
                    <>
                      <button
                        onClick={() => handleStartEdit(section)}
                        className="btn-ghost text-gray-600"
                      >
                        <Edit2 className="w-4 h-4 mr-1" />
                        Edit
                      </button>
                      <button
                        onClick={() =>
                          regenerateMutation.mutate({ sectionId: section.id })
                        }
                        disabled={regenerateMutation.isPending}
                        className="btn-ghost text-gray-600"
                      >
                        {regenerateMutation.isPending ? (
                          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4 mr-1" />
                        )}
                        Regenerate
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => handleSaveEdit(section.id)}
                        disabled={updateSectionMutation.isPending}
                        className="btn-primary"
                      >
                        {updateSectionMutation.isPending ? (
                          <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                        ) : (
                          <Save className="w-4 h-4 mr-1" />
                        )}
                        Save
                      </button>
                      <button onClick={handleCancelEdit} className="btn-ghost">
                        <X className="w-4 h-4 mr-1" />
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>
              <div className="p-4">
                {editingSection === section.id ? (
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full h-64 p-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Enter section content..."
                  />
                ) : (
                  <div className="prose max-w-none">
                    <ReactMarkdown>{section.content || 'No content yet'}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}
        </Tabs.Content>
      </Tabs.Root>
    </div>
  )
}
