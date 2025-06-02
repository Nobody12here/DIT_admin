from django.db import models

NFT_CHOICES = [
    ("blackNFT", "Black Diamond NFT"),
    ("greenNFT", "Green Diamond NFT"),
    ("blueNFT", "Blue Diamond NFT"),
    ("redNFT", "Red Diamond NFT"),
    ("flawlessNFT", "Flawless Diamond NFT"),
]


class NFTReward(models.Model):
    email = models.EmailField()
    wallet_address = models.CharField(max_length=80)
    nft_type = models.CharField(choices=NFT_CHOICES)
    dit_amount = models.DecimalField(max_digits=20, decimal_places=8)
    reward_collection_date = models.DateTimeField(auto_now_add=True)
    reward_sent = models.BooleanField(default=False)

    class Meta:
        db_table = "nft_reward"

    def __str__(self):
        return self.wallet_address
