"""Real DNS verification for custom domains (PRD F4).

An actual outbound CNAME lookup — works identically in dev and prod,
no Traefik/production wiring required. There's no background poller;
the developer triggers a check by clicking Verify (see
ProjectDomainVerifyView). Routing traffic on a verified domain to the
right project is a separate, not-yet-built piece — see DEPLOY.md.
"""
import dns.resolver

from .models import DNS_CNAME_TARGET

TIMEOUT_SECONDS = 5.0


def check_domain(domain_name):
    """Look up `domain_name`'s CNAME record and check it points at
    DNS_CNAME_TARGET. Returns (is_verified: bool, message: str)."""
    resolver = dns.resolver.Resolver()
    resolver.lifetime = TIMEOUT_SECONDS
    resolver.timeout = TIMEOUT_SECONDS

    try:
        answer = resolver.resolve(domain_name, 'CNAME')
    except dns.resolver.NXDOMAIN:
        return False, f'{domain_name} does not exist (NXDOMAIN).'
    except dns.resolver.NoAnswer:
        return False, (
            f'No CNAME record found for {domain_name}. '
            f'Add a CNAME record pointing to {DNS_CNAME_TARGET}.'
        )
    except dns.resolver.Timeout:
        return False, 'DNS lookup timed out — DNS may still be propagating. Try again shortly.'
    except Exception as exc:  # pragma: no cover - defensive, unexpected resolver error
        return False, f'DNS lookup failed: {exc}'

    targets = [str(rdata.target).rstrip('.').lower() for rdata in answer]
    if DNS_CNAME_TARGET.lower() in targets:
        return True, 'CNAME verified.'

    found = ', '.join(targets) or 'nothing'
    return False, f'CNAME points to "{found}", expected "{DNS_CNAME_TARGET}".'
