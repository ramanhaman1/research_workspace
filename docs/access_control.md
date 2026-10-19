# Access Control Matrix

## 1. Overview

Research Workspace has two user roles, Researcher and Administrator.

Researchers can create, view, and export their own datasets. The administrator can view audit logs but does not automatically have access to private datasets.

Permissions will be checked by the Resource Service, including when requests come from other services.

## 2. User Permissions

| Action | Researcher | Administrator |
|---|---|---|
| Log in | Yes | Yes |
| Create a dataset | Yes | No |
| View own datasets | Yes | No |
| View another user's datasets | No | No |
| Export own datasets | Yes | No |
| Export another user's datasets | No | No |
| Download own exports | Yes | No |
| View audit logs | No | Yes |

Researchers can only access datasets they own. The administrator has separate permissions for viewing audit logs.

## 3. Service Permissions

The three services have different responsibilities and permissions.

| Action | Application API | Resource Service | Processing Service |
|---|---|---|---|
| Authenticate users | Yes | No | No |
| Coordinate user requests | Yes | No | No |
| Store datasets | No | Yes | No |
| Check dataset permissions | Request-level checks | Yes | No |
| Read dataset contents | Through authorized requests | Yes | Only for authorized export jobs |
| Generate CSV files | No | No | Yes |
| Store export results | No | Yes | Through authorized requests |
| Access audit logs | Forward admin requests | Enforce admin access | No |

The Application API does not have unrestricted access to datasets. It must use the Resource Service to access protected resources.

The Processing Service does not access the database directly. It requests data through the Resource Service.

## 4. Authorization Rules

The following rules will apply:

- A user must be authenticated before accessing protected resources.
- Researchers can only access datasets they own.
- The administrator can view audit logs.
- The Resource Service must check ownership and permissions before returning datasets or export results.
- The Processing Service can only access data required for an authorized export job.
- Requests between services must be authenticated and carry appropriate authorization.
- Access is denied by default unless permission is explicitly granted.

## 5. Authorization Between Services

We plan to use signed, timelimited tokens for service-to-service authorization.

For an export job, the authorization information should identify:

- The user requesting the export.
- The service receiving the request.
- The dataset being accessed.
- The permitted operation.
- The token's expiration time.

The Resource Service will verify the calling service, token validity, requested operation, and dataset ownership before allowing access.

A service being authenticated does not automatically mean it is authorized to access every dataset.

## 6. Authorization Test Cases

We will use the predefined accounts `ali`, `Raman`, and `admin` to test access control.

| Test | Action | Expected Result |
|---|---|---|
| AC1 | ali accesses his own dataset | Allowed |
| AC2 | ali accesses Raman's dataset | Denied |
| AC3 | Raman exports his own dataset | Allowed |
| AC4 | Raman exports ali's dataset | Denied |
| AC5 | ali requests audit logs | Denied |
| AC6 | admin requests audit logs | Allowed |
| AC7 | Processing Service requests a dataset outside its authorized job | Denied |
| AC8 | Unauthenticated user requests a private dataset | Denied |

For protected HTTP endpoints, unauthenticated requests should normally return 401, while authenticated users without permission should receive 403.

These tests describe the expected behavior of the secure implementation. During vulnerability testing, we will intentionally introduce selected weaknesses, demonstrate them, and verify that the fixes restore the expected behavior.
