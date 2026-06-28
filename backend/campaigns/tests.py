from django.test import TestCase
from rest_framework.test import APIClient
from .models import Campaign


class CampaignStatusTests(TestCase):

    def test_status_ok(self):
        campaign = Campaign(name='Test', budget=1000, spend=500)
        self.assertEqual(self._get_status(campaign), 'OK')

    def test_status_warning_at_90_percent(self):
        campaign = Campaign(name='Test', budget=1000, spend=900)
        self.assertEqual(self._get_status(campaign), 'Warning')

    def test_status_warning_above_90_percent(self):
        campaign = Campaign(name='Test', budget=1000, spend=950)
        self.assertEqual(self._get_status(campaign), 'Warning')

    def test_status_budget_reached(self):
        campaign = Campaign(name='Test', budget=1000, spend=1000)
        self.assertEqual(self._get_status(campaign), 'Budget Reached')

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

    def test_create_campaign_budget_reached_status(self):
        payload = {'name': 'Campaign D', 'budget': '1000.00', 'spend': '1000.00'}
        response = self.client.post('/api/campaigns/', payload, format='json')
        self.assertEqual(response.data['status'], 'Budget Reached')

    def test_campaign_fields_present(self):
        response = self.client.get('/api/campaigns/')
        keys = response.data[0].keys()
        for field in ['id', 'name', 'budget', 'spend', 'status']:
            self.assertIn(field, keys)

    def test_patch_campaign_spend(self):
        campaign = Campaign.objects.first()
        response = self.client.patch(
            f'/api/campaigns/{campaign.id}/',
            {'spend': '900.00'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'Warning')

    def test_delete_campaign(self):
        campaign = Campaign.objects.first()
        response = self.client.delete(f'/api/campaigns/{campaign.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Campaign.objects.count(), 0)


class CampaignValidationTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_negative_budget_rejected(self):
        payload = {'name': 'Bad Campaign', 'budget': '-100.00', 'spend': '0.00'}
        response = self.client.post('/api/campaigns/', payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_negative_spend_rejected(self):
        payload = {'name': 'Bad Campaign', 'budget': '1000.00', 'spend': '-50.00'}
        response = self.client.post('/api/campaigns/', payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_missing_name_rejected(self):
        payload = {'budget': '1000.00', 'spend': '0.00'}
        response = self.client.post('/api/campaigns/', payload, format='json')
        self.assertEqual(response.status_code, 400)

    def test_missing_budget_rejected(self):
        payload = {'name': 'Campaign', 'spend': '0.00'}
        response = self.client.post('/api/campaigns/', payload, format='json')
        self.assertEqual(response.status_code, 400)
