import unittest
import os
from PIL import Image
from app import app

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_upload(self):
        # Create a valid PNG test image
        test_image_path = 'uploads/test_image.png'
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path)

        with open(test_image_path, 'rb') as test_file:
            response = self.app.post('/upload_image', data={'file': test_file}, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)

        # Cleanup
        os.remove(test_image_path)

if __name__ == '__main__':
    unittest.main()
