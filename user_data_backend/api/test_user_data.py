import json
from pathlib import Path
from rest_framework.test import APITestCase
from django.urls import reverse


class UserDataTests(APITestCase):
    """
    Test cases for user data submission and retrieval endpoints.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.url = reverse('UserData')
        self.valid_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'age': 25
        }
        
        # Clean up any existing test data
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.data_file = BASE_DIR / 'user_submissions.json'
        if self.data_file.exists():
            self.data_file.unlink()
    
    def tearDown(self):
        """Clean up after tests."""
        if self.data_file.exists():
            self.data_file.unlink()
    
    def test_post_valid_user_data(self):
        """Test submitting valid user data."""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['name'], 'John Doe')
        self.assertEqual(response.data['data']['email'], 'john.doe@example.com')
        self.assertEqual(response.data['data']['age'], 25)
    
    def test_post_missing_name(self):
        """Test submitting data without name."""
        payload = {
            'email': 'test@example.com',
            'age': 30
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.data)
        self.assertIn('name', response.data['errors'])
    
    def test_post_invalid_email(self):
        """Test submitting data with invalid email."""
        payload = {
            'name': 'John Doe',
            'email': 'invalid-email',
            'age': 25
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.data)
        self.assertIn('email', response.data['errors'])
    
    def test_post_invalid_age(self):
        """Test submitting data with invalid age."""
        # Test age too low
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 0
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('errors', response.data)
        
        # Test age too high
        payload['age'] = 151
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_get_empty_submissions(self):
        """Test retrieving submissions when none exist."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['data'], [])
    
    def test_get_submissions_after_post(self):
        """Test retrieving submissions after posting data."""
        # Post first submission
        self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        # Post second submission
        payload2 = {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'age': 30
        }
        self.client.post(
            self.url,
            data=json.dumps(payload2),
            content_type='application/json'
        )
        
        # Get all submissions
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['data']), 2)
        self.assertEqual(response.data['data'][0]['name'], 'John Doe')
        self.assertEqual(response.data['data'][1]['name'], 'Jane Smith')
    
    def test_name_validation(self):
        """Test name field validation rules."""
        # Test empty name
        payload = {
            'name': '   ',
            'email': 'test@example.com',
            'age': 25
        }
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test name with numbers
        payload['name'] = 'John123'
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # Test valid name with hyphen and apostrophe
        payload['name'] = "Mary-Jane O'Connor"
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
