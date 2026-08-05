"""
Organizations Domain Integration Unit Tests.
"""

from api.domain.organizations.service import organization_domain_service


def test_organization_domain_service_instantiation():
    assert organization_domain_service is not None
    assert hasattr(organization_domain_service, 'get_organization')
    assert hasattr(organization_domain_service, 'list_user_organizations')
    assert hasattr(organization_domain_service, 'get_members')
