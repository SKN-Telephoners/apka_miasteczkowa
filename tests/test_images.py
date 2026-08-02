import pytest
import io
from unittest.mock import patch
import base64

# =============================================================================
# Tests for handling uploading pictures to the cloud (Cloudflare R2)
# =============================================================================
TINY_JPG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxISEhUTEhIVFRUVFRUVFRUVFRUVFRUWFxUVFRUYHSggGBolHRUVITEhJSkrLi4uFx8zODMtNygtLisBCgoKDg0OFRAQFS0dHR0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAAEAAQMBIgACEQEDEQH/xAAV"
    "AAEBAAAAAAAAAAAAAAAAAAAABf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhADEAAAAJ8f/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQL/xAAVEQEBAAAAAAAAAAAAAAAAAAABAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAgEBPwF//8QAFBABAAAAAAAA"
    "AAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9k="
)

@patch('backend.routes.picture_routes.validate_and_process_image')
@patch('backend.routes.picture_routes.upload_to_r2')
def test_upload_file_success(mock_upload_to_r2, mock_validate, client, logged_in_user, app):
    mock_upload_to_r2.return_value = 'fake_12345.jpg'
    mock_validate.return_value = (io.BytesIO(b"fake_processed_data"), None)
    
    with app.app_context():
        user, token = logged_in_user
        
        data = {
            'type': 'event',
            'file': (io.BytesIO(TINY_JPG), 'test_picture.jpg')
        }
        
        response = client.post(
            '/api/pictures/upload', 
            data=data, 
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        json_data = response.get_json()
        assert json_data['cloud_id'] == 'fake_12345.jpg'
        assert 'picture_url' in json_data
        mock_upload_to_r2.assert_called_once()

@patch('backend.routes.picture_routes.validate_and_process_image')
@patch('backend.routes.picture_routes.upload_to_r2')
def test_upload_batch_success(mock_upload_to_r2, mock_validate, client, logged_in_user, app):
    """Test successful upload of multiple pictures."""
    with app.app_context():
        user, user_token = logged_in_user

        mock_upload_to_r2.side_effect = ['id_1.jpg', 'id_2.jpg']
        mock_validate.return_value = (io.BytesIO(b"fake_processed_data"), None)

        data = {
            'files': [
                (io.BytesIO(TINY_JPG), 'test1.jpg'),
                (io.BytesIO(TINY_JPG), 'test2.jpg'),
            ],
            'type': 'event'
        }

        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.post(
            "/api/pictures/upload-batch",
            data=data,
            headers=headers
        )
        assert response.status_code == 201 
        json_data = response.get_json()
        
        assert len(json_data['pictures']) == 2
        assert len(json_data['errors']) == 0
        assert json_data['pictures'][0]['cloud_id'] == 'id_1.jpg'
        assert json_data['pictures'][1]['cloud_id'] == 'id_2.jpg'
        assert mock_upload_to_r2.call_count == 2

def test_upload_batch_too_many_files(client, logged_in_user):
    """Test rejection when exceeding the 5-file limit."""
    user, user_token = logged_in_user
    
    files = [(io.BytesIO(TINY_JPG), f'test{i}.jpg') for i in range(6)]
    data = {'files': files}

    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.post(
        "/api/pictures/upload-batch",
        data=data,
        headers=headers
    )

    assert response.status_code == 400
    assert "Maximum 5 pictures allowed" in response.get_json()['message']

def test_upload_batch_no_files(client, logged_in_user):
    """Test error when no files key is present in the request."""
    user, user_token = logged_in_user
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.post(
        "/api/pictures/upload-batch",
        data={},
        headers=headers
    )

    assert response.status_code == 400
    assert "No files provided" in response.get_json()['message']

@patch('backend.routes.picture_routes.validate_and_process_image')
@patch('backend.routes.picture_routes.upload_to_r2')
def test_upload_batch_partial_failure(mock_upload_to_r2, mock_validate, client, logged_in_user, app):
    """Test behavior when one picture fails but another succeeds."""
    with app.app_context():
        user, user_token = logged_in_user

        mock_upload_to_r2.side_effect = ['success_id.jpg', None]
        mock_validate.return_value = (io.BytesIO(b"fake_processed_data"), None)

        data = {
            'files': [
                (io.BytesIO(TINY_JPG), 'good.jpg'),
                (io.BytesIO(TINY_JPG), 'bad.jpg'),
            ]
        }

        headers = {"Authorization": f"Bearer {user_token}"}
        response = client.post(
            "/api/pictures/upload-batch", 
            data=data, 
            headers=headers
        )

        assert response.status_code == 201 
        json_data = response.get_json()
        
        assert len(json_data['pictures']) == 1
        assert len(json_data['errors']) == 1
        assert json_data['pictures'][0]['cloud_id'] == 'success_id.jpg'
        assert "Some pictures failed to upload" in json_data['message']

@patch('backend.routes.picture_routes.validate_and_process_image')
@patch('backend.routes.picture_routes.upload_to_r2')
def test_upload_file_failure(mock_upload_to_r2, mock_validate, client, logged_in_user, app):
    """Tests error during sending pictures to R2 (function upload_to_r2 returns None)."""
    mock_upload_to_r2.return_value = None
    mock_validate.return_value = (io.BytesIO(b"fake_processed_data"), None)
    
    with app.app_context():
        user, user_token = logged_in_user
        headers = {"Authorization": f"Bearer {user_token}"}
        
        data = {
            'file': (io.BytesIO(TINY_JPG), 'test.jpg'),
            'type': 'event'
        }
        
        response = client.post("/api/pictures/upload", data=data, headers=headers)
        
        assert response.status_code == 500
        assert "Upload to S3 failed" in response.get_json()["message"]

def test_upload_file_no_file(client, logged_in_user):
    """Tests situation when there are no pictures in form (no pictures were sent)"""
    user, user_token = logged_in_user
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = client.post("/api/pictures/upload", data={}, headers=headers)

    assert response.status_code == 400
    assert "No file provided" in response.get_json()['message']
