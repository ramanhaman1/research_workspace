# Secure Research Workspace

Software Security – Assignment 1

## Project Overview

Secure Research Workspace is a small Python application where researchers can create, view and export private datasets.

The main focus of the project is software security. I developed the application to investigate authentication, authorization, communication between services and vulnerabilities that can occur when separate components work together.

## Technology Stack

- Python 3.12
- FastAPI
- SQLite
- HTTP and JWT authentication
- Pytest
- Bandit
- pip-audit
- Jenkins
- Windows PowerShell

## Architecture

The application consists of three separate HTTP services:

1. **Application API (port 8000):** Handles user authentication and coordinates requests.
2. **Resource Service (port 8001):** Stores datasets and enforces authorization.
3. **Processing Service (port 8002):** Handles CSV exports using a local helper package.

Dataset export involves all three components.

## Windows Setup

The project was developed on Windows using VS Code and PowerShell. Python 3.12 is used for the Jenkins pipeline.

From the project folder, create a virtual environment:

```powershell
py -3.12 -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e packages\csv_helper
```

### Environment configuration

The application uses environment variables for authentication and internal communication:

- `RW_JWT_SECRET`
- `RW_INTERNAL_JWT_SECRET`
- `RW_PROCESSING_API_KEY`
- `RW_ALI_PASSWORD`
- `RW_RAMAN_PASSWORD`
- `RW_ADMIN_PASSWORD`

Configure these before starting the services. Services that use the same internal JWT secret must receive the same value. Use strong local secrets and do not commit passwords or secrets to GitHub.

### Running the services

Start each service in a separate PowerShell terminal, after configuring its required environment variables.

**Resource Service:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.resource_service.main:app --host 127.0.0.1 --port 8001
```

**Processing Service:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.processing_service.main:app --host 127.0.0.1 --port 8002
```

**Application API:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.application_api.main:app --host 127.0.0.1 --port 8000
```

The API documentation can then be opened at `http://127.0.0.1:8000/docs`.

## Running Tests

To run all automated tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

The automated tests cover authentication, authorization, dataset operations, CSV export, internal tokens and security regression tests.

## Vulnerability Testing

Four vulnerabilities were introduced and tested during development:

- **V1:** Missing dataset ownership verification (CWE-862).
- **V2:** Missing dataset row limit validation (CWE-20).
- **V3:** SQL injection through unsafe SQL query construction (CWE-89).
- **V4:** Cross-service authorization bypass caused by missing dataset-bound delegation checks.

The vulnerabilities were demonstrated and subsequently fixed. The before-and-after versions are preserved in the separate Git branch `vulnerability-branch`. The `main` branch contains the corrected implementation and regression tests.

## Continuous Integration

Jenkins is configured as a Multibranch Pipeline. It checks GitHub periodically for new commits and pull requests.

The pipeline performs:

- Automated tests using Pytest.
- Static security analysis using Bandit.
- Dependency vulnerability analysis using pip-audit.
- Archiving of test and security reports.

The pipeline has been tested for pushes to `main`, pull requests and merging changes into `main`.

## Documentation

The `docs` folder contains project planning and security design documentation, including the initial SSDLC plan.

The main assignment report describes the architecture, threat modelling, secure design principles, vulnerabilities, testing and CI results.