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

Install the dependencies from `requirements.txt` (this also installs the local CSV helper package):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Initialize the database

Before starting the services for the first time, create the local SQLite tables:

```powershell
.\.venv\Scripts\python.exe -m services.resource_service.database
```

This creates the dataset, export and audit-log tables in `data/research_workspace.db`. The local `ali`, `Raman` and `admin` accounts are configured in the application using the passwords below; they do not require database seeding.

### Environment configuration

The application uses these environment variables:

- `RW_JWT_SECRET`: signs the user login tokens (at least 32 characters).
- `RW_INTERNAL_JWT_SECRET`: signs internal service tokens (at least 32 characters).
- `RW_PROCESSING_API_KEY`: authorizes calls to Processing Service (at least 32 characters).
- `RW_ALI_PASSWORD`, `RW_RAMAN_PASSWORD` and `RW_ADMIN_PASSWORD`: passwords for the local test accounts.

Set the variables in the PowerShell terminal **before** starting the corresponding service. Replace all `REPLACE_...` values with strong local credentials. The internal JWT secret and processing API key must match wherever they are used. Do not commit real secrets or passwords.

### Running the services

Open **three PowerShell terminals** in the project folder. Start each service with the following commands. Keep each terminal open while the service is running.

**Terminal 1 – Resource Service (port 8001):**

```powershell
$env:RW_INTERNAL_JWT_SECRET = "REPLACE_WITH_SHARED_RANDOM_INTERNAL_SECRET_AT_LEAST_32_CHARS"
.\.venv\Scripts\python.exe -m uvicorn services.resource_service.main:app --host 127.0.0.1 --port 8001
```

**Terminal 2 – Processing Service (port 8002):**

```powershell
$env:RW_PROCESSING_API_KEY = "REPLACE_WITH_SHARED_RANDOM_PROCESSING_KEY_AT_LEAST_32_CHARS"
.\.venv\Scripts\python.exe -m uvicorn services.processing_service.main:app --host 127.0.0.1 --port 8002
```

**Terminal 3 – Application API (port 8000):**

```powershell
$env:RW_JWT_SECRET = "REPLACE_WITH_RANDOM_LOGIN_SECRET_AT_LEAST_32_CHARS"
$env:RW_INTERNAL_JWT_SECRET = "REPLACE_WITH_SHARED_RANDOM_INTERNAL_SECRET_AT_LEAST_32_CHARS"
$env:RW_PROCESSING_API_KEY = "REPLACE_WITH_SHARED_RANDOM_PROCESSING_KEY_AT_LEAST_32_CHARS"
$env:RW_ALI_PASSWORD = "REPLACE_WITH_ALI_PASSWORD"
$env:RW_RAMAN_PASSWORD = "REPLACE_WITH_RAMAN_PASSWORD"
$env:RW_ADMIN_PASSWORD = "REPLACE_WITH_ADMIN_PASSWORD"
.\.venv\Scripts\python.exe -m uvicorn services.application_api.main:app --host 127.0.0.1 --port 8000
```

Once the services are running, their health endpoints are available at `http://127.0.0.1:8000/health`, `http://127.0.0.1:8001/health` and `http://127.0.0.1:8002/health`. The Application API's Swagger documentation is at `http://127.0.0.1:8000/docs`.

## Running Tests

To run all automated tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

The automated tests cover authentication, authorization, dataset operations, CSV export, internal tokens and security regression tests. Test fixtures use their own temporary test database.

### End-to-end export check

With all three services running, open a **fourth PowerShell terminal** in the project folder. Set the same three user passwords used by the Application API, then run:

```powershell
$env:RW_ALI_PASSWORD = "REPLACE_WITH_ALI_PASSWORD"
$env:RW_RAMAN_PASSWORD = "REPLACE_WITH_RAMAN_PASSWORD"
$env:RW_ADMIN_PASSWORD = "REPLACE_WITH_ADMIN_PASSWORD"
.\.venv\Scripts\python.exe scripts\check_export_e2e.py
```

This script checks a successful CSV export through the three services and verifies that cross-user, unauthenticated, admin and invalid-token export requests are rejected.

## Vulnerability Testing

Four vulnerabilities were introduced and tested during development:

- **V1:** Missing dataset ownership verification (CWE-862).
- **V2:** Missing dataset row limit validation (CWE-20).
- **V3:** SQL injection through unsafe SQL query construction (CWE-89).
- **V4:** Cross-service authorization bypass caused by missing dataset-bound delegation checks.

The vulnerabilities were demonstrated and subsequently fixed. The before-and-after versions are preserved in the separate Git branch `vulnerability-branch`. The `main` branch contains the corrected implementation and regression tests.

## Continuous Integration

Jenkins is configured as a Multibranch Pipeline. It checks GitHub for changes by periodically scanning the repository (rather than using a GitHub webhook).

The pipeline performs:

- Automated tests using Pytest.
- Static security analysis using Bandit.
- Dependency vulnerability analysis using pip-audit.
- Archiving of test and security reports.

The pipeline has been tested for pushes to `main`, pull requests and merging changes into `main`.

## Documentation

The `docs` folder contains project planning and security design documentation, including the initial SSDLC plan.

The main assignment report describes the architecture, threat modelling, secure design principles, vulnerabilities, testing and CI results.
