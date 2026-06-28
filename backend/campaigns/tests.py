from django.test import TestCase
from rest_framework.test import APIClient
from .models import Campaign


class CampaignStatusTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_status_ok(self):
        campaign = Campaign(name='Test', budget=1000, spend=500)
        self.assertEqual(self._get_status(campaign), 'OK')

    def test_status_warning_at_90_percent(self):
        campaign = Campaign(name='Test', budget=1000, spend=900)
        self.assertEqual(self._get_status(campaign), 'Warning')

    def test_status_warning_above_90_percent(self):
        campaign = Campaign(name='Test', budget=1000, spend=950)
        self.assertEqual(self._get_status(campaign), 'Warning')

    def test_status_overspent(self):
        campaign = Campaign(name='Test', budget=1000, spend=1001)
        self.assertEqual(self._get_status(campaign), 'Overspent')

    def test_status_zero_budget(self):
        campaign = Campaign(name='Test', budget=0, spend=0)
        self.assertEqual(self._get_status(campaign), 'OK')

    def _get_status(self, campaign):
        from .serializers import CampaignSerializer
        serializer = CampaignSerializer(campaign)
        return serializer.data['status']


class CampaignAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Campaign.objects.create(name='Campaign A', budget=1000, spend=500)

    def test_list_campaigns(self):
        response = self.client.get('/api/campaigns/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_create_campaign(self):
        payload = {'name': 'Campaign B', 'budget': '2000.00', 'spend': '100.00'}
        response = self.client.post('/api/campaigns/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Campaign.objects.count(), 2)

    def test_create_campaign_returns_status(self):
        payload = {'name': 'Campaign C', 'budget': '1000.00', 'spend': '950.00'}
        response = self.client.post('/api/campaigns/', payload, format='json')
        self.assertEqual(response.data['status'], 'Warning')

    def test_campaign_fields_present(self):
        response = self.client.get('/api/campaigns/')
        keys = response.data[0].keys()
        for field in ['id', 'name', 'budget', 'spend', 'status']:
            self.assertIn(field, keys)
