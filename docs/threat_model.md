# STRIDE Threat Model – Research Workspace

## 1. Overview

This threat model identifies possible security problems in Research Workspace using STRIDE.

The application has three separate services: Application API, Resource Service, and Processing Service. Since users and services communicate through HTTP, we need to check both user permissions and service permissions.

The analysis focuses on private datasets, authentication, authorization, and communication between services.

## 2. Assets and Trust Boundaries

The main assets are:

- Private research datasets
- Exported CSV files
- User credentials and authentication tokens
- Audit logs
- Service credentials

The main trust boundaries are:

- TB1: User to Application API
- TB2: Application API to Resource Service
- TB3: Application API to Processing Service
- TB4: Processing Service to Resource Service
- TB5: Processing Service to external helper package

These boundaries are described in more detail in `architecture.md`.

## 3. STRIDE Analysis

| STRIDE | Threat | Affected Boundary | Planned Control |
|---|---|---|---|
| Spoofing | An attacker uses a stolen or forged token to access the API | TB1 | Token signature and expiration validation |
| Tampering | A user modifies a dataset belonging to someone else | TB2 | Ownership checks and input validation |
| Repudiation | A user denies creating or exporting a dataset | TB1, TB2 | Audit logging of important actions |
| Information Disclosure | A researcher accesses another researcher's private dataset | TB2 | Resource-level authorization |
| Denial of Service | A user sends excessive export requests | TB3 | Request limits and export size limits |
| Elevation of Privilege | The Processing Service receives broader permissions than required | TB3, TB4 | Dataset-specific, time-limited authorization |

The Resource Service is responsible for enforcing access permissions, even when requests come from another service.

## 4. Planned Vulnerability Investigation

We will investigate four security vulnerabilities during development.

### V1: SQL Injection (CWE-89)

A database query may become vulnerable if user input is inserted directly into SQL.

We will demonstrate the problem using controlled test data and fix it with parameterized queries.

### V2: Path Traversal (CWE-22)

If filenames or export paths are not properly restricted, a user may be able to access files outside the intended directory.

We will test this using local test files and then enforce safe file paths.

### V3: Missing Authorization (CWE-862)

A researcher may be able to access another researcher's dataset if an ownership check is missing.

For example, ali should not be able to read Raman's dataset.

We will demonstrate the missing check and then enforce resource ownership.

### V4: Composition Vulnerability

A separate problem may occur when the Application API starts an export job in the Processing Service.

If the Processing Service receives broad access to the Resource Service, it might be able to request datasets outside the authorized export job.

Unlike V3, this vulnerability concerns how authority is delegated between services.

We will test whether the Processing Service can access a dataset outside its assigned job and then restrict authorization to the specific dataset and operation.

## 5. Security Controls and Tests

| Threat | Control | Planned Test |
|---|---|---|
| Invalid authentication token | Validate token signature and expiration | Reject modified or expired tokens |
| Unauthorized dataset access | Check dataset ownership | ali cannot access Raman's dataset |
| Unsafe SQL input | Use parameterized queries | SQL injection attempts cannot change query behavior |
| Unsafe file paths | Restrict file access to approved directories | Path traversal attempts are rejected |
| Excessive export requests | Limit requests and dataset size | Requests above configured limits are rejected |
| Excessive service permissions | Restrict delegated authorization | Processing Service cannot access datasets outside its job |

## 6. Security Requirements and Gate Decisions

We will use the following rules when testing the application:

- Users must be authenticated before accessing protected resources.
- Unauthorized dataset access must be denied.
- Invalid or expired authorization tokens must be rejected.
- Services must not have unrestricted access to other users' datasets.
- Unexpected dependencies and build artifacts must be rejected.
- Confirmed violations of required security controls must block the release pipeline.

The vulnerable versions will be tested locally. After applying fixes, the security tests must pass before the implementation is considered ready.

## 7. Evidence

We will document the results using automated tests, Git commits, security scan reports, and Jenkins logs.

For each vulnerability, we will keep evidence of the original problem, the implemented fix, and the result after retesting.
