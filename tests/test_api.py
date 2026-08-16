import unittest
from fastapi.testclient import TestClient
from api.app import app

class ApiTests(unittest.TestCase):
    def setUp(self): self.client = TestClient(app)
    def test_health(self): self.assertEqual(self.client.get('/health').status_code, 200)
    def test_summary(self):
        r=self.client.get('/summary'); self.assertEqual(r.status_code,200); self.assertEqual(r.json()['agents'],120)
    def test_unknown_agent_404(self): self.assertEqual(self.client.get('/agents/not-real').status_code,404)
    def test_agent_detail(self):
        r=self.client.get('/agents/agent-048'); self.assertEqual(r.status_code,200); self.assertIn('effective_access_paths',r.json())

if __name__ == '__main__': unittest.main()
