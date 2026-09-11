import requests
import json

BASE_URL = "http://127.0.0.1:8001"

# 1x1 minimal valid JPEG
TINY_JPEG = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00'
    b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
    b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c'
    b' $.#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01'
    b'\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
    b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
)

def run_tests():
    print("=== STARTING FULL CITIZEN VERIFICATION & XP FLOW TEST SUITE ===")

    # -------------------------------------------------------------
    # 1. Health Check
    # -------------------------------------------------------------
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    print("[PASS] 1. GET /health is healthy")

    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    print("[PASS] 2. GET / serves Application API / Web status")

    # -------------------------------------------------------------
    # 2. Register & Login Citizen User
    # -------------------------------------------------------------
    user_payload = {
        "name": "Citizen Rohit",
        "email": "rohit.spotter@example.com",
        "password": "secure_password_123"
    }
    r = requests.post(f"{BASE_URL}/auth/register", json=user_payload)
    if r.status_code == 400: # Already exists from previous run
        r = requests.post(f"{BASE_URL}/auth/login", json={"email": user_payload["email"], "password": user_payload["password"]})
    assert r.status_code in (200, 201), f"Auth failed: {r.text}"
    auth_data = r.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[PASS] 3. Citizen registered & logged in (user_id={user_id}, initial_xp={auth_data['user']['xp']})")

    # -------------------------------------------------------------
    # 3. Mandatory Fields Validation (Reject if missing)
    # -------------------------------------------------------------
    valid_data = {
        "citizen_handle": "@rohit_spotter",
        "locality_name": "Salt Lake Sector V",
        "structure_type": "Community Hall",
        "ground_observation": "WORK_COMPLETED",
        "latitude": "22.5726410",
        "longitude": "88.3638920"
    }

    # Missing Citizen Handle
    d_no_handle = dict(valid_data)
    del d_no_handle["citizen_handle"]
    r = requests.post(f"{BASE_URL}/verifications/", data=d_no_handle, files={"proof_image": ("site.jpg", TINY_JPEG, "image/jpeg")}, headers=headers)
    assert r.status_code == 400
    assert "Citizen Handle" in r.text
    print("[PASS] 4. Missing Citizen Handle correctly rejected (HTTP 400)")

    # Missing Locality Name
    d_no_loc = dict(valid_data)
    del d_no_loc["locality_name"]
    r = requests.post(f"{BASE_URL}/verifications/", data=d_no_loc, files={"proof_image": ("site.jpg", TINY_JPEG, "image/jpeg")}, headers=headers)
    assert r.status_code == 400
    assert "Locality Name" in r.text
    print("[PASS] 5. Missing Locality Name correctly rejected (HTTP 400)")

    # Missing Structure Type
    d_no_struct = dict(valid_data)
    del d_no_struct["structure_type"]
    r = requests.post(f"{BASE_URL}/verifications/", data=d_no_struct, files={"proof_image": ("site.jpg", TINY_JPEG, "image/jpeg")}, headers=headers)
    assert r.status_code == 400
    assert "Structure Type" in r.text
    print("[PASS] 6. Missing Structure Type correctly rejected (HTTP 400)")

    # Missing Ground Observation
    d_no_obs = dict(valid_data)
    del d_no_obs["ground_observation"]
    r = requests.post(f"{BASE_URL}/verifications/", data=d_no_obs, files={"proof_image": ("site.jpg", TINY_JPEG, "image/jpeg")}, headers=headers)
    assert r.status_code == 400
    assert "ground observation" in r.text
    print("[PASS] 7. Missing Ground Observation correctly rejected (HTTP 400)")

    # Missing Location
    d_no_loc_coords = dict(valid_data)
    del d_no_loc_coords["latitude"]
    r = requests.post(f"{BASE_URL}/verifications/", data=d_no_loc_coords, files={"proof_image": ("site.jpg", TINY_JPEG, "image/jpeg")}, headers=headers)
    assert r.status_code == 400
    assert "Location is required" in r.text
    print("[PASS] 8. Missing Location coordinates correctly rejected (HTTP 400)")

    # Missing Photo
    r = requests.post(f"{BASE_URL}/verifications/", data=valid_data, headers=headers)
    assert r.status_code == 400
    assert "upload a photo" in r.text
    print("[PASS] 9. Missing Ground Photo correctly rejected (HTTP 400)")

    # -------------------------------------------------------------
    # 4. Valid Verification Submission (XP MUST NOT BE AWARDED HERE!)
    # -------------------------------------------------------------
    r_me_before = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    xp_before = r_me_before.json()["xp"]

    files = {"proof_image": ("ground_proof_sector5.jpg", TINY_JPEG, "image/jpeg")}
    r_sub = requests.post(f"{BASE_URL}/verifications/", data=valid_data, files=files, headers=headers)
    assert r_sub.status_code == 201, f"Failed: {r_sub.text}"
    sub_res = r_sub.json()
    ver_id = sub_res["verification_id"]
    print(f"\n[PASS] 10. Verification submitted successfully (id={ver_id})")
    print(f"       Message: {sub_res['message']}")
    print(f"       MongoDB Image URL: {sub_res['image_url']}")
    print(f"       XP Awarded on Submit: {sub_res['xp_awarded']} (Expected: 0)")

    # STRICT RULE: Verify XP was NOT awarded upon submission!
    r_me_after_sub = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    xp_after_sub = r_me_after_sub.json()["xp"]
    assert xp_after_sub == xp_before, f"CRITICAL FAILURE: XP was awarded on submit! Before: {xp_before}, After: {xp_after_sub}"
    print(f"[PASS] 11. STRICT XP CHECK: User XP remained {xp_after_sub} (NO premature XP awarded!)")

    # -------------------------------------------------------------
    # 5. User Dashboard Before Review
    # -------------------------------------------------------------
    r_dash = requests.get(f"{BASE_URL}/users/me/dashboard", headers=headers)
    assert r_dash.status_code == 200
    dash_data = r_dash.json()
    assert dash_data["pending_submissions"] >= 1
    print(f"[PASS] 12. Dashboard reflects pending verification (Level={dash_data['current_level']}, XP={dash_data['current_xp']})")

    # -------------------------------------------------------------
    # 6. Admin Portal View & Review Action (Auto-awards 150 XP)
    # -------------------------------------------------------------
    r_admin_login = requests.post(f"{BASE_URL}/auth/login", json={"email": "admin@gg", "password": "admin"})
    assert r_admin_login.status_code == 200
    admin_token = r_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    r_admin = requests.get(f"{BASE_URL}/admin/verifications", headers=admin_headers)
    assert r_admin.status_code == 200
    admin_items = r_admin.json()
    assert len(admin_items) >= 1
    print(f"[PASS] 13. Admin view fetched {len(admin_items)} citizen submissions with ground evidence")

    # Admin approves verification
    admin_patch = {
        "review_status": "VERIFIED",
        "admin_comment": "Field verification validated with local municipality records."
    }
    r_rev = requests.patch(f"{BASE_URL}/admin/verifications/{ver_id}/review", json=admin_patch, headers=admin_headers)
    assert r_rev.status_code == 200
    assert r_rev.json()["review_status"] == "VERIFIED"
    assert r_rev.json()["xp_awarded"] == 150
    print(f"[PASS] 14. Admin review updated to 'VERIFIED' with comments (+150 XP awarded)")

    # Verify user profile reflects new XP
    r_me_claimed = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert r_me_claimed.json()["xp"] == xp_before + 150
    print(f"[PASS] 15. User profile updated to {r_me_claimed.json()['xp']} XP")

    # -------------------------------------------------------------
    # 7. DUPLICATE XP PROTECTION (CRITICAL TEST)
    # -------------------------------------------------------------
    r_dup = requests.patch(f"{BASE_URL}/admin/verifications/{ver_id}/review", json=admin_patch, headers=admin_headers)
    assert r_dup.status_code == 200
    r_me_dup = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert r_me_dup.json()["xp"] == xp_before + 150
    print("[PASS] 16. DUPLICATE XP PROTECTION: Re-verifying record does NOT award duplicate XP")

    # -------------------------------------------------------------
    # 8. My Submissions History
    # -------------------------------------------------------------
    r_subs = requests.get(f"{BASE_URL}/users/me/submissions", headers=headers)
    assert r_subs.status_code == 200
    my_subs = r_subs.json()
    assert len(my_subs) >= 1
    my_ver = next(v for v in my_subs if v["id"] == ver_id)
    assert my_ver["xp_claimed"] == True
    assert my_ver["xp_awarded"] == 150
    print(f"[PASS] 17. GET /users/me/submissions shows correct XP status (xp_claimed=True, xp_awarded=150)")

    # -------------------------------------------------------------
    # 9. Final Dashboard Check
    # -------------------------------------------------------------
    r_dash_final = requests.get(f"{BASE_URL}/users/me/dashboard", headers=headers)
    dash_final = r_dash_final.json()
    print(f"\nFinal Citizen Dashboard Stats:")
    print(f"  Name: {dash_final['name']}")
    print(f"  Current XP: {dash_final['current_xp']}")
    print(f"  Current Level: {dash_final['current_level']}")
    print(f"  Next Level XP: {dash_final['next_level_xp']}")
    print(f"  Progress: {dash_final['progress_percent']}%")
    print(f"  Total Submissions: {dash_final['total_submissions']}")
    print(f"  Verified Submissions: {dash_final['verified_submissions']}")
    print(f"  Pending Submissions: {dash_final['pending_submissions']}")
    print("\n*** ALL WORKFLOW & XP INTEGRATION TESTS PASSED WITH 100% SUCCESS! ***\n")

if __name__ == "__main__":
    run_tests()
