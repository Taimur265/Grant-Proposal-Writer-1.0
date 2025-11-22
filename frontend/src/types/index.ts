// User types
export interface User {
  id: string
  email: string
  full_name?: string
  organization?: string
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login?: string
}

// Project types
export type ProjectStatus = 'draft' | 'in_progress' | 'review' | 'submitted' | 'approved' | 'rejected'

export interface Project {
  id: string
  name: string
  description?: string
  grant_type?: string
  funding_agency?: string
  deadline?: string
  target_amount?: string
  status: ProjectStatus
  owner_id: string
  created_at: string
  updated_at: string
  document_count?: number
  proposal_count?: number
}

export interface ProjectStats {
  total_documents: number
  guidelines_documents: number
  beneficiary_documents: number
  total_proposals: number
  latest_proposal_status?: string
}

// Document types
export type DocumentCategory = 'guidelines' | 'beneficiary' | 'generated' | 'reference'

export type DocumentType =
  | 'guidelines' | 'terms_conditions' | 'tor' | 'rfp'
  | 'eligibility' | 'evaluation_criteria' | 'budget_template'
  | 'organization_profile' | 'registration_docs' | 'financial_statements'
  | 'project_description' | 'beneficiary_data' | 'impact_assessment'
  | 'team_cvs' | 'past_performance' | 'letters_of_support' | 'other'

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface Document {
  id: string
  filename: string
  original_filename: string
  file_path: string
  file_size: number
  mime_type: string
  file_extension: string
  document_type: DocumentType
  category: DocumentCategory
  extracted_text?: string
  extracted_metadata?: Record<string, any>
  summary?: string
  key_points?: string[]
  processing_status: ProcessingStatus
  processing_error?: string
  project_id: string
  uploaded_by: string
  created_at: string
  updated_at: string
  processed_at?: string
}

export interface DocumentContent {
  id: string
  extracted_text?: string
  summary?: string
  key_points?: string[]
  extracted_metadata?: Record<string, any>
}

// Proposal types
export type ProposalStatus = 'generating' | 'draft' | 'in_review' | 'approved' | 'final' | 'submitted'

export interface ProposalSection {
  id: string
  section_name: string
  section_order: number
  content?: string
  word_count?: number
  max_words?: number
  is_required: boolean
  is_complete: boolean
  ai_suggestions?: string[]
  compliance_notes?: string
  created_at: string
  updated_at: string
}

export interface Proposal {
  id: string
  title: string
  version: number
  status: ProposalStatus
  executive_summary?: string
  full_content?: string
  structured_content?: Record<string, any>
  word_count?: number
  compliance_score?: number
  ai_model_used?: string
  generation_params?: Record<string, any>
  last_exported_at?: string
  export_format?: string
  project_id: string
  created_by: string
  created_at: string
  updated_at: string
  sections: ProposalSection[]
}

export interface ProposalFeedback {
  id: string
  proposal_id: string
  section_id?: string
  feedback_type: 'comment' | 'suggestion' | 'approval' | 'rejection'
  content: string
  is_resolved: boolean
  author_id: string
  created_at: string
  resolved_at?: string
}

export interface ComplianceCheck {
  overall_score: number
  section_scores: Record<string, number>
  missing_requirements: string[]
  suggestions: string[]
  word_count_status: Record<string, { current: number; max: number; status: string }>
}

// API response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages?: number
}

export interface DocumentTypesResponse {
  categories: {
    guidelines: {
      name: string
      description: string
      types: Array<{ value: string; label: string }>
    }
    beneficiary: {
      name: string
      description: string
      types: Array<{ value: string; label: string }>
    }
  }
  allowed_extensions: string[]
  max_file_size_mb: number
}

// Form types
export interface GenerateProposalForm {
  project_id: string
  title?: string
  ai_provider?: 'openai' | 'anthropic'
  model?: string
  tone?: 'professional' | 'academic' | 'conversational' | 'formal'
  focus_areas?: string[]
  custom_instructions?: string
  include_sections?: string[]
  max_words_per_section?: number
}

export interface ExportProposalForm {
  format: 'docx' | 'pdf' | 'txt' | 'html' | 'md'
  include_metadata?: boolean
  include_comments?: boolean
  template_id?: string
}
