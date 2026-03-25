import pytest
from fast_api.services.corroboration_service import (
    CorroborationService,
    IdentityMapping,
    CorroborationSource,
)


class TestIdentityMapping:

    def test_empty_mapping_has_zero_confidence(self):
        mapping = IdentityMapping("+2348012345678")
        assert mapping.confidence_score == 0.0
        assert mapping.nin is None
        assert mapping.bvn is None
        assert mapping.is_recycled is False
        assert mapping.conflicts == []

    def test_to_dict_returns_all_fields(self):
        mapping = IdentityMapping("+2348012345678")
        mapping.nin = "12345678901"
        mapping.bvn = "10987654321"
        mapping.operator_code = "MTN"
        mapping.is_recycled = True
        mapping.nin_active = True
        mapping.bvn_active = True
        mapping.confidence_score = 0.85
        mapping.sources.append(
            CorroborationSource(name="reconix_sims", data={}, available=True)
        )

        result = mapping.to_dict()
        assert result["msisdn"] == "+2348012345678"
        assert result["nin"] == "12345678901"
        assert result["bvn"] == "10987654321"
        assert result["operator_code"] == "MTN"
        assert result["is_recycled"] is True
        assert result["confidence_score"] == 0.85
        assert result["assessed_at"] is not None
        assert len(result["sources_consulted"]) == 1

    def test_conflicts_included_in_dict(self):
        mapping = IdentityMapping("+2348012345678")
        mapping.conflicts.append({
            "field": "nin",
            "local_value": "111",
            "external_value": "222",
            "external_source": "nimc_api",
        })
        result = mapping.to_dict()
        assert result["conflicts"] is not None
        assert len(result["conflicts"]) == 1


class TestConfidenceScoring:

    def test_no_sources_gives_zero(self):
        mapping = IdentityMapping("+2348012345678")
        service = CorroborationService.__new__(CorroborationService)
        service._compute_confidence(mapping)
        assert mapping.confidence_score == 0.0

    def test_all_data_available_gives_high_score(self):
        mapping = IdentityMapping("+2348012345678")
        mapping.nin = "12345678901"
        mapping.bvn = "10987654321"
        mapping.operator_code = "MTN"
        mapping.is_recycled = True
        mapping.sources = [
            CorroborationSource("reconix_sims", {}, True),
            CorroborationSource("reconix_nin", {}, True),
            CorroborationSource("reconix_bvn", {}, True),
        ]
        service = CorroborationService.__new__(CorroborationService)
        service._compute_confidence(mapping)
        assert mapping.confidence_score >= 0.8

    def test_conflicts_reduce_score(self):
        mapping = IdentityMapping("+2348012345678")
        mapping.nin = "12345678901"
        mapping.bvn = "10987654321"
        mapping.operator_code = "MTN"
        mapping.is_recycled = True
        mapping.sources = [
            CorroborationSource("reconix_sims", {}, True),
            CorroborationSource("nimc_api", {}, True),
        ]
        mapping.conflicts = [
            {"field": "nin", "local_value": "111", "external_value": "222"},
            {"field": "bvn", "local_value": "333", "external_value": "444"},
        ]
        service = CorroborationService.__new__(CorroborationService)
        service._compute_confidence(mapping)
        assert mapping.confidence_score < 0.7

    def test_unavailable_sources_reduce_score(self):
        mapping = IdentityMapping("+2348012345678")
        mapping.nin = "12345678901"
        mapping.sources = [
            CorroborationSource("reconix_nin", {}, True),
            CorroborationSource("nimc_api", None, False),
            CorroborationSource("nibss_api", None, False),
        ]
        service = CorroborationService.__new__(CorroborationService)
        service._compute_confidence(mapping)
        assert mapping.confidence_score < 0.5


class TestOutboundAdapterSecurity:

    def test_ssrf_blocked_for_private_ips(self):
        from fast_api.services.adapters.base_adapter import validate_outbound_url
        assert validate_outbound_url("https://127.0.0.1/api") is False
        assert validate_outbound_url("https://10.0.0.1/api") is False
        assert validate_outbound_url("https://192.168.1.1/api") is False
        assert validate_outbound_url("https://169.254.169.254/metadata") is False
        assert validate_outbound_url("https://localhost/api") is False

    def test_ssrf_blocked_for_internal_hosts(self):
        from fast_api.services.adapters.base_adapter import validate_outbound_url
        assert validate_outbound_url("https://metadata.google.internal/v1") is False
        assert validate_outbound_url("https://evil.internal/steal") is False
        assert validate_outbound_url("https://db.local/admin") is False

    def test_ssrf_blocked_for_http(self):
        from fast_api.services.adapters.base_adapter import validate_outbound_url
        assert validate_outbound_url("http://api.nimc.gov.ng/v1") is False

    def test_safe_https_url_allowed(self):
        from fast_api.services.adapters.base_adapter import validate_outbound_url
        assert validate_outbound_url("https://api.nimc.gov.ng/v1") is True
        assert validate_outbound_url("https://api.nibss.gov.ng/v1") is True

    def test_ftp_blocked(self):
        from fast_api.services.adapters.base_adapter import validate_outbound_url
        assert validate_outbound_url("ftp://files.nimc.gov.ng/data") is False
