'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, X, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { documentsApi } from '@/lib/api'
import { formatBytes, getDocumentIcon } from '@/lib/utils'
import { cn } from '@/lib/utils'

interface DocumentUploaderProps {
  projectId: string
  category: 'guidelines' | 'beneficiary'
  documentTypes: Array<{ value: string; label: string }>
  onUploadComplete?: () => void
}

interface UploadingFile {
  file: File
  progress: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
  documentType?: string
}

export default function DocumentUploader({
  projectId,
  category,
  documentTypes,
  onUploadComplete,
}: DocumentUploaderProps) {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])
  const [selectedType, setSelectedType] = useState(documentTypes[0]?.value || 'other')
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: async ({ file, documentType }: { file: File; documentType: string }) => {
      return documentsApi.upload(file, projectId, category, documentType)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const newFiles: UploadingFile[] = acceptedFiles.map((file) => ({
        file,
        progress: 0,
        status: 'uploading' as const,
        documentType: selectedType,
      }))

      setUploadingFiles((prev) => [...prev, ...newFiles])

      for (let i = 0; i < acceptedFiles.length; i++) {
        const file = acceptedFiles[i]
        const fileIndex = uploadingFiles.length + i

        try {
          await uploadMutation.mutateAsync({ file, documentType: selectedType })

          setUploadingFiles((prev) =>
            prev.map((f, idx) =>
              idx === fileIndex ? { ...f, status: 'completed', progress: 100 } : f
            )
          )

          toast.success(`${file.name} uploaded successfully`)
        } catch (error: any) {
          setUploadingFiles((prev) =>
            prev.map((f, idx) =>
              idx === fileIndex
                ? { ...f, status: 'error', error: error.response?.data?.detail || 'Upload failed' }
                : f
            )
          )
          toast.error(`Failed to upload ${file.name}`)
        }
      }

      onUploadComplete?.()
    },
    [projectId, category, selectedType, uploadMutation, onUploadComplete]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'application/rtf': ['.rtf'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  const removeFile = (index: number) => {
    setUploadingFiles((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-4">
      {/* Document type selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Document Type
        </label>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="input max-w-xs"
        >
          {documentTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          'dropzone',
          isDragActive && 'active'
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center">
          <Upload className="w-12 h-12 text-gray-400 mb-4" />
          {isDragActive ? (
            <p className="text-primary-600 font-medium">Drop the files here...</p>
          ) : (
            <>
              <p className="text-gray-600 font-medium">
                Drag & drop files here, or click to select
              </p>
              <p className="text-sm text-gray-500 mt-1">
                PDF, DOCX, XLSX, PPTX, TXT (max 50MB)
              </p>
            </>
          )}
        </div>
      </div>

      {/* Upload progress */}
      {uploadingFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Uploaded Files</h4>
          <div className="space-y-2">
            {uploadingFiles.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <span className="text-xl">{getDocumentIcon(`.${item.file.name.split('.').pop()}`)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatBytes(item.file.size)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {item.status === 'uploading' && (
                    <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
                  )}
                  {item.status === 'completed' && (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                  {item.status === 'error' && (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  )}
                  <button
                    onClick={() => removeFile(index)}
                    className="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
