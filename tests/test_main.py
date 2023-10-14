from dataclasses import dataclass
from typing import Any, Optional

import pytest

from flager.exceptions import FeatureFlagNotDefined, FeatureFlagNotFound
from flager.main import FeatureFlagsProxy, FeatureFlagsUpdater


@dataclass
class Flag:
    key: str
    enabled: Optional[bool]


@pytest.mark.asyncio
async def test_feature_flag_updater_interval_error(mocker: Any) -> None:
    with pytest.raises(ValueError):
        FeatureFlagsUpdater([], client=mocker.Mock(), interval=-1)


@pytest.mark.asyncio
async def test_feature_flag_updater() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", True)

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater([flags], client=Client(), interval=1)
    await ff_updater.update_feature_flags()

    assert flags == {"flag_1": True}


@pytest.mark.asyncio
async def test_feature_flag_updater_skip() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", False)

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater([flags], client=Client(), interval=1)
    await ff_updater.update_feature_flags()

    assert flags == {"flag_1": False}


@pytest.mark.asyncio
async def test_feature_flag_updater_skip_client_errors() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            raise ValueError

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater([flags], client=Client(), interval=1)
    await ff_updater.update_feature_flags()

    assert flags == {"flag_1": False}


@pytest.mark.asyncio
async def test_feature_flag_updater_client_errors() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            raise ValueError

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater(
        [flags], client=Client(), interval=1, skip_client_errors=False
    )
    with pytest.raises(ValueError):
        await ff_updater.update_feature_flags()

    assert flags == {"flag_1": False}


@pytest.mark.asyncio
async def test_feature_flag_updater_skip_not_found_error() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return None

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater([flags], client=Client(), interval=1)
    await ff_updater.update_feature_flags()

    assert flags == {"flag_1": False}


@pytest.mark.asyncio
async def test_feature_flag_updated_not_found_error() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return None

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater(
        [flags], client=Client(), interval=1, skip_not_found_error=False
    )
    with pytest.raises(FeatureFlagNotFound):
        await ff_updater.update_feature_flags()

    assert flags == {"flag_1": False}


@pytest.mark.asyncio
async def test_feature_flag_updater_skip_not_defined_error() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", None)

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater([flags], client=Client(), interval=1)
    await ff_updater.update_feature_flags()

    assert flags == {"flag_1": False}


@pytest.mark.asyncio
async def test_feature_flag_updater_not_defined_error() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", None)

    flags = {"flag_1": False}

    ff_updater = FeatureFlagsUpdater(
        [flags], client=Client(), interval=1, skip_not_defined_error=False
    )
    with pytest.raises(FeatureFlagNotDefined):
        await ff_updater.update_feature_flags()

    assert flags == {"flag_1": False}


@pytest.mark.asyncio
async def test_feature_flag_proxy() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", True)

    flags = {"flag_1": False}

    flags_proxy = FeatureFlagsProxy(flags, client=Client())

    assert await flags_proxy["flag_1"] is True


@pytest.mark.asyncio
async def test_feature_flag_proxy_skip() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", False)

    flags = {"flag_1": False}

    flags_proxy = FeatureFlagsProxy(flags, client=Client())

    assert await flags_proxy["flag_1"] is False


@pytest.mark.asyncio
async def test_feature_flag_proxy_skip_not_found() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return None

    flags = {"flag_1": False}

    flags_proxy = FeatureFlagsProxy(flags, client=Client())

    assert await flags_proxy["flag_1"] is False


@pytest.mark.asyncio
async def test_feature_flag_proxy_not_found() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return None

    flags = {"flag_1": False}

    flags_proxy = FeatureFlagsProxy(flags, client=Client(), skip_not_found_error=False)

    with pytest.raises(FeatureFlagNotFound):
        assert await flags_proxy["flag_1"]


@pytest.mark.asyncio
async def test_feature_flag_proxy_skip_not_defind() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", None)

    flags = {"flag_1": False}

    flags_proxy = FeatureFlagsProxy(flags, client=Client())

    assert await flags_proxy["flag_1"] is False


@pytest.mark.asyncio
async def test_feature_flag_proxy_not_defind() -> None:
    class Client:
        async def get_flag(self, key: str) -> Optional[Flag]:
            assert key == "flag_1"
            return Flag("flag_1", None)

    flags = {"flag_1": False}

    flags_proxy = FeatureFlagsProxy(
        flags, client=Client(), skip_not_defined_error=False
    )

    with pytest.raises(FeatureFlagNotDefined):
        assert await flags_proxy["flag_1"]
