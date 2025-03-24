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
    return 0  # Return 0 if the rating is not found

@register.filter
def multiply(value, arg):
    return value * arg


# from django import template

# register = template.Library()

# @register.filter
# def less_than(value, arg):
#     return value < arg

# @register.filter
# def get_item(queryset, rating):
#     print(f"get_item called with queryset: {queryset}, rating: {rating}")  # Debugging print
#     for item in queryset:
#         print(f"  Checking item: {item}")  # Debugging print
#         if item['rating'] == int(rating):
#             print(f"  Found count: {item['count']}")  # Debugging print
#             return item['count']
#     print(f"  Rating {rating} not found.")  # Debugging print
#     return 0

# @register.filter
# def multiply(value, arg):
#     return value * arg