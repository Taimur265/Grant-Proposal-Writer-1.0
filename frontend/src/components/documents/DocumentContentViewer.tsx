'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, FileText, List, Sparkles, Loader2, Copy, Check } from 'lucide-react'
import { documentsApi } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import * as Tabs from '@radix-ui/react-tabs'
import { cn } from '@/lib/utils'
import toast from 'react-hot-toast'

interface DocumentContentViewerProps {
  documentId: string
  documentName: string
  onClose: () => void
}

export default function DocumentContentViewer({
  documentId,
  documentName,
  onClose,
}: DocumentContentViewerProps) {
  const [activeTab, setActiveTab] = useState('summary')
  const [copied, setCopied] = useState(false)

  const { data: content, isLoading, error } = useQuery({
    queryKey: ['document-content', documentId],
    queryFn: () => documentsApi.getContent(documentId),
  })

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 flex flex-col items-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
          <p className="mt-4 text-gray-600">Loading document content...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-xl p-8 max-w-md">
          <h3 className="text-lg font-semibold text-red-600">Error Loading Content</h3>
          <p className="text-gray-600 mt-2">
            Could not load document content. The document may still be processing.
          </p>
          <Button variant="outline" onClick={onClose} className="mt-4">
            Close
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900 truncate max-w-md">
              {documentName}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
          <Tabs.List className="flex border-b px-4">
            <Tabs.Trigger
              value="summary"
              className={cn(
                'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeTab === 'summary'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <Sparkles className="w-4 h-4 inline mr-2" />
              AI Summary
            </Tabs.Trigger>
            <Tabs.Trigger
              value="keypoints"
              className={cn(
                'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeTab === 'keypoints'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <List className="w-4 h-4 inline mr-2" />
              Key Points
            </Tabs.Trigger>
            <Tabs.Trigger
              value="fulltext"
              className={cn(
                'px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
                activeTab === 'fulltext'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Full Text
            </Tabs.Trigger>
          </Tabs.List>

          <div className="flex-1 overflow-y-auto">
            <Tabs.Content value="summary" className="p-6">
              {content?.summary ? (
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">AI-Generated Summary</h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(content.summary || '')}
                      leftIcon={copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    >
                      {copied ? 'Copied' : 'Copy'}
                    </Button>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-700 whitespace-pre-wrap">{content.summary}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Sparkles className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">No AI summary available for this document</p>
                </div>
              )}
            </Tabs.Content>

            <Tabs.Content value="keypoints" className="p-6">
              {content?.key_points && content.key_points.length > 0 ? (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Extracted Key Points
                  </h3>
                  <ul className="space-y-3">
                    {content.key_points.map((point: string, index: number) => (
                      <li
                        key={index}
                        className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                      >
                        <Badge variant="primary" className="mt-0.5">
                          {index + 1}
                        </Badge>
                        <span className="text-gray-700">{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="text-center py-8">
                  <List className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">No key points extracted from this document</p>
                </div>
              )}
            </Tabs.Content>

            <Tabs.Content value="fulltext" className="p-6">
              {content?.extracted_text ? (
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Extracted Text
                      <span className="text-sm font-normal text-gray-500 ml-2">
                        ({content.extracted_text.split(/\s+/).length.toLocaleString()} words)
                      </span>
                    </h3>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(content.extracted_text || '')}
                      leftIcon={copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    >
                      {copied ? 'Copied' : 'Copy'}
                    </Button>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                      {content.extracted_text}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">No text extracted from this document</p>
                </div>
              )}

              {content?.extracted_metadata && Object.keys(content.extracted_metadata).length > 0 && (
                <div className="mt-6">
                  <h4 className="text-md font-semibold text-gray-900 mb-3">Document Metadata</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <dl className="grid grid-cols-2 gap-4">
                      {Object.entries(content.extracted_metadata).map(([key, value]) => (
                        <div key={key}>
                          <dt className="text-xs text-gray-500 uppercase">{key.replace(/_/g, ' ')}</dt>
                          <dd className="text-sm text-gray-900">{String(value)}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                </div>
              )}
            </Tabs.Content>
          </div>
        </Tabs.Root>

        {/* Footer */}
        <div className="p-4 border-t flex justify-end">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
