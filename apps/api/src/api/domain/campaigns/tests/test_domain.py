"""
Campaign Domain Integration Unit Tests.
"""

from api.domain.campaigns.service import campaign_domain_service


def test_campaign_domain_service_instantiation():
    assert campaign_domain_service is not None
    assert hasattr(campaign_domain_service, 'create_campaign')
    assert hasattr(campaign_domain_service, 'list_campaigns')
    assert hasattr(campaign_domain_service, 'get_campaign')
    assert hasattr(campaign_domain_service, 'update_campaign')
    assert hasattr(campaign_domain_service, 'delete_campaign')
