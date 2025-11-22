'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi, getDocumentTypes } from '@/lib/api'
import type { Document, DocumentContent, DocumentTypesResponse, PaginatedResponse } from '@/types'
import toast from 'react-hot-toast'

export function useDocuments(
  projectId: string,
  params?: {
    page?: number
    category?: string
    document_type?: string
  }
) {
  return useQuery<PaginatedResponse<Document>>({
    queryKey: ['documents', projectId, params],
    queryFn: () => documentsApi.list(projectId, params),
    enabled: !!projectId,
  })
}

export function useDocument(id: string) {
  return useQuery<Document>({
    queryKey: ['document', id],
    queryFn: () => documentsApi.get(id),
    enabled: !!id,
  })
}

export function useDocumentContent(id: string) {
  return useQuery<DocumentContent>({
    queryKey: ['document-content', id],
    queryFn: () => documentsApi.getContent(id),
    enabled: !!id,
  })
}

export function useDocumentTypes() {
  return useQuery<DocumentTypesResponse>({
    queryKey: ['document-types'],
    queryFn: getDocumentTypes,
    staleTime: Infinity,
  })
}

export function useUploadDocument(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      file,
      category,
      documentType,
    }: {
      file: File
      category: string
      documentType?: string
    }) => documentsApi.upload(file, projectId, category, documentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] })
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload document')
    },
  })
}

export function useDeleteDocument(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project-stats', projectId] })
      toast.success('Document deleted')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete document')
    },
  })
}

export function useReprocessDocument(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: documentsApi.reprocess,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] })
      toast.success('Document reprocessing started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reprocess document')
    },
  })
}
