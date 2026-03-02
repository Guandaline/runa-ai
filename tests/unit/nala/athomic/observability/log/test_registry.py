from nala.athomic.observability.log.maskers.base_masker import BaseMasker


def test_registry_contains_maskers():
    from nala.athomic.observability.log.registry import MASKER_REGISTRY

    assert len(MASKER_REGISTRY) > 0
    assert all(isinstance(m, (BaseMasker, type)) for m in MASKER_REGISTRY)
