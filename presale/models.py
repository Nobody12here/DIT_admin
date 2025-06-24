from django.db import models


class Presale(models.Model):
    dit_amount = models.DecimalField(max_digits=20, decimal_places=8)
    usdt_amount = models.DecimalField(max_digits=20, decimal_places=8)
    crypto_currency = models.CharField(max_length=50)
    purchase_date = models.DateTimeField(auto_now_add=True)
    receiver_address = models.CharField(max_length=255)
    tokens_delivered = models.BooleanField(default=False)
    class Meta:
        db_table = 'diamond_token_store'
        verbose_name = 'diamond token store'
        verbose_name_plural = 'diamond token store'
    def __str__(self):
        return self.receiver_address
