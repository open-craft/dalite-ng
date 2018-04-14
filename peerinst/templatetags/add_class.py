from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()

@register.filter(needs_autoescape=True)
@stringfilter
def add_class(tag, css_class, autoescape=True):
    """Appends given css class to html tag"""

    print(tag)
    print(css_class)
    return
