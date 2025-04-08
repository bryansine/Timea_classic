from django import template

register = template.Library()

@register.filter
def less_than(value, arg):
    return value < arg

@register.filter
def get_item(queryset, rating):
    for item in queryset:
        if item['rating'] == int(rating):
            return item['count']
    return 0

@register.filter
def multiply(value, arg):
    return value * arg