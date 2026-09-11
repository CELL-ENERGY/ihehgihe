import requests
import json
import os

BASE_URL = "http://127.0.0.1:8001"

def run_tests():
    print("=== STARTING FULL ENDPOINT TESTS ===")
    
    # 1. Health check
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}
    print("[PASS] GET /health")

    # 2. Service status
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    assert r.json() == {"status": "online", "service": "Jan Nidhi Spotter Backend"}
    print("[PASS] GET /")

    # 3. Create verification without image
    data = {
        "work_id": "WB/2025/0553",
        "observation": "NO_WORK_FOUND",
        "comment": "No construction found at the reported location.",
        "latitude": "22.5726",
        "longitude": "88.3639",
        "citizen_name": "Citizen Rohit"
    }
    r = requests.post(f"{BASE_URL}/verifications/", data=data)
    assert r.status_code == 201, f"Failed: {r.text}"
    res = r.json()
    assert res["status"] == "success"
    assert res["review_status"] == "Pending"
    ver_id_1 = res["verification_id"]
    print(f"[PASS] POST /verifications/ (work_id=WB/2025/0553, id={ver_id_1})")

    # 4. Create second verification
    data2 = {
        "work_id": "WB/2025/0553",
        "observation": "WORK_IN_PROGRESS",
        "comment": "Excavation work started today.",
        "citizen_name": "Citizen Priya"
    }
    r = requests.post(f"{BASE_URL}/verifications/", data=data2)
    assert r.status_code == 201
    ver_id_2 = r.json()["verification_id"]
    print(f"[PASS] POST /verifications/ (second record, id={ver_id_2})")

    # 5. Create third verification with different work_id and observation
    data3 = {
        "work_id": "DL/2024/9911",
        "observation": "WORK_COMPLETED",
        "comment": "Community center fully constructed.",
        "citizen_name": "Citizen Amit"
    }
    r = requests.post(f"{BASE_URL}/verifications/", data=data3)
    assert r.status_code == 201
    ver_id_3 = r.json()["verification_id"]
    print(f"[PASS] POST /verifications/ (third record, id={ver_id_3})")

    # 6. Test invalid observation
    bad_data = {
        "work_id": "WB/2025/0553",
        "observation": "INVALID_STATUS"
    }
    r = requests.post(f"{BASE_URL}/verifications/", data=bad_data)
    assert r.status_code == 400, f"Expected 400 got {r.status_code}"
    print("[PASS] POST /verifications/ (Invalid observation rejected with 400)")

    # 7. Test invalid coordinates
    bad_coords = {
        "work_id": "WB/2025/0553",
        "observation": "NO_WORK_FOUND",
        "latitude": "not-a-number"
    }
    r = requests.post(f"{BASE_URL}/verifications/", data=bad_coords)
    assert r.status_code == 400
    print("[PASS] POST /verifications/ (Invalid latitude rejected with 400)")

    # 8. Test file validation: Invalid MIME type
    files = {"proof_image": ("test.txt", b"dummy text", "text/plain")}
    r = requests.post(f"{BASE_URL}/verifications/", data=data, files=files)
    assert r.status_code == 400
    assert "Invalid image type" in r.text
    print("[PASS] POST /verifications/ (Invalid MIME rejected with 400)")

    # 9. Test file validation: Oversized image (> 10MB)
    oversized_bytes = b"0" * (10 * 1024 * 1024 + 100)
    files = {"proof_image": ("large.jpg", oversized_bytes, "image/jpeg")}
    r = requests.post(f"{BASE_URL}/verifications/", data=data, files=files)
    assert r.status_code == 400
    assert "Image too large" in r.text
    print("[PASS] POST /verifications/ (Oversized image rejected with 400)")

    # 10. GET /verifications/
    r = requests.get(f"{BASE_URL}/verifications/")
    assert r.status_code == 200
    records = r.json()
    assert len(records) >= 3
    print(f"[PASS] GET /verifications/ (Total fetched: {len(records)})")

    # 11. GET /verifications/ with filter
    r = requests.get(f"{BASE_URL}/verifications/?work_id=WB/2025/0553")
    assert r.status_code == 200
    filtered = r.json()
    assert all(item["work_id"] == "WB/2025/0553" for item in filtered)
    print(f"[PASS] GET /verifications/?work_id=WB/2025/0553 (Fetched {len(filtered)} items)")

    # 12. GET /verifications/{id}
    r = requests.get(f"{BASE_URL}/verifications/{ver_id_1}")
    assert r.status_code == 200
    rec1 = r.json()
    assert rec1["id"] == ver_id_1
    assert rec1["work_id"] == "WB/2025/0553"
    assert rec1["citizen_name"] == "Citizen Rohit"
    print(f"[PASS] GET /verifications/{ver_id_1}")

    # 13. GET non-existent ID (404)
    r = requests.get(f"{BASE_URL}/verifications/999999")
    assert r.status_code == 404
    print("[PASS] GET /verifications/999999 (404 Not Found)")

    # 14. GET /verifications/work/{work_id:path} with slashes in work_id
    r = requests.get(f"{BASE_URL}/verifications/work/WB/2025/0553")
    assert r.status_code == 200
    work_records = r.json()
    assert len(work_records) >= 2
    assert all(item["work_id"] == "WB/2025/0553" for item in work_records)
    print(f"[PASS] GET /verifications/work/WB/2025/0553 (Path with slashes)")

    # 15. PATCH /verifications/{id}/status
    patch_body = {"review_status": "Verified"}
    r = requests.patch(f"{BASE_URL}/verifications/{ver_id_1}/status", json=patch_body)
    assert r.status_code == 200
    assert r.json()["review_status"] == "Verified"
    print(f"[PASS] PATCH /verifications/{ver_id_1}/status to 'Verified'")

    # Test invalid status in PATCH
    r = requests.patch(f"{BASE_URL}/verifications/{ver_id_1}/status", json={"review_status": "SUPER_STATUS"})
    assert r.status_code == 422
    print("[PASS] PATCH with invalid status rejected with 422")

    # 16. GET /verifications/stats
    r = requests.get(f"{BASE_URL}/verifications/stats")
    assert r.status_code == 200
    stats = r.json()
    print("Stats received:", stats)
    assert stats["total"] >= 3
    assert stats["verified"] >= 1
    assert stats["no_work_found"] >= 1
    assert stats["work_completed"] >= 1
    assert stats["work_in_progress"] >= 1
    print("[PASS] GET /verifications/stats")

    print("\n*** ALL 16 BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY! ***")

if __name__ == "__main__":
    run_tests()
