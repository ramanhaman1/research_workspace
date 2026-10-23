
# Secure Research Workspace

Assignment I

## Project Overview

Secure Research Workspace is a small application that allows researchers to create, view, and export private datasets.

The project focuses on authentication, authorization, secure component communication, vulnerability analysis and secure software development practices.

## Technology Stack

- Python
- FastAPI
- SQLite
- Docker
- Pytest
- Bandit
- Jenkins

## Architecture

The application consists of three separate services:

1. Application API - Authentication and request coordination.
2. Resource Service - Dataset storage and authorization.
3. Processing Service - Dataset export using an external helper package.

## Documentation

See `docs/initial_ssdlc_plan.md` for the initial Secure Software Development Lifecycle plan.

## Status

Planning phase. Implementation has not started.

## CI Verification

The Jenkins pipeline automatically checks the project for changes
and runs the configured tests and security checks.
