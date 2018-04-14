from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = Library()

@register.filter(needs_autoescape=True)
@stringfilter
def add_class(html, css_class, autoescape=True):
    """Appends given css class to html tag"""

    from HTMLParser import HTMLParser

    if autoescape:
        html = conditional_escape(html)
        css_class = conditional_escape(css_class)

    class CustomTagParser(HTMLParser):
        new_tag = ''

        def add_class(self, tag, attrs):
            class_added = False
            self.new_tag = self.new_tag + '<' + tag
            for key, value in attrs:
                if key == 'class':
                    self.new_tag = self.new_tag + ' ' + key + '=\"' + value + ' ' + css_class + '\" '
                    class_added = True
                else:
                    self.new_tag = self.new_tag + ' ' + key + '=\"' + value + '\" '

            if not class_added:
                self.new_tag = self.new_tag + 'class=\"' + css_class + '\" '

            return

        def handle_starttag(self, tag, attrs):
            self.add_class(tag, attrs)

            self.new_tag = self.new_tag + '>'

            return

        def handle_startendtag(self, tag, attrs):
            self.add_class(tag, attrs)

            self.new_tag = self.new_tag + '/>'

            return

        def handle_data(self, data):
            self.new_tag = self.new_tag + data

            return

        def handle_endtag(self, tag):
            self.new_tag = self.new_tag + '</' + tag + '>'

            return

    parser = CustomTagParser()
    parser.feed(html)

    return mark_safe(parser.new_tag)
