"""
Billing Domain Integration Unit Tests.
"""

from api.domain.billing.service import billing_domain_service


def test_billing_domain_service_instantiation():
    assert billing_domain_service is not None
    assert hasattr(billing_domain_service, 'get_subscription')
    assert hasattr(billing_domain_service, 'list_plans')
    assert hasattr(billing_domain_service, 'get_invoices')
    assert hasattr(billing_domain_service, 'get_credits')
