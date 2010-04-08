#coding:utf-8

"""
    django-weave unittests
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyleft: 2010 by the django-weave team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import base64
import logging
import time


if __name__ == "__main__":
    # run unittest directly
    # this works only in a created test virtualenv, see:
    # http://code.google.com/p/django-weave/wiki/CreateTestEnvironment
    import os
    os.environ["DJANGO_SETTINGS_MODULE"] = "testproject.settings"
    virtualenv_file = os.path.abspath("../../../bin/activate_this.py")
    execfile(virtualenv_file, dict(__file__=virtualenv_file))


from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test import TestCase
from django.conf import settings

from weave import Logging

# Uncomment this, to see logging output:
#logger = Logging.get_logger()
#handler = logging.StreamHandler()
#logger.addHandler(handler)


class WeaveServerTest(TestCase):
    def _pre_setup(self, *args, **kwargs):
        super(WeaveServerTest, self)._pre_setup(*args, **kwargs)

        # Create a test user with basic auth data
        self.testuser = User(username="testuser")
        raw_password = "test user password!"
        self.testuser.set_password(raw_password)
        self.testuser.save()

        raw_auth_data = "%s:%s" % (self.testuser.username, raw_password)
        self.auth_data = "basic %s" % base64.b64encode(raw_auth_data)

    def _post_teardown(self, *args, **kwargs):
        super(WeaveServerTest, self)._post_teardown(*args, **kwargs)
        self.testuser.delete()

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def assertWeaveTimestamp(self, response):
        """ Check if a valid weave timestamp is in response. """
        try:
            raw_timestamp = response["x-weave-timestamp"]
        except KeyError, err:
            self.fail("Weave timestamp %r not in response.")

        timestamp = float(raw_timestamp)
        comparison_value = time.time() - 1
        self.failUnless(timestamp > comparison_value,
            "Weave timestamp %r is not bigger than comparison value %r" % (timestamp, comparison_value)
        )

    def test_register_check_user_not_exist(self):
        """ test user.register_check view with not existing user. """
        url = reverse("weave-register_check", kwargs={"username":"user doesn't exist"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "1")

    def test_register_check_user_exist(self):
        """ test user.register_check view with existing test user. """
        url = reverse("weave-register_check", kwargs={"username":self.testuser.username})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "0")

    def test_exists_with_not_existing_user(self):
        """ test user.exists view with not existing user. """
        url = reverse("weave-exists", kwargs={"username":"user doesn't exist", "version":"1.0"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "0")

    def test_exists_with_existing_user(self):
        """ test user.exists view with existing test user. """
        url = reverse("weave-exists", kwargs={"username":self.testuser.username, "version":"1.0"})
        response = self.client.get(url)
        self.failUnlessEqual(response.content, "1")

    def test_basicauth_get_authenticate(self):
        """ test if we get 401 'unauthorized' response. """
        url = reverse("weave-info", kwargs={"username":self.testuser.username, "version":"1.0"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 401) # Unauthorized: request requires user authentication
        self.failUnlessEqual(
            response["www-authenticate"], 'Basic realm="%s"' % settings.WEAVE.BASICAUTH_REALM
        )
        self.failUnlessEqual(response.content, "")

    def test_basicauth_send_authenticate(self):
        """ test if we can login via basicauth. """
        url = reverse("weave-info", kwargs={"username":self.testuser.username, "version":"1.0"})
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_data)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.content, "{}")
        self.failUnlessEqual(response["content-type"], "application/json")
        self.assertWeaveTimestamp(response)

#        from django_tools.unittest_utils.BrowserDebug import debug_response
#        debug_response(response)


#__test__ = {"doctest": """
#Another way to test that 1 + 1 is equal to 2.
#
#>>> 1 + 1 == 2
#True
#"""}

if __name__ == "__main__":
    # Run all unittest directly
    from django.core import management
    management.call_command('test', "weave", verbosity=1)
