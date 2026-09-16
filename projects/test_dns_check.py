from unittest.mock import patch

import dns.resolver
from django.test import SimpleTestCase

from .dns_check import check_domain


class FakeRdata:
    def __init__(self, target):
        self.target = target


class CheckDomainTests(SimpleTestCase):
    @patch('projects.dns_check.dns.resolver.Resolver.resolve')
    def test_verified_when_cname_matches(self, mock_resolve):
        mock_resolve.return_value = [FakeRdata('devlaunch.app.')]
        ok, message = check_domain('www.example.com')
        self.assertTrue(ok)
        self.assertIn('verified', message.lower())

    @patch('projects.dns_check.dns.resolver.Resolver.resolve')
    def test_not_verified_when_cname_points_elsewhere(self, mock_resolve):
        mock_resolve.return_value = [FakeRdata('some-other-host.example.net.')]
        ok, message = check_domain('www.example.com')
        self.assertFalse(ok)
        self.assertIn('some-other-host.example.net', message)

    @patch('projects.dns_check.dns.resolver.Resolver.resolve')
    def test_nxdomain(self, mock_resolve):
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        ok, message = check_domain('does-not-exist.invalid')
        self.assertFalse(ok)
        self.assertIn('does not exist', message)

    @patch('projects.dns_check.dns.resolver.Resolver.resolve')
    def test_no_cname_record(self, mock_resolve):
        mock_resolve.side_effect = dns.resolver.NoAnswer()
        ok, message = check_domain('example.com')
        self.assertFalse(ok)
        self.assertIn('No CNAME record', message)

    @patch('projects.dns_check.dns.resolver.Resolver.resolve')
    def test_timeout(self, mock_resolve):
        mock_resolve.side_effect = dns.resolver.Timeout()
        ok, message = check_domain('slow.example.com')
        self.assertFalse(ok)
        self.assertIn('timed out', message.lower())

    @patch('projects.dns_check.dns.resolver.Resolver.resolve')
    def test_matches_case_insensitively(self, mock_resolve):
        mock_resolve.return_value = [FakeRdata('DevLaunch.App.')]
        ok, _ = check_domain('www.example.com')
        self.assertTrue(ok)
