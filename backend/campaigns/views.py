from rest_framework import viewsets
from .models import Campaign
from .serializers import CampaignSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().order_by('-created_at')
    serializer_class = CampaignSerializer
