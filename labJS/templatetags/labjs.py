from django import template
from django.core.exceptions import ImproperlyConfigured
from labJS.conf import settings
from labJS.base import Labjs
from django.utils.safestring import mark_safe
from django.template.base import Token, TOKEN_TEXT
from django.template import NodeList

register = template.Library()

class LabjsNode(template.Node):

    def __init__(self, nodelist, *args, **kwargs):
        self.nodelist = nodelist

    def debug_mode(self, context):
        if settings.LABJS_DEBUG_TOGGLE:
            # Only check for the debug parameter
            # if a RequestContext was used
            request = context.get('request', None)
            if request is not None:
                return settings.LABJS_DEBUG_TOGGLE in request.GET

    def render(self, context):
        #Check if in debug mode
        if self.debug_mode(context) or not settings.LABJS_ENABLED:
            return self.nodelist.render(context)
        
        # Check if we should allow labks to perform for IE6/7
        # As it seems to have some issues in some cases.
        request = context.get('request', None)
        if request and not settings.LABJS_IE7IE6_ENABLED:
            agent = request.META.get('HTTP_USER_AGENT', '').lower()
            if "msie 7" in agent or "msie 6" in agent:
                return self.nodelist.render(context)

        if self.debug_mode(context) or not settings.LABJS_ENABLED:
            return self.nodelist.render(context)

        # call compressor output method and handle exceptions
        rendered_output = Labjs(content=self.nodelist.render(context),context=context).render_output()
        return rendered_output


@register.tag
def labjs(parser, token):
    """
    Renders a labjs queue from linked js.

    Syntax::

        {% labjs %}
        <html of linked JS>
        {% endlabjs %}

    Examples::

    {% labjs %}

        <script type="text/javascript" src="{{ STATIC_URL }}js/jquery-1.5.2.min.js" ></script>

        {% wait %}

        <script type="text/javascript" src="{{ STATIC_URL }}js/jquery.formset.min.js" ></script>
        <script type="text/javascript" src="{% url django.views.i18n.javascript_catalog %}"></script>

    {% endlabjs %}

    Which would be rendered something like::

     <script type="text/javascript">$LAB.queueScript("/static/js/jquery-1.5.2.min.js").queueScript("/static/js/jquery.formset.min.js").queueScript("/jsi18n/")</script>

    """
    nodelist = NodeList()
    while True:
        chunk = parser.parse(('endlabjs','wait'))
        ptoken = parser.next_token()

        if ptoken.contents == 'wait':
            chunk.append(Wait())
            nodelist.extend(chunk)
        elif ptoken.contents == 'endlabjs':
            #parser.delete_first_token()
            nodelist.extend(chunk)
            break

    return LabjsNode(nodelist)



class Wait(template.Node):
    def debug_mode(self, context):
        if settings.LABJS_DEBUG_TOGGLE:
        # Only check for the debug parameter
        # if a RequestContext was used
            request = context.get('request', None)
            if request is not None:
                return settings.LABJS_DEBUG_TOGGLE in request.GET

    def render(self, context):
        #TODO: implement check
        return '<script type="text/javascript"></script>'


@register.simple_tag(takes_context=True)
def runlabjs(context):
    """
    Renders an empty labjs queue
    """
    return """<script type="text/javascript">
        $LAB
	    .runQueue();
    </script>""" #TODO: make this prettier





