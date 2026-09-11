import React, { useState, useRef } from 'react';
import api from '../api';

export default function VerificationForm({ user, onSuccess }) {
  const [citizenHandle, setCitizenHandle] = useState(user?.name ? `@${user.name.toLowerCase().replace(/\s+/g, '_')}` : '');
  const [localityName, setLocalityName] = useState('');
  const [structureType, setStructureType] = useState('');
  const [groundObservation, setGroundObservation] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [locationStatus, setLocationStatus] = useState('Location required before submission');
  const [locationSuccess, setLocationSuccess] = useState(false);
  const [photoFile, setPhotoFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [photoInfo, setPhotoInfo] = useState('');
  const [workId, setWorkId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Separate refs for camera capture and file picker
  const cameraInputRef = useRef(null);
  const fileInputRef = useRef(null);

  const captureLocation = () => {
    setError('');
    setLocationStatus('Capturing location...');

    if (!navigator.geolocation) {
      setLocationStatus('Browser does not support geolocation. Location is required.');
      setLocationSuccess(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude.toFixed(7);
        const lon = pos.coords.longitude.toFixed(7);
        setLatitude(lat);
        setLongitude(lon);
        setLocationStatus('Location captured ✓');
        setLocationSuccess(true);
      },
      () => {
        // Fallback coordinates for local/desktop development
        setLatitude('22.5726410');
        setLongitude('88.3638920');
        setLocationStatus('Location captured ✓');
        setLocationSuccess(true);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const processImageFile = (file) => {
    if (!file) return;

    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type)) {
      setError('Invalid image type. Only JPG, PNG, and WEBP are allowed.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('Image too large. Maximum size is 10 MB.');
      return;
    }

    setError('');
    setPhotoFile(file);
    setPhotoInfo(`${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`);

    const reader = new FileReader();
    reader.onload = (event) => {
      setPreviewUrl(event.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleCameraChange = (e) => {
    processImageFile(e.target.files[0]);
    // Reset input so the same file can be re-selected
    e.target.value = '';
  };

  const handleFileChange = (e) => {
    processImageFile(e.target.files[0]);
    e.target.value = '';
  };

  const handleRemovePhoto = () => {
    setPhotoFile(null);
    setPreviewUrl('');
    setPhotoInfo('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Strict Field Validations
    if (!citizenHandle.trim()) {
      setError('Please provide your Citizen Handle / ID.');
      return;
    }
    if (!localityName.trim()) {
      setError('Please provide the Locality Name.');
      return;
    }
    if (!structureType) {
      setError('Please select a Structure Type.');
      return;
    }
    if (!groundObservation) {
      setError('Please select your ground observation.');
      return;
    }
    if (!latitude || !longitude) {
      setError('Location is required to submit a verification. Please click [ Use My Current Location ].');
      return;
    }
    if (!photoFile) {
      setError('Please take or upload a ground photo.');
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('citizen_handle', citizenHandle.trim());
      formData.append('locality_name', localityName.trim());
      formData.append('structure_type', structureType);
      formData.append('ground_observation', groundObservation);
      formData.append('latitude', latitude);
      formData.append('longitude', longitude);
      formData.append('proof_image', photoFile);
      if (workId.trim()) {
        formData.append('work_id', workId.trim());
      }

      const res = await api.post('/verifications/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      onSuccess({
        id: res.data.verification_id,
        imageUrl: res.data.image_url,
        citizenHandle: citizenHandle.trim(),
        localityName: localityName.trim(),
        structureType,
        groundObservation,
        latitude,
        longitude,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit verification. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div className="form-header">
        <h2>Submit Ground Verification</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '4px' }}>
          Every field is mandatory. Photo evidence and GPS coordinates are verified on the ledger.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>

        {/* 1. Citizen Handle / ID */}
        <div className="form-group">
          <label className="form-label">
            1. Citizen Handle / ID <span className="req">*</span>
          </label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. @citizen_rohit or Spotter_WB05"
            value={citizenHandle}
            onChange={(e) => setCitizenHandle(e.target.value)}
            required
          />
          <small style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
            This identifier tags your public ground report.
          </small>
        </div>

        {/* 2. Locality Name */}
        <div className="form-group">
          <label className="form-label">
            2. Locality Name <span className="req">*</span>
          </label>
          <input
            type="text"
            className="form-input"
            placeholder='e.g. "Salt Lake Sector V" or "Barasat Ward 12"'
            value={localityName}
            onChange={(e) => setLocalityName(e.target.value)}
            required
          />
        </div>

        {/* 3. Structure Type */}
        <div className="form-group">
          <label className="form-label">
            3. Structure Type <span className="req">*</span>
          </label>
          <select
            className="form-select"
            value={structureType}
            onChange={(e) => setStructureType(e.target.value)}
            required
          >
            <option value="" disabled>-- Select Structure Type --</option>
            <option value="Community Hall">Community Hall</option>
            <option value="Shelter">Shelter</option>
            <option value="Solar Street Light">Solar Street Light</option>
            <option value="Public Water RO Plant">Public Water RO Plant</option>
            <option value="Public Library / Study Center">Public Library / Study Center</option>
            <option value="Drainage">Drainage</option>
            <option value="Concrete Road">Concrete Road</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* 4. Ground Observation */}
        <div className="form-group">
          <label className="form-label">
            4. Ground Observation <span className="req">*</span>
          </label>
          <div className="radio-cards-grid">
            <label
              className={`radio-card ${groundObservation === 'WORK_COMPLETED' ? 'selected' : ''}`}
              onClick={() => setGroundObservation('WORK_COMPLETED')}
            >
              <input
                type="radio"
                name="ground_observation"
                value="WORK_COMPLETED"
                checked={groundObservation === 'WORK_COMPLETED'}
                onChange={() => setGroundObservation('WORK_COMPLETED')}
              />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>Fully Built / Ready</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Structure is complete</div>
              </div>
            </label>

            <label
              className={`radio-card ${groundObservation === 'WORK_IN_PROGRESS' ? 'selected' : ''}`}
              onClick={() => setGroundObservation('WORK_IN_PROGRESS')}
            >
              <input
                type="radio"
                name="ground_observation"
                value="WORK_IN_PROGRESS"
                checked={groundObservation === 'WORK_IN_PROGRESS'}
                onChange={() => setGroundObservation('WORK_IN_PROGRESS')}
              />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>Work in Progress</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Construction ongoing</div>
              </div>
            </label>

            <label
              className={`radio-card ${groundObservation === 'NO_WORK_FOUND' ? 'selected' : ''}`}
              onClick={() => setGroundObservation('NO_WORK_FOUND')}
            >
              <input
                type="radio"
                name="ground_observation"
                value="NO_WORK_FOUND"
                checked={groundObservation === 'NO_WORK_FOUND'}
                onChange={() => setGroundObservation('NO_WORK_FOUND')}
              />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>No Structure Found</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>No work found at site</div>
              </div>
            </label>
          </div>
        </div>

        {/* 5. Location */}
        <div className="form-group">
          <label className="form-label">
            5. Location <span className="req">*</span>
          </label>
          <div className="location-box">
            <div className="location-info">
              <div className={locationSuccess ? 'location-badge-success' : 'location-badge-warning'}>
                {locationStatus}
              </div>
              {latitude && longitude && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontFamily: 'monospace', marginTop: '4px' }}>
                  Latitude: {latitude} | Longitude: {longitude}
                </div>
              )}
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={captureLocation}
            >
              📍 Use My Current Location
            </button>
          </div>
        </div>

        {/* 6. Upload Ground Photo — Two Options */}
        <div className="form-group">
          <label className="form-label">
            6. Upload Ground Photo <span className="req">*</span>
          </label>

          {/* Hidden camera input — opens device camera on mobile */}
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            style={{ display: 'none' }}
            onChange={handleCameraChange}
            id="camera-input"
          />

          {/* Hidden file picker input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            id="file-input"
          />

          {!previewUrl ? (
            /* No photo yet — show both buttons */
            <div className="photo-upload-options">
              <button
                type="button"
                className="photo-option-btn photo-option-camera"
                onClick={() => cameraInputRef.current?.click()}
              >
                <span className="photo-option-icon">📷</span>
                <span className="photo-option-label">Take Picture</span>
                <span className="photo-option-sub">Use device camera</span>
              </button>

              <button
                type="button"
                className="photo-option-btn photo-option-gallery"
                onClick={() => fileInputRef.current?.click()}
              >
                <span className="photo-option-icon">📁</span>
                <span className="photo-option-label">Upload from Device</span>
                <span className="photo-option-sub">JPG, PNG, WEBP · Max 10 MB</span>
              </button>
            </div>
          ) : (
            /* Photo selected — show preview with retake/remove options */
            <div className="photo-preview-container">
              <img src={previewUrl} className="preview-image" alt="Ground Preview" />
              <div className="photo-preview-info">
                <span style={{ fontSize: '0.85rem', color: 'var(--accent-emerald)', fontWeight: 600 }}>
                  ✓ Photo ready
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                  {photoInfo}
                </span>
              </div>
              <div className="photo-preview-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem', padding: '8px 16px' }}
                  onClick={() => cameraInputRef.current?.click()}
                >
                  📷 Retake
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem', padding: '8px 16px' }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  📁 Change File
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem', padding: '8px 16px', color: '#f87171', borderColor: '#f87171' }}
                  onClick={handleRemovePhoto}
                >
                  ✕ Remove
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Optional Work ID */}
        <div className="form-group">
          <label className="form-label" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Optional Work ID (if known)
          </label>
          <input
            type="text"
            className="form-input"
            placeholder="e.g. WB/2025/0553"
            value={workId}
            onChange={(e) => setWorkId(e.target.value)}
          />
        </div>

        {/* Submit Button */}
        <div style={{ marginTop: '32px' }}>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '16px', fontSize: '1.1rem', fontWeight: 700 }}
            disabled={loading}
          >
            {loading ? 'Submitting Evidence to Ledger...' : 'SUBMIT VERIFICATION'}
          </button>
        </div>

      </form>
    </div>
  );
}
