# models.py
from django.db import models


class ExternalUser(models.Model):
    display_name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    wallet_address = models.CharField(max_length=255, null=True, blank=True)
    dit_token_balance = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        managed = False  # ✅ No DB table
        verbose_name = "Community Member"
        verbose_name_plural = "Community Members"

    def __str__(self):
        return self.display_name
