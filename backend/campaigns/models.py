# data and business rules about the data itself. Things that are true regardless of how the data is used.
from django.db import models


class Campaign(models.Model):
    name = models.CharField(max_length=255)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    
    @property
    def spend_percentage(self):
        if self.budget <= 0:
            return 0
        return (self.spend / self.budget) * 100
