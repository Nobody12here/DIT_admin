# your_app/templatetags/querystring_utils.py
from django import template

register = template.Library()


@register.simple_tag
def toggle_filter(request, param, value):
    query = request.GET.copy()

    values = query.getlist(param)
    if value in values:
        values.remove(value)
    else:
        values.append(value)

    query.setlist(param, values)
    return "?" + query.urlencode()
