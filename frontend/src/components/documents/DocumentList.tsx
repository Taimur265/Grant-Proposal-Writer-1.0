'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Trash2,
  RefreshCw,
  Eye,
  MoreVertical,
  Loader2,
  CheckCircle,
  Clock,
  AlertCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { documentsApi } from '@/lib/api'
import { formatBytes, formatDate, getDocumentIcon, getStatusColor } from '@/lib/utils'
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'

interface Document {
  id: string
  original_filename: string
  file_extension: string
  file_size: number
  document_type: string
  processing_status: string
  summary?: string
  key_points?: string[]
  created_at: string
}

interface DocumentListProps {
  documents: Document[]
  projectId: string
  onViewContent?: (document: Document) => void
}

export default function DocumentList({
  documents,
  projectId,
  onViewContent,
}: DocumentListProps) {
  const queryClient = useQueryClient()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] })
      toast.success('Document deleted')
    },
    onError: () => {
      toast.error('Failed to delete document')
    },
  })

  const reprocessMutation = useMutation({
    mutationFn: documentsApi.reprocess,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] })
      toast.success('Document reprocessing started')
    },
    onError: () => {
      toast.error('Failed to reprocess document')
    },
  })

  const handleDelete = async (id: string) => {
    setDeletingId(id)
    await deleteMutation.mutateAsync(id)
    setDeletingId(null)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-500" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <p className="text-gray-500">No documents uploaded yet</p>
      </div>
    )
  }

  return (
    <div className="divide-y">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center space-x-4 flex-1 min-w-0">
            <span className="text-2xl">{getDocumentIcon(doc.file_extension)}</span>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-900 truncate">
                {doc.original_filename}
              </p>
              <div className="flex items-center space-x-3 text-sm text-gray-500">
                <span>{formatBytes(doc.file_size)}</span>
                <span>•</span>
                <span className="capitalize">{doc.document_type.replace('_', ' ')}</span>
                <span>•</span>
                <span>{formatDate(doc.created_at)}</span>
              </div>
              {doc.summary && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-1">
                  {doc.summary}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              {getStatusIcon(doc.processing_status)}
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                  doc.processing_status
                )}`}
              >
                {doc.processing_status}
              </span>
            </div>

            <DropdownMenu.Root>
              <DropdownMenu.Trigger asChild>
                <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  className="min-w-[160px] bg-white rounded-lg shadow-lg border p-1 z-50"
                  sideOffset={5}
                >
                  {doc.processing_status === 'completed' && onViewContent && (
                    <DropdownMenu.Item
                      className="flex items-center px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100 cursor-pointer"
                      onClick={() => onViewContent(doc)}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Content
                    </DropdownMenu.Item>
                  )}
                  <DropdownMenu.Item
                    className="flex items-center px-3 py-2 text-sm text-gray-700 rounded-md hover:bg-gray-100 cursor-pointer"
                    onClick={() => reprocessMutation.mutate(doc.id)}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Reprocess
                  </DropdownMenu.Item>
                  <DropdownMenu.Separator className="h-px bg-gray-200 my-1" />
                  <DropdownMenu.Item
                    className="flex items-center px-3 py-2 text-sm text-red-600 rounded-md hover:bg-red-50 cursor-pointer"
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                  >
                    {deletingId === doc.id ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4 mr-2" />
                    )}
                    Delete
                  </DropdownMenu.Item>
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </div>
        </div>
      ))}
    </div>
  )
}
