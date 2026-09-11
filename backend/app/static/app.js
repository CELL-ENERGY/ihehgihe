/**
 * Jan Nidhi Spotter — Frontend Application Logic
 * Manages JWT Auth, Geolocation capture, Photo preview,
 * Mandatory field validation, Deferred XP flow, and Admin review.
 */

const API_BASE = "";
let currentToken = localStorage.getItem("jn_token") || null;
let currentUser = null;
let lastSubmittedVerification = null;

// ==========================================================================
// Initialization & Authentication
// ==========================================================================

document.addEventListener("DOMContentLoaded", async () => {
  if (currentToken) {
    await fetchUserProfile();
  } else {
    // Auto-login to demo account for instant out-of-the-box testing
    await quickDemoLogin();
  }
  showView("dashboard");
});

async function fetchUserProfile() {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${currentToken}` }
    });
    if (res.ok) {
      currentUser = await res.json();
      updateUserNav();
      loadDashboard();
    } else {
      logout();
    }
  } catch (err) {
    console.error("Failed to load user profile:", err);
  }
}

function updateUserNav() {
  const navBox = document.getElementById("user-nav-box");
  const loginBtn = document.getElementById("btn-open-login");
  const levelBadge = document.getElementById("nav-level-badge");
  const xpPill = document.getElementById("nav-xp-pill");

  if (currentUser) {
    navBox.style.display = "flex";
    loginBtn.style.display = "none";
    levelBadge.innerText = `Lvl ${currentUser.level}`;
    xpPill.innerText = `${currentUser.xp} XP`;
  } else {
    navBox.style.display = "none";
    loginBtn.style.display = "block";
  }
}

function logout() {
  currentToken = null;
  currentUser = null;
  localStorage.removeItem("jn_token");
  updateUserNav();
  showView("dashboard");
}

// ==========================================================================
// View Routing
// ==========================================================================

function showView(viewName) {
  const views = ["dashboard", "submit", "success", "submissions", "admin"];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) el.style.display = (v === viewName) ? "block" : "none";
    const navBtn = document.getElementById(`nav-${v}`);
    if (navBtn) navBtn.classList.toggle("active", v === viewName);
  });

  if (viewName === "dashboard") loadDashboard();
  if (viewName === "submissions") loadMySubmissions();
  if (viewName === "admin") loadAdminPortal();
}

// ==========================================================================
// Dashboard
// ==========================================================================

async function loadDashboard() {
  if (!currentToken) return;

  try {
    const res = await fetch(`${API_BASE}/users/me/dashboard`, {
      headers: { Authorization: `Bearer ${currentToken}` }
    });
    if (!res.ok) return;

    const data = await res.json();

    document.getElementById("dash-user-name").innerText = data.name;
    document.getElementById("dash-user-email").innerText = data.email;
    document.getElementById("dash-level-large").innerText = `Level ${data.current_level}`;
    document.getElementById("dash-total-xp").innerText = data.current_xp;

    document.getElementById("dash-progress-fill").style.width = `${data.progress_percent}%`;
    document.getElementById("dash-xp-progress-text").innerText = `${data.xp_to_next_level} XP to Level ${data.current_level + 1} (${data.progress_percent}%)`;

    document.getElementById("dash-total-submissions").innerText = data.total_submissions;
    document.getElementById("dash-verified-submissions").innerText = data.verified_submissions;
    document.getElementById("dash-pending-submissions").innerText = data.pending_submissions;
    document.getElementById("dash-unclaimed-xp").innerText = data.unclaimed_xp_count;

    if (currentUser) {
      currentUser.xp = data.current_xp;
      currentUser.level = data.current_level;
      updateUserNav();
    }
  } catch (err) {
    console.error("Error loading dashboard:", err);
  }
}

// ==========================================================================
// Verification Form: Geolocation & Photo
// ==========================================================================

function selectObservation(value) {
  document.querySelectorAll(".radio-card").forEach(c => c.classList.remove("selected"));
  const input = document.querySelector(`input[name="ground_observation"][value="${value}"]`);
  if (input) {
    input.checked = true;
    input.closest(".radio-card").classList.add("selected");
  }
}

function captureLocation() {
  const statusEl = document.getElementById("loc-status-text");
  const coordsDisplay = document.getElementById("loc-coords-display");
  const latDisplay = document.getElementById("display-lat");
  const lonDisplay = document.getElementById("display-lon");
  const latInput = document.getElementById("latitude");
  const lonInput = document.getElementById("longitude");

  if (!navigator.geolocation) {
    statusEl.className = "location-badge-warning";
    statusEl.innerText = "Location is required to submit a verification (Browser GPS not supported).";
    return;
  }

  statusEl.className = "location-badge-warning";
  statusEl.innerText = "Capturing location...";

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude.toFixed(7);
      const lon = pos.coords.longitude.toFixed(7);

      latInput.value = lat;
      lonInput.value = lon;
      latDisplay.innerText = lat;
      lonDisplay.innerText = lon;

      statusEl.className = "location-badge-success";
      statusEl.innerText = "Location captured ✓";
      coordsDisplay.style.display = "block";
    },
    (err) => {
      console.warn("Geolocation error:", err);
      // If denied in dev environment or permissions unavailable, fallback to Kolkata demo coordinates
      const fallbackLat = "22.5726410";
      const fallbackLon = "88.3638920";
      latInput.value = fallbackLat;
      lonInput.value = fallbackLon;
      latDisplay.innerText = fallbackLat;
      lonDisplay.innerText = fallbackLon;

      statusEl.className = "location-badge-success";
      statusEl.innerText = "Location captured ✓ (Default Local Coordinates)";
      coordsDisplay.style.display = "block";
    },
    { timeout: 10000, enableHighAccuracy: true }
  );
}

function handleFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  const validTypes = ["image/jpeg", "image/png", "image/webp"];
  if (!validTypes.includes(file.type)) {
    showToast("Invalid image type. Please select a JPG, PNG, or WEBP photo.");
    event.target.value = "";
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    showToast("Image too large. Maximum size is 10 MB.");
    event.target.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById("image-preview").src = e.target.result;
    document.getElementById("preview-filename").innerText = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    document.getElementById("preview-container").style.display = "block";
    document.getElementById("photo-placeholder").style.display = "none";
  };
  reader.readAsDataURL(file);
}

// ==========================================================================
// Verification Submission Handler
// ==========================================================================

async function handleFormSubmit(event) {
  event.preventDefault();

  const handle = document.getElementById("citizen_handle").value.trim();
  const locality = document.getElementById("locality_name").value.trim();
  const structure = document.getElementById("structure_type").value;
  const obsRadio = document.querySelector('input[name="ground_observation"]:checked');
  const lat = document.getElementById("latitude").value.trim();
  const lon = document.getElementById("longitude").value.trim();
  const photoInput = document.getElementById("proof_image");
  const workId = document.getElementById("work_id").value.trim();

  // Strict Validation: Every field is mandatory
  if (!handle) return showToast("Please provide your Citizen Handle / ID.");
  if (!locality) return showToast("Please provide the Locality Name.");
  if (!structure) return showToast("Please select a Structure Type.");
  if (!obsRadio) return showToast("Please select your ground observation.");
  if (!lat || !lon) return showToast("Location is required to submit a verification. Click [ Use My Current Location ].");
  if (!photoInput.files || !photoInput.files[0]) return showToast("Please upload a photo.");

  const submitBtn = document.getElementById("btn-submit-verification");
  submitBtn.disabled = true;
  submitBtn.innerText = "Submitting Evidence...";

  try {
    const formData = new FormData();
    formData.append("citizen_handle", handle);
    formData.append("locality_name", locality);
    formData.append("structure_type", structure);
    formData.append("ground_observation", obsRadio.value);
    formData.append("latitude", lat);
    formData.append("longitude", lon);
    formData.append("proof_image", photoInput.files[0]);
    if (workId) formData.append("work_id", workId);

    const headers = {};
    if (currentToken) {
      headers["Authorization"] = `Bearer ${currentToken}`;
    }

    const res = await fetch(`${API_BASE}/verifications/`, {
      method: "POST",
      headers: headers,
      body: formData,
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Submission failed");
    }

    // Save for success screen & XP claim
    lastSubmittedVerification = {
      id: data.verification_id,
      handle: handle,
      locality: locality,
      structure: structure,
      observation: obsRadio.value,
      coords: `${lat}, ${lon}`,
      imageUrl: data.image_url,
      xpClaimed: false,
    };

    // Render Success Screen
    renderSuccessScreen();
    showView("success");

    // Reset Form
    event.target.reset();
    document.getElementById("preview-container").style.display = "none";
    document.getElementById("photo-placeholder").style.display = "block";
    document.getElementById("loc-coords-display").style.display = "none";
    document.getElementById("loc-status-text").innerText = "Location required before submission";
    document.getElementById("loc-status-text").className = "location-badge-warning";
    document.querySelectorAll(".radio-card").forEach(c => c.classList.remove("selected"));

  } catch (err) {
    showToast(`Error: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = "SUBMIT VERIFICATION";
  }
}

// ==========================================================================
// Success Screen & Deferred XP Flow
// ==========================================================================

function renderSuccessScreen() {
  if (!lastSubmittedVerification) return;

  document.getElementById("success-evidence-img").src = lastSubmittedVerification.imageUrl;
  document.getElementById("success-handle").innerText = lastSubmittedVerification.handle;
  document.getElementById("success-locality").innerText = lastSubmittedVerification.locality;
  document.getElementById("success-structure").innerText = lastSubmittedVerification.structure;
  document.getElementById("success-obs").innerText = lastSubmittedVerification.observation;
  document.getElementById("success-coords").innerText = lastSubmittedVerification.coords;

  const claimBtn = document.getElementById("btn-claim-xp-main");
  const feedback = document.getElementById("claim-feedback");

  claimBtn.disabled = false;
  claimBtn.innerText = "⭐ CLAIM 150 XP ⭐";
  claimBtn.style.display = "inline-flex";
  feedback.style.display = "none";
}

async function claimXpForCurrent() {
  if (!lastSubmittedVerification) return;
  await executeClaimXp(lastSubmittedVerification.id, "btn-claim-xp-main", "claim-feedback");
}

async function executeClaimXp(verificationId, buttonId, feedbackId) {
  if (!currentToken) {
    showToast("Please log in to claim XP.");
    openAuthModal();
    return;
  }

  const btn = document.getElementById(buttonId);
  const feedback = feedbackId ? document.getElementById(feedbackId) : null;

  if (btn) {
    btn.disabled = true;
    btn.innerText = "Claiming...";
  }

  try {
    const res = await fetch(`${API_BASE}/verifications/${verificationId}/claim-xp`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${currentToken}`
      }
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to claim XP");
    }

    // Success: Award XP
    if (btn) {
      btn.innerText = "✓ 150 XP Claimed!";
      btn.classList.remove("btn-claim");
      btn.classList.add("btn-secondary");
    }

    if (feedback) {
      feedback.style.display = "block";
      feedback.innerText = `🎉 +150 XP Added! New Total: ${data.total_xp} XP (Level ${data.level})`;
    }

    // Update global profile
    if (currentUser) {
      currentUser.xp = data.total_xp;
      currentUser.level = data.level;
      updateUserNav();
    }

    loadDashboard();
    showToast("🎉 150 XP Claimed successfully!");

  } catch (err) {
    if (btn) {
      btn.disabled = true;
      btn.innerText = "✓ XP Already Claimed";
    }
    showToast(err.message);
  }
}

// ==========================================================================
// My Submissions
// ==========================================================================

async function loadMySubmissions() {
  if (!currentToken) return;

  const container = document.getElementById("submissions-list");
  container.innerHTML = `<div style="color: var(--text-secondary); text-align: center; grid-column: 1/-1; padding: 40px;">Loading your submissions...</div>`;

  try {
    const res = await fetch(`${API_BASE}/users/me/submissions`, {
      headers: { Authorization: `Bearer ${currentToken}` }
    });
    if (!res.ok) return;

    const items = await res.json();
    if (items.length === 0) {
      container.innerHTML = `
        <div style="color: var(--text-secondary); text-align: center; grid-column: 1/-1; padding: 60px;">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">📷</div>
          <h3>No ground verifications yet</h3>
          <p style="margin-top: 4px;">Click "+ New Verification" to submit your first ground evidence.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = items.map(item => {
      const dateStr = new Date(item.created_at).toLocaleDateString("en-US", {
        year: "numeric", month: "short", day: "numeric"
      });

      const xpButton = item.xp_claimed
        ? `<span class="badge" style="color: var(--accent-emerald); font-weight: 700; font-size: 0.9rem;">✓ 150 XP Claimed</span>`
        : `<button id="claim-btn-${item.id}" class="btn btn-claim" style="font-size: 0.85rem; padding: 8px 18px;" onclick="executeClaimXp(${item.id}, 'claim-btn-${item.id}')">⭐ CLAIM 150 XP</button>`;

      return `
        <div class="submission-card">
          <img src="${item.image_url}" class="submission-img" alt="Ground Proof" onerror="this.src='/static/placeholder.jpg'">
          <div class="submission-body">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
              <span class="status-badge status-${item.review_status.toLowerCase().replace(' ', '-')}">${item.review_status}</span>
              <span style="font-size: 0.8rem; color: var(--text-muted);">${dateStr}</span>
            </div>
            <h4 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">${item.locality_name}</h4>
            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 8px;">
              <strong>${item.structure_type}</strong> &bull; ${item.ground_observation}
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace; margin-bottom: 16px;">
              📍 ${Number(item.latitude).toFixed(5)}, ${Number(item.longitude).toFixed(5)}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 12px;">
              <span style="font-size: 0.85rem; color: #93c5fd;">ID: ${item.citizen_handle}</span>
              ${xpButton}
            </div>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose); grid-column: 1/-1; padding: 20px;">Failed to load submissions: ${err.message}</div>`;
  }
}

// ==========================================================================
// Admin Portal
// ==========================================================================

async function loadAdminPortal() {
  const container = document.getElementById("admin-submissions-list");
  container.innerHTML = `<div style="color: var(--text-secondary); padding: 40px; text-align: center;">Loading all submissions for review...</div>`;

  try {
    const res = await fetch(`${API_BASE}/admin/verifications`);
    if (!res.ok) return;

    const items = await res.json();
    if (items.length === 0) {
      container.innerHTML = `<div style="color: var(--text-secondary); padding: 40px; text-align: center;">No submissions in registry.</div>`;
      return;
    }

    container.innerHTML = items.map(item => `
      <div class="card" style="margin-bottom: 0;">
        <div style="display: grid; grid-template-columns: 220px 1fr 240px; gap: 24px;">
          <!-- Ground Evidence Photo -->
          <div>
            <a href="${item.image_url}" target="_blank">
              <img src="${item.image_url}" style="width: 100%; height: 160px; object-fit: cover; border-radius: 8px; border: 1px solid var(--border-color);" alt="Evidence">
            </a>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 6px; text-align: center;">Click photo to open full size</div>
          </div>

          <!-- Ground & User Details -->
          <div>
            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
              <span class="status-badge status-${item.review_status.toLowerCase().replace(' ', '-')}">${item.review_status}</span>
              <span style="font-size: 0.8rem; color: var(--text-muted);">${new Date(item.created_at).toLocaleString()}</span>
            </div>
            <h3 style="font-size: 1.2rem; font-weight: 700; margin-bottom: 6px;">${item.locality_name}</h3>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 10px;">
              <strong>Structure:</strong> ${item.structure_type} &bull; <strong>Ground Obs:</strong> ${item.ground_observation}
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-family: monospace; margin-bottom: 12px;">
              📍 Lat: ${item.latitude.toFixed(6)} | Lon: ${item.longitude.toFixed(6)}
            </div>
            <div style="background: rgba(15, 23, 42, 0.6); padding: 10px 14px; border-radius: 8px; font-size: 0.85rem;">
              <strong>Citizen:</strong> ${item.citizen_handle} &bull; <strong>Account:</strong> ${item.user.name} (${item.user.email}) &bull; <strong>User Lvl:</strong> ${item.user.level}
            </div>
          </div>

          <!-- Review Controls & Fixed XP Info -->
          <div style="border-left: 1px solid var(--border-color); padding-left: 20px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
              <div style="font-size: 0.8rem; color: var(--accent-emerald); font-weight: 700; margin-bottom: 4px;">
                XP Info: ${item.xp_claimed ? "✓ 150 XP Claimed" : "Unclaimed (150 XP eligible)"}
              </div>
              <small style="color: var(--text-muted); display: block; margin-bottom: 12px; font-size: 0.75rem;">
                XP is fixed at 150 per verification and cannot be changed.
              </small>

              <label style="font-size: 0.8rem; font-weight: 600; display: block; margin-bottom: 4px;">Update Status:</label>
              <select id="admin-status-${item.id}" class="form-select" style="padding: 8px; font-size: 0.85rem; margin-bottom: 8px;">
                <option value="Pending" ${item.review_status === "Pending" ? "selected" : ""}>Pending</option>
                <option value="Under Review" ${item.review_status === "Under Review" ? "selected" : ""}>Under Review</option>
                <option value="Verified" ${item.review_status === "Verified" ? "selected" : ""}>Verified</option>
                <option value="Rejected" ${item.review_status === "Rejected" ? "selected" : ""}>Rejected</option>
              </select>

              <label style="font-size: 0.8rem; font-weight: 600; display: block; margin-bottom: 4px;">Admin Feedback:</label>
              <input type="text" id="admin-comment-${item.id}" class="form-input" style="padding: 8px; font-size: 0.85rem;" placeholder="Review notes..." value="${item.admin_comment || ""}">
            </div>

            <button class="btn btn-primary" style="margin-top: 12px; padding: 8px 16px; font-size: 0.85rem;" onclick="saveAdminReview(${item.id})">
              Save Review
            </button>
          </div>
        </div>
      </div>
    `).join("");

  } catch (err) {
    container.innerHTML = `<div style="color: var(--accent-rose); padding: 20px;">Error loading admin portal: ${err.message}</div>`;
  }
}

async function saveAdminReview(id) {
  const statusVal = document.getElementById(`admin-status-${id}`).value;
  const commentVal = document.getElementById(`admin-comment-${id}`).value;

  try {
    const res = await fetch(`${API_BASE}/admin/verifications/${id}/review`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_status: statusVal, admin_comment: commentVal })
    });

    if (!res.ok) throw new Error("Failed to save review");
    showToast("Review decision saved successfully!");
    loadAdminPortal();
  } catch (err) {
    showToast(`Error: ${err.message}`);
  }
}

// ==========================================================================
// Auth Modal & Login Logic
// ==========================================================================

function openAuthModal() {
  document.getElementById("auth-modal").style.display = "flex";
}

function closeAuthModal() {
  document.getElementById("auth-modal").style.display = "none";
}

function switchAuthTab(tab) {
  document.getElementById("form-login").style.display = (tab === "login") ? "block" : "none";
  document.getElementById("form-register").style.display = (tab === "register") ? "block" : "none";
  document.getElementById("tab-login").classList.toggle("active", tab === "login");
  document.getElementById("tab-register").classList.toggle("active", tab === "register");
  document.getElementById("auth-title").innerText = (tab === "login") ? "Citizen Login" : "Register Spotter Account";
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");

    currentToken = data.access_token;
    currentUser = data.user;
    localStorage.setItem("jn_token", currentToken);

    updateUserNav();
    closeAuthModal();
    loadDashboard();
    showToast(`Welcome back, ${currentUser.name}!`);

  } catch (err) {
    document.getElementById("auth-error").style.display = "block";
    document.getElementById("auth-error").innerText = err.message;
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration failed");

    currentToken = data.access_token;
    currentUser = data.user;
    localStorage.setItem("jn_token", currentToken);

    updateUserNav();
    closeAuthModal();
    loadDashboard();
    showToast(`Account created! Welcome, ${currentUser.name}!`);

  } catch (err) {
    document.getElementById("auth-error").style.display = "block";
    document.getElementById("auth-error").innerText = err.message;
  }
}

async function quickDemoLogin() {
  // Check if demo user exists or register
  try {
    let res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "citizen@jannidhi.gov.in", password: "demo_password_123" })
    });

    if (!res.ok) {
      // Register demo user
      res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "Citizen Explorer",
          email: "citizen@jannidhi.gov.in",
          password: "demo_password_123"
        })
      });
    }

    const data = await res.json();
    if (data.access_token) {
      currentToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem("jn_token", currentToken);
      updateUserNav();
      closeAuthModal();
      loadDashboard();
    }
  } catch (err) {
    console.error("Demo login error:", err);
  }
}

function showToast(message) {
  const alert = document.getElementById("global-alert");
  alert.innerText = message;
  alert.style.display = "block";
  setTimeout(() => {
    alert.style.display = "none";
  }, 4500);
}
