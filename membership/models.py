from django.db import models


class Membership(models.Model):
    usdt_amount = models.DecimalField(max_digits=20, decimal_places=8)
    crypto_currency = models.CharField(max_length=50)
    purchase_date = models.DateTimeField(auto_now_add=True)
    receiver_address = models.CharField(max_length=255)
    membership_added = models.BooleanField(default=False)
    class Meta:
        db_table = 'diora_membership'
        verbose_name = 'diora_membership'
        verbose_name_plural = 'diora_memberships'
    def __str__(self):
        return self.receiver_address
