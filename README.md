# Grant Proposal Writer

An AI-powered grant proposal generation system that helps organizations create compelling, compliant grant proposals based on uploaded guidelines and beneficiary information.

## Features

### Core Functionality
- **Document Upload & Processing**: Support for PDF, DOCX, XLSX, PPTX, TXT, and more
- **Two-Section Document Organization**:
  - **Guidelines Section**: Upload RFPs, guidelines, terms & conditions, eligibility criteria, evaluation criteria
  - **Beneficiary Section**: Upload organization profiles, financial statements, project descriptions, team CVs
- **AI-Powered Proposal Generation**: Generate complete grant proposals using OpenAI GPT-4 or Anthropic Claude
- **Section-by-Section Editing**: Edit and regenerate individual proposal sections
- **Compliance Checking**: AI-powered compliance verification against guidelines
- **Multi-Format Export**: Export proposals to DOCX, PDF, HTML, Markdown, or plain text

### User Features
- User authentication and authorization
- Project management (create, update, delete)
- Document management with automatic text extraction
- Proposal versioning and status tracking
- AI-generated summaries and key points extraction

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM with async support
- **OpenAI/Anthropic** - AI providers for proposal generation
- **pdfplumber/python-docx** - Document processing

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **TanStack Query** - Data fetching
- **Zustand** - State management
- **Radix UI** - Accessible components

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key and/or Anthropic API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Grant-Proposal-Writer-1.0
```

2. **Set up environment variables**
```bash
# Copy the example env file
cp backend/.env.example backend/.env

# Edit the .env file and add your API keys
# Required: At least one AI provider key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs

### Manual Installation (Development)

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Start PostgreSQL (or use Docker)
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=grant_writer -p 5432:5432 postgres:15-alpine

# Run the backend
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Usage Guide

### 1. Create a Project
- Log in to the application
- Click "New Project" on the dashboard
- Enter project details (name, funding agency, deadline, etc.)

### 2. Upload Guidelines
Navigate to your project and upload documents in the **Guidelines & Requirements** section:
- **Guidelines**: General grant guidelines
- **Terms & Conditions**: Legal terms and conditions
- **TOR (Terms of Reference)**: Detailed requirements
- **RFP (Request for Proposal)**: Full RFP documents
- **Eligibility Criteria**: Who can apply
- **Evaluation Criteria**: How proposals will be scored
- **Budget Template**: Budget format requirements

### 3. Upload Beneficiary Information
Upload documents in the **Beneficiary Information** section:
- **Organization Profile**: About your organization
- **Registration Documents**: Legal registration docs
- **Financial Statements**: Annual reports, audits
- **Project Description**: Detailed project plan
- **Beneficiary Data**: Data about target beneficiaries
- **Impact Assessment**: Expected project impact
- **Team CVs**: Resumes of key personnel
- **Past Performance**: Previous project achievements
- **Letters of Support**: Supporting letters

### 4. Generate Proposal
- Click "Generate Proposal"
- Configure generation options:
  - Proposal title
  - Writing tone (Professional, Academic, etc.)
  - AI provider (OpenAI or Anthropic)
  - Custom instructions (optional)
- Wait for AI to generate the proposal

### 5. Review and Edit
- Review the generated proposal
- Edit individual sections as needed
- Regenerate sections with feedback
- Check compliance against guidelines

### 6. Export
Export your proposal in your preferred format:
- DOCX (Microsoft Word)
- PDF (coming soon)
- HTML
- Markdown
- Plain text

## API Documentation

### Authentication
```
POST /api/v1/auth/register - Register new user
POST /api/v1/auth/login - Login (returns JWT)
GET /api/v1/auth/me - Get current user
PATCH /api/v1/auth/me - Update profile
```

### Projects
```
GET /api/v1/projects/ - List projects
POST /api/v1/projects/ - Create project
GET /api/v1/projects/{id} - Get project
PATCH /api/v1/projects/{id} - Update project
DELETE /api/v1/projects/{id} - Delete project
GET /api/v1/projects/{id}/stats - Get project statistics
```

### Documents
```
POST /api/v1/documents/upload - Upload document
POST /api/v1/documents/upload/batch - Upload multiple documents
GET /api/v1/documents/ - List documents (filter by project/category)
GET /api/v1/documents/{id} - Get document
GET /api/v1/documents/{id}/content - Get extracted content
PATCH /api/v1/documents/{id} - Update document metadata
DELETE /api/v1/documents/{id} - Delete document
POST /api/v1/documents/{id}/reprocess - Reprocess document
```

### Proposals
```
POST /api/v1/proposals/generate - Generate new proposal
GET /api/v1/proposals/ - List proposals
GET /api/v1/proposals/{id} - Get proposal with sections
PATCH /api/v1/proposals/{id} - Update proposal
DELETE /api/v1/proposals/{id} - Delete proposal
PATCH /api/v1/proposals/{id}/sections/{section_id} - Update section
POST /api/v1/proposals/{id}/sections/{section_id}/regenerate - Regenerate section
POST /api/v1/proposals/{id}/check-compliance - Check compliance
POST /api/v1/proposals/{id}/export - Export proposal
```

## Project Structure

```
Grant-Proposal-Writer-1.0/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # Database setup
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   └── proposal.py
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API routes
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── documents.py
│   │   │   └── proposals.py
│   │   └── services/            # Business logic
│   │       ├── auth.py
│   │       ├── document_processor.py
│   │       ├── ai_service.py
│   │       ├── proposal_generator.py
│   │       └── storage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── dashboard/
│   │   │       ├── projects/
│   │   │       └── settings/
│   │   ├── components/          # React components
│   │   │   ├── layout/
│   │   │   ├── documents/
│   │   │   └── proposals/
│   │   ├── lib/                 # Utilities
│   │   │   ├── api.ts
│   │   │   └── utils.ts
│   │   └── store/               # State management
│   ├── package.json
│   ├── Dockerfile
│   └── tailwind.config.ts
├── docker-compose.yml
└── README.md
```

## Configuration

### Environment Variables

#### Backend (.env)
```env
# Application
APP_NAME="Grant Proposal Writer"
DEBUG=true
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/grant_writer

# JWT
JWT_SECRET_KEY=jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Providers (at least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
DEFAULT_AI_PROVIDER=openai

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB
UPLOAD_DIR=./uploads

# Storage (optional)
STORAGE_TYPE=local  # or "s3", "minio"
```

## Security Considerations

- All API endpoints require JWT authentication (except login/register)
- Passwords are hashed using bcrypt
- File uploads are validated for type and size
- API keys are stored server-side only
- CORS is configured for specific origins

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and feature requests, please open a GitHub issue.
