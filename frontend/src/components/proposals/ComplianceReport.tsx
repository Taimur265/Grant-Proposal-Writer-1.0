'use client'

import { CheckCircle, XCircle, AlertTriangle, TrendingUp } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import type { ComplianceCheck } from '@/types'
import { cn } from '@/lib/utils'

interface ComplianceReportProps {
  compliance: ComplianceCheck
  onClose: () => void
}

export default function ComplianceReport({ compliance, onClose }: ComplianceReportProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-100'
    if (score >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Overall Score */}
      <div className="text-center">
        <div
          className={cn(
            'inline-flex items-center justify-center w-32 h-32 rounded-full',
            getScoreBg(compliance.overall_score)
          )}
        >
          <div>
            <p className={cn('text-4xl font-bold', getScoreColor(compliance.overall_score))}>
              {compliance.overall_score?.toFixed(0) || 0}%
            </p>
            <p className="text-sm text-gray-500">Compliance Score</p>
          </div>
        </div>
      </div>

      {/* Section Scores */}
      {compliance.section_scores && Object.keys(compliance.section_scores).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Section Scores</h3>
          <div className="space-y-2">
            {Object.entries(compliance.section_scores).map(([section, score]) => (
              <div key={section} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-700">{section}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full',
                        score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      )}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                  <span className={cn('text-sm font-medium', getScoreColor(score))}>
                    {score.toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing Requirements */}
      {compliance.missing_requirements && compliance.missing_requirements.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <XCircle className="w-5 h-5 text-red-500 mr-2" />
            Missing Requirements
          </h3>
          <ul className="space-y-2">
            {compliance.missing_requirements.map((req, index) => (
              <li key={index} className="flex items-start space-x-2 p-2 bg-red-50 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-red-700">{req}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {compliance.suggestions && compliance.suggestions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <TrendingUp className="w-5 h-5 text-blue-500 mr-2" />
            Improvement Suggestions
          </h3>
          <ul className="space-y-2">
            {compliance.suggestions.map((suggestion, index) => (
              <li key={index} className="flex items-start space-x-2 p-2 bg-blue-50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-blue-700">{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Word Count Status */}
      {compliance.word_count_status && Object.keys(compliance.word_count_status).length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Word Count Status</h3>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(compliance.word_count_status).map(([section, status]: [string, any]) => (
              <div key={section} className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-900">{section}</p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-500">
                    {status.current} / {status.max} words
                  </span>
                  <Badge
                    variant={
                      status.status === 'ok' ? 'success' :
                      status.status === 'over' ? 'danger' : 'warning'
                    }
                  >
                    {status.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
