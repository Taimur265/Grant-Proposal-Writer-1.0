'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { proposalsApi } from '@/lib/api'
import type { Proposal, ProposalSection, ProposalFeedback, ComplianceCheck, PaginatedResponse, GenerateProposalForm } from '@/types'
import toast from 'react-hot-toast'
import { downloadBlob } from '@/lib/utils'

export function useProposals(params?: {
  project_id?: string
  page?: number
  status?: string
}) {
  return useQuery<PaginatedResponse<Proposal>>({
    queryKey: ['proposals', params],
    queryFn: () => proposalsApi.list(params),
  })
}

export function useProposal(id: string) {
  return useQuery<Proposal>({
    queryKey: ['proposal', id],
    queryFn: () => proposalsApi.get(id),
    enabled: !!id,
  })
}

export function useGenerateProposal() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: GenerateProposalForm) => proposalsApi.generate(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['proposals', { project_id: variables.project_id }] })
      toast.success('Proposal generated successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to generate proposal')
    },
  })
}

export function useUpdateProposal() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Proposal> }) =>
      proposalsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['proposal', id] })
      queryClient.invalidateQueries({ queryKey: ['proposals'] })
      toast.success('Proposal updated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update proposal')
    },
  })
}

export function useDeleteProposal() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: proposalsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] })
      toast.success('Proposal deleted')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete proposal')
    },
  })
}

export function useUpdateSection(proposalId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      sectionId,
      data,
    }: {
      sectionId: string
      data: { content?: string; is_complete?: boolean }
    }) => proposalsApi.updateSection(proposalId, sectionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal', proposalId] })
      toast.success('Section updated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update section')
    },
  })
}

export function useRegenerateSection(proposalId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sectionId, feedback }: { sectionId: string; feedback?: string }) =>
      proposalsApi.regenerateSection(proposalId, sectionId, feedback),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal', proposalId] })
      toast.success('Section regenerated')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to regenerate section')
    },
  })
}

export function useCheckCompliance(proposalId: string) {
  const queryClient = useQueryClient()

  return useMutation<ComplianceCheck>({
    mutationFn: () => proposalsApi.checkCompliance(proposalId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['proposal', proposalId] })
      toast.success(`Compliance score: ${data.overall_score?.toFixed(0) || 0}%`)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to check compliance')
    },
  })
}

export function useExportProposal(proposal?: Proposal) {
  return useMutation({
    mutationFn: ({ id, format }: { id: string; format: string }) =>
      proposalsApi.export(id, format),
    onSuccess: (data, { format }) => {
      const filename = `${proposal?.title || 'proposal'}.${format}`
      downloadBlob(data, filename)
      toast.success('Proposal exported')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to export proposal')
    },
  })
}

export function useProposalFeedback(proposalId: string) {
  return useQuery<ProposalFeedback[]>({
    queryKey: ['proposal-feedback', proposalId],
    queryFn: () => proposalsApi.listFeedback(proposalId),
    enabled: !!proposalId,
  })
}

export function useAddFeedback(proposalId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { section_id?: string; feedback_type: string; content: string }) =>
      proposalsApi.addFeedback(proposalId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposal-feedback', proposalId] })
      toast.success('Feedback added')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to add feedback')
    },
  })
}
