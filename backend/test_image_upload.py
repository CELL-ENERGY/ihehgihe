import requests

url = 'http://127.0.0.1:8001/verifications/'

# Minimal valid 1x1 JPEG image bytes
tiny_jpeg = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00'
    b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
    b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c'
    b' $.#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01'
    b'\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
    b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
)

# First get auth token
auth_res = requests.post('http://127.0.0.1:8001/auth/login', json={'username': 'admin', 'password': 'admin'})
if auth_res.status_code != 200:
    auth_res = requests.post('http://127.0.0.1:8001/auth/register', json={'name': 'Live Citizen', 'email': 'live.citizen@example.com', 'password': 'password123'})
    if auth_res.status_code != 201:
        auth_res = requests.post('http://127.0.0.1:8001/auth/login', json={'email': 'live.citizen@example.com', 'password': 'password123'})

token = auth_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

data = {
    'citizen_handle': '@live_citizen',
    'locality_name': 'Salt Lake Sector V',
    'structure_type': 'Community Hall',
    'ground_observation': 'NO_WORK_FOUND',
    'work_id': 'WB/2025/0553',
    'comment': 'Live MongoDB photo proof test from citizen',
    'latitude': '22.5726000',
    'longitude': '88.3639000',
    'citizen_name': 'Live Citizen'
}

files = {
    'proof_image': ('site_inspection.jpg', tiny_jpeg, 'image/jpeg')
}

print("Submitting verification with live photo to MongoDB Storage...")
res = requests.post(url, data=data, files=files, headers=headers)
print('Response HTTP Status:', res.status_code)
print('Response JSON:', res.json())
assert res.status_code == 201

resp_json = res.json()
image_url = resp_json.get('image_url')
print('\nUploaded Image Public URL:', image_url)
assert image_url is not None
assert "/images/" in image_url

print("\nVerifying image can be downloaded via public URL...")
fetch_url = image_url if image_url.startswith('http') else f'http://127.0.0.1:8001{image_url}'
img_res = requests.get(fetch_url)
print('HTTP status code of image URL:', img_res.status_code)
assert img_res.status_code == 200
print(f'Successfully downloaded {len(img_res.content)} bytes from MongoDB Storage!')

print("\n*** MONGODB PHOTO UPLOAD & CITIZEN VERIFICATION 100% WORKING! ***")
