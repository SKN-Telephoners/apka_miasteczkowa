import pytest
from backend.extensions import db
import json
import uuid
import io
import base64

# A valid 1x1 transparent GIF pixel to satisfy Cloudinary's image validation
TINY_GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")

def test_upload_file_success(client, logged_in_user):
    user, token = logged_in_user

    data = {
        'tags': 'test, python, flask',
        'file': (io.BytesIO(TINY_GIF), 'test_image.gif')
    }

    response = client.post('/api/photos/upload', data=data, content_type='multipart/form-data',  headers={
            "Authorization": f"Bearer {token}"
    })

    json_data = response.get_json()

    assert response.status_code == 201
    assert 'image_url' in json_data
    assert 'test' in json_data['tags']
    
    print(f"Uploaded URL: {json_data['image_url']}")

def test_upload_no_file(client, logged_in_user):
    user, token = logged_in_user

    response = client.post('/api/photos/upload', data={'tags': 'no-file-here'},  headers={
            "Authorization": f"Bearer {token}"
    })
    
    assert response.status_code == 400
    assert response.get_json()['message'] == "No file provided"