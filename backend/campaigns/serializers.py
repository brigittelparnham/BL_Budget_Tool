from rest_framework import serializers
from .models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    budget = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    spend = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)

    class Meta:
        model = Campaign
        fields = ['id', 'name', 'budget', 'spend', 'status']

    def validate_budget(self, value):
        if value < 0:
            raise serializers.ValidationError('Budget cannot be negative.')
        return value

    def validate_spend(self, value):
        if value < 0:
            raise serializers.ValidationError('Spend cannot be negative.')
        return value

    def get_status(self, obj):
        if obj.budget <= 0:
            return 'OK'
        if obj.spend > obj.budget:
            return 'Overspent'
        if obj.spend == obj.budget:
            return 'Budget Reached'
        if float(obj.spend) / float(obj.budget) >= 0.9:
            return 'Warning'
        return 'OK'
