# templatetags/custom_filters.py
from django import template
register = template.Library()

@register.filter
def get_row_columns(row):
    print(row)
    return [
        row.id, row.display_name, row.email, row.wallet_address, row.dit_token_balance,
        row.wallet_provider, row.flawless, row.red, row.blue, row.green, row.black
    ]
