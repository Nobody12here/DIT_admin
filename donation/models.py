from django.db import models

# Create your models here.


class Donation(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=6)
    usdt_amount = models.DecimalField(max_digits=12, decimal_places=6)
    receiver_address = models.CharField(max_length=50)
    email_address = models.EmailField(null=True, blank=True)
    purchase_date = models.DateTimeField(auto_now_add=True)

    has_dragon = models.BooleanField(default=False)
    dragon_delivered = models.BooleanField(default=False)

    def __str__(self):
        return self.receiver_address
