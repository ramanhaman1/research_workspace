
import csv
import io
import os

import httpx

BASE_URL = "http://127.0.0.1:8000"


def check_status(response: httpx.Response, expected: int) -> None:
    assert response.status_code == expected, (
        f"Expected HTTP {expected}, got HTTP {response.status_code}: "
        f"{response.text[:300]}"
    )


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    with httpx.Client(
        base_url=BASE_URL,
        timeout=15.0,
        trust_env=False,
    ) as client:

        def login(username: str) -> str:
            password = os.environ[f"RW_{username.upper()}_PASSWORD"]
            response = client.post(
                "/login",
                json={"username": username, "password": password},
            )
            check_status(response, 200)
            return response.json()["access_token"]

        
        ali_token = login("ali")
        response = client.post(
            "/datasets",
            json={
                "name": "E2E Student Survey",
                "rows": [
                    {"participant": 1, "score": 80},
                    {"participant": 2, "score": 92},
                ],
            },
            headers=auth_header(ali_token),
        )
        check_status(response, 201)
        dataset_id = response.json()["id"]

        response = client.get(
            f"/datasets/{dataset_id}/export",
            headers=auth_header(ali_token),
        )
        check_status(response, 200)
        assert response.headers.get("content-type", "").startswith("text/csv"), (
            f"Expected text/csv, got {response.headers.get('content-type')!r}"
        )
        rows = list(csv.reader(io.StringIO(response.text)))
        assert rows == [
            ["participant", "score"],
            ["1", "80"],
            ["2", "92"],
        ], f"Unexpected CSV content: {rows!r}"
        print("PASS: Ali can export his own dataset")

        
        raman_token = login("Raman")
        response = client.get(
            f"/datasets/{dataset_id}/export",
            headers=auth_header(raman_token),
        )
        check_status(response, 404)
        print("PASS: Cross-user export denied")

        
        response = client.get(f"/datasets/{dataset_id}/export")
        check_status(response, 401)
        print("PASS: Export without authentication denied")

        
        admin_token = login("admin")
        response = client.get(
            f"/datasets/{dataset_id}/export",
            headers=auth_header(admin_token),
        )
        check_status(response, 403)
        print("PASS: Admin export denied")

        
        response = client.get(
            f"/datasets/{dataset_id}/export",
            headers=auth_header("invalid-token"),
        )
        check_status(response, 401)
        print("PASS: Invalid authentication token denied")

    print("\nAll 5 end-to-end checks passed!")


if __name__ == "__main__":
    main()
