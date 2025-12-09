from django import template

register = template.Library()

@register.filter
def get_option(question, option_number):
    """
    Usage: {{ question|get_option:"1" }}
    Returns option_1, option_2, option_3, or option_4 based on number
    """
    try:
        option_number = int(option_number)
        if option_number == 1:
            return question.option_1
        elif option_number == 2:
            return question.option_2
        elif option_number == 3:
            return question.option_3
        elif option_number == 4:
            return question.option_4
    except (ValueError, AttributeError):
        return ""
    return ""
