import pytest
import io
from unittest.mock import patch
import base64

# =============================================================================
# Tests for handling uploading pictures to the cloud
# =============================================================================
TINY_JPG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxISEhUTEhIVFRUVFRUVFRUVFRUVFRUWFxUVFRUYHSggGBolHRUVITEhJSkrLi4uFx8zODMtNygtLisBCgoKDg0OFRAQFS0dHR0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAAEAAQMBIgACEQEDEQH/xAAV"
    "AAEBAAAAAAAAAAAAAAAAAAAABf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhADEAAAAJ8f/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQL/xAAVEQEBAAAAAAAAAAAAAAAAAAABAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAgEBPwF//8QAFBABAAAAAAAA"
    "AAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9k="
)

@patch('cloudinary.uploader.upload')
def test_upload_file_success(mock_cloudinary_upload, client, logged_in_user):
    
    mock_cloudinary_upload.return_value = {
        'eager': [{'secure_url': 'https://fake-cloudinary.com/picture.jpg'}],
        'cloud_id': 'fake_12345',
        'tags': ['test', 'python', 'flask']
    }

    user, token = logged_in_user

    data = {
        'tags': 'test, python, flask',
        'file': (io.BytesIO(TINY_JPG), 'test_picture.gif')
    }

    response = client.post('/api/pictures/upload', data=data, content_type='multipart/form-data',  headers={
        "Authorization": f"Bearer {token}"
        })

    json_data = response.get_json()

    assert response.status_code == 201
    # Depending on how make_api_response wraps data, this might be json_data['data']['picture_url'] 
    # but kept matching your original test structure
    assert json_data['picture_url'] == 'https://fake-cloudinary.com/picture.jpg'
    mock_cloudinary_upload.assert_called_once()

@patch('cloudinary.uploader.upload')
def test_upload_batch_success(mock_upload, client, logged_in_user):
    """Test successful upload of multiple pictures."""
    user, user_token = logged_in_user

    # mock the Cloudinary response
    mock_upload.side_effect = [
        {
            'cloud_id': 'id_1',
            'eager': [{'secure_url': 'https://res.cloudinary.com/url1.jpg'}]
        },
        {
            'cloud_id': 'id_2',
            'eager': [{'secure_url': 'https://res.cloudinary.com/url2.jpg'}]
        }
    ]

    # create mock files using BytesIO
    data = {
        'files': [
            (io.BytesIO(b"fake picture 1 content"), 'test1.jpg'),
            (io.BytesIO(b"fake picture 2 content"), 'test2.jpg'),
        ],
        'tags': 'test, pytest'
    }

    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.post(
        "/api/pictures/upload-batch",
        data=data,
        headers=headers,
        content_type='multipart/form-data'
    )

    assert response.status_code == 201
    json_data = response.get_json()
    assert len(json_data['pictures']) == 2
    assert json_data['pictures'][0]['cloud_id'] == 'id_1'
    assert mock_upload.call_count == 2

def test_upload_batch_too_many_files(client, logged_in_user):
    """Test rejection when exceeding the 5-file limit."""
    user, user_token = logged_in_user
    
    # create 6 fake files
    files = [(io.BytesIO(b"content"), f'test{i}.jpg') for i in range(6)]
    data = {'files': files}

    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.post(
        "/api/pictures/upload-batch",
        data=data,
        headers=headers,
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
    assert "Maximum 5 pictures allowed" in response.get_json()['message']

def test_upload_batch_no_files(client, logged_in_user):
    """Test error when no files key is present in the request."""
    user, user_token = logged_in_user
    headers = {"Authorization": f"Bearer {user_token}"}
    # sending empty data
    response = client.post(
        "/api/pictures/upload-batch",
        data={},
        headers=headers,
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
    assert "No files provided" in response.get_json()['message']

@patch('cloudinary.uploader.upload')
def test_upload_batch_partial_failure(mock_upload, client, logged_in_user):
    """Test behavior when one picture fails but another succeeds."""
    user, user_token = logged_in_user

    # first call succeeds, second call raises an exception
    mock_upload.side_effect = [
        {
            'cloud_id': 'success_id',
            'eager': [{'secure_url': 'https://res.cloudinary.com/success.jpg'}]
        },
        Exception("Cloudinary is down")
    ]

    data = {
        'files': [
            (io.BytesIO(b"good"), 'good.jpg'),
            (io.BytesIO(b"bad"), 'bad.jpg'),
        ]
    }

    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.post("/api/pictures/upload-batch", data=data, headers=headers)

    assert response.status_code == 201 # still 201 because at least one worked
    json_data = response.get_json()
    assert len(json_data['pictures']) == 1
    assert len(json_data['errors']) == 1
    assert "Some pictures failed to upload" in json_data['message']