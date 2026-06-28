from rest_framework import serializers
from .models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = ['id', 'name', 'budget', 'spend', 'status']

    def get_status(self, obj):
        if obj.budget <= 0:
            return 'OK'
        if obj.spend > obj.budget:
            return 'Overspent'
        if obj.spend / obj.budget >= 0.9:
            return 'Warning'
        return 'OK'
