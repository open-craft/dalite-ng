from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect


def admin_index_wrapper(request):
    """
    Redirect to login page outside of an iframe, show help on enabling cookies inside an iframe.
    We consider the request to come from within an iframe if the HTTP Referer header is set.  This
    isn't entirely accurate, but should be good enough.
    """
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('admin:index'))
    else:
        # We probably got here from within the Studio, and the user has third-party cookies disabled,
        # so we show help on enabling cookies for this site.
        return render_to_response('peerinst/cookie_help.html', dict(host=request.get_host()))

