# Nexora AI Support Hub

### Company: **Nexora Technologies**
### Tagline: **Smart Technology. Smarter Support.**

**Nexora AI Support Hub** is a multi-agent AI customer support system using Retrieval-Augmented Generation (RAG) to automate customer support workflows, routing, information retrieval, and query processing.

---

## Phase 1 Status: Project Foundation & Architecture

> [!IMPORTANT]
> **This is Phase 1 — Project Foundation and Architecture only.**
> Core infrastructure, scaffolding, connectivity, database managers, security middlewares, and automated testing are established. Functional AI agents, RAG pipelines, FAISS indices, embeddings, session authentication, and ticketing features are planned for future phases.

---

## 1. Directory Structure

```text
Nexora-AI-Support-Hub/
│
├── frontend/                     # Next.js Frontend Application
│   ├── app/                      # App Router layouts, routes, pages
│   ├── components/               # UI, Layout, Common components
│   ├── lib/                      # Axios API Client with error normalization
│   ├── services/                 # Frontend health check services
│   ├── tests/                    # Frontend test folder
│   └── package.json              # Frontend package definitions
│
├── backend/                      # FastAPI Backend Application
│   ├── api/                      # Routing layers (/api/v1)
│   ├── agents/                   # Agent system placeholder
│   ├── rag/                      # RAG logic placeholder
│   ├── embeddings/               # Embeddings placeholder
│   ├── vectorstore/              # Vector store index placeholder
│   ├── database/                 # Asynchronous MongoDB connection manager
│   ├── core/                     # Configuration, middlewares, error handlers
│   ├── schemas/                  # Pydantic schemas (health, request models)
│   ├── tests/                    # Pytest backend test suite
│   ├── main.py                   # FastAPI main entrance
│   └── requirements.txt          # Python production dependencies
│
├── knowledge_base/               # Knowledge base docs directory (placeholder)
├── datasets/                     # Raw and processed datasets (placeholder)
│   ├── raw/
│   └── processed/
├── evaluation/                   # RAG evaluation scripts placeholder
├── docs/                         # Project documentation and wireframes
│   ├── architecture/
│   ├── wireframes/
│   ├── screenshots/
│   └── report/
├── scripts/                      # Helper maintenance scripts
├── .env.example                  # Root environment configurations template
├── .gitignore                    # Global git ignore configuration
├── LICENSE                       # MIT License
└── README.md                     # This README
```

---

## 2. Technology Stack

* **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Axios, Tailwind CSS, ESLint
* **Backend**: FastAPI, Uvicorn, Pydantic v2, `pydantic-settings`, Motor (Async MongoDB Driver)
* **Database**: MongoDB (asynchronous connectivity configured)
* **Testing**: Pytest, Pytest-Asyncio, HTTPX, Next.js Production Build Validation

---

## 3. Prerequisites

* **Node.js**: v22.x or later
* **npm**: v10.x or later
* **Python**: v3.12.x (installed inside `.venv/`)

---

## 4. Local Setup Steps

Follow these instructions to run the Nexora AI Support Hub locally on **Windows**.

### Step 4.1: Environment Variable Setup

1. Copy the global `.env.example` to a new file named `.env` in the root directory:
   ```powershell
   copy .env.example .env
   ```
2. (Optional) Customize variables if you have a local MongoDB instance. If `MONGODB_URI` remains empty or unconfigured, the application runs gracefully without database connectivity, reporting database status as `not_configured` or `unavailable`.

3. Propagate the environment variables into both the frontend and backend subdirectories:
   ```powershell
   copy .env frontend/.env
   copy .env backend/.env
   ```

---

### Step 4.2: Backend Installation & Setup

1. **Activate the existing Python Virtual Environment (`.venv`)**:
   Open PowerShell and run:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   *(Ensure execution policy allows scripts: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` if needed)*

2. **Install Backend Dependencies**:
   ```powershell
   python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
   ```

3. **Run the Backend Server**:
   ```powershell
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   * The backend server starts on [http://localhost:8000](http://localhost:8000).

---

### Step 4.3: Frontend Installation & Setup

1. **Navigate to the frontend folder**:
   ```powershell
   cd frontend
   ```

2. **Install Node dependencies**:
   ```powershell
   npm install
   ```

3. **Run Frontend in Development Mode**:
   ```powershell
   npm run dev
   ```
   * The frontend client starts on [http://localhost:3000](http://localhost:3000).

---

## 5. Verifying Health & API Docs

* **General Health Status**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
  * Returns JSON showing `status`, `service`, `environment`, and `version`.
* **Database Connection Status**: [http://localhost:8000/api/v1/health/database](http://localhost:8000/api/v1/health/database)
  * Returns database connectivity (`connected`, `unavailable`, or `not_configured`).
* **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
  * Automatically generated endpoint docs.
* **Alternative Redoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 6. Testing, Linting & Building

### Running Backend Tests
Ensure your `.venv` is active and run:
```powershell
python -m pytest backend/tests -v
```
This runs the unit tests verifying general health, unconfigured database states, request ID headers, and normalized validation/HTTP error structures.

### Running Frontend Lints
```powershell
cd frontend
npm run lint
```
Checks for ESLint rules, syntax warnings, and React hooks best practices.

### Building Frontend for Production
```powershell
cd frontend
npm run build
```
Compiles and generates the optimized production build of the Next.js frontend, executing TypeScript checks and static page generations.

---

## 7. Licensing

This project is licensed under the MIT License - see the [LICENSE](file:///c:/Users/Abhishek%20Kulkarni/OneDrive/Documents/Nexora-AI-Support-Hub/LICENSE) file for details.
