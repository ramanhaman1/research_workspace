# Initial SSDLC Plan – Research Workspace

## 1. Project Overview

Research Workspace is a small application where users can create, view, and export private research datasets.

The application will have three separate services that communicate through HTTP. The main focus is to investigate security vulnerabilities, especially problems related to authorization and communication between services.

We will first demonstrate selected vulnerabilities in a controlled environment, then fix them and test whether the fixes work.

## 2. Scope and Requirements

The application will include the following features:

- FR1: Users can log in to the application.
- FR2: Users can create private datasets.
- FR3: Users can view their own datasets.
- FR4: Users can export their datasets as CSV files.
- FR5: An administrator can view audit logs.

We will use three predefined accounts and synthetic data. We do not plan to implement a graphical interface or deploy the application publicly.

The system should also validate user input, protect private data, and support automated testing.

## 3. System Architecture

The system will consist of three services:

1. **Application API:** Handles user authentication and incoming requests.
2. **Resource Service:** Stores datasets and export results, and checks whether users have permission to access them.
3. **Processing Service:** Handles dataset exports using a separate CSV helper package.

The services will run as separate processes and communicate through HTTP requests.

An important part of the project is making sure that services cannot access data simply because another service has sent a request. Each service should only have the permissions needed for its tasks.

## 4. Users and Protected Resources

We will use three accounts:

- **ali:** Researcher
- **Raman:** Researcher
- **admin:** Administrator

Researchers should only be able to create, view, and export their own datasets. The administrator will have access to audit logs but will not automatically have access to everyone's private datasets.

The main resources we need to protect are private datasets, exported files, authentication tokens, audit logs, and service credentials.

## 5. Security Principles

We plan to follow three security principles:

- **Least Privilege:** Users and services should only have access to what they need.
- **Complete Mediation:** Permissions should be checked whenever someone tries to access a protected resource.
- **Fail-Safe Defaults:** Access should be denied unless it is explicitly allowed.

The tesource service will be responsible for checking dataset permissions, including requests coming from other services.

We will use established authentication libraries rather than implementing our own cryptography.

## 6. Vulnerabilities to Investigate

We plan to introduce and investigate four vulnerabilities:

1. **CWE-89 – SQL Injection:** Unsafe handling of input in database queries.
2. **CWE-22 – Path Traversal:** Using file paths without properly restricting which files can be accessed.
3. **CWE-862 – Missing Authorization:** A user being able to access another user's dataset because a permission check is missing.
4. **Composition Vulnerability:** A service being able to access more data than intended because permissions are not properly restricted between services.

For each vulnerability, we will explain the problem, demonstrate it through testing, implement a fix, and test again.

The vulnerable version will only be used in our local test environment.

## 7. SSDLC Phases

### Phase 1: Requirements

Before implementation, we will define the system requirements, identify protected resources, and create an architecture diagram.

We will also prepare an access-control matrix and use STRIDE to identify possible threats.

**Gate:** The architecture, access rules, and planned security controls must be reviewed before development begins.

### Phase 2: Implementation and Build

We will implement the three services in Python, including authentication, authorization, dataset management, and CSV export.

The CSV helper will be a separate installable package. We will also track and pin dependencies to make builds reproducible.

**Gate:** The build should reject dependencies or artifacts that have not been approved.

### Phase 3: Testing

We will test the application's main features and check that users cannot access resources belonging to others.

We will also test the four vulnerabilities before and after fixing them.

We plan to use Pytest for automated tests, Bandit for static security analysis, and a dependency scanner for known vulnerable packages.

**Gate:** Functional and authorization tests must pass, and confirmed security problems must be fixed before release.

### Phase 4: Release and Operation

We will configure a Jenkins pipeline to run on pushes and pull requests. It will validate the build, run security analysis, start a fresh test environment, execute the tests, and save the results.

The pipeline should fail if required tests or security checks fail.

We do not plan to deploy the application publicly. However, the final report will discuss what would be needed for production, such as HTTPS, secret management, logging, and restricted network access.

## 8. Documentation and Evidence

We will keep track of our security decisions and test results throughout the project.

For example:

- **Asset:** Private research datasets
- **Threat:** One researcher accesses another researcher's data
- **Control:** Check dataset ownership before allowing access
- **Implementation:** Authorization checks in the Resource Service
- **Test:** ali tries to access Raman's dataset
- **Expected result:** Access is denied
- **Gate:** The authorization test must pass

We will use Git commits, test results, security reports, and Jenkins logs as evidence in the final report.