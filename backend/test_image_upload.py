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

data = {
    'work_id': 'WB/2025/0553',
    'observation': 'NO_WORK_FOUND',
    'comment': 'Live Supabase photo proof test from citizen',
    'latitude': '22.5726000',
    'longitude': '88.3639000',
    'citizen_name': 'Live Citizen'
}

files = {
    'proof_image': ('site_inspection.jpg', tiny_jpeg, 'image/jpeg')
}

print("Submitting verification with live photo to Supabase...")
res = requests.post(url, data=data, files=files)
print('Response HTTP Status:', res.status_code)
print('Response JSON:', res.json())
assert res.status_code == 201

resp_json = res.json()
image_url = resp_json.get('image_url')
print('\nUploaded Image Public URL:', image_url)
assert image_url is not None
assert "supabase.co/storage/v1/object/public/citizen-proofs" in image_url

print("\nVerifying image can be downloaded via public URL...")
img_res = requests.get(image_url)
print('HTTP status code of image URL:', img_res.status_code)
assert img_res.status_code == 200
print(f'Successfully downloaded {len(img_res.content)} bytes from Supabase!')

print("\n*** SUPABASE PHOTO UPLOAD & CITIZEN VERIFICATION 100% WORKING! ***")
