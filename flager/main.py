import logging
from typing import Any, Dict, Iterable, List, Optional, Protocol, Set, Union

import anyio

from .exceptions import FeatureFlagNotDefined, FeatureFlagNotFound

__all__ = (
    "FeatureFlagsProxy",
    "FeatureFlagsUpdater",
)

logger = logging.getLogger(__name__)


class Flag(Protocol):
    key: str
    enabled: Optional[bool]


class FeatureFlags(Protocol):  # pragma:no cover
    def keys(self) -> Iterable[str]:
        ...

    def __setitem__(self, key: str, item: bool) -> None:
        ...

    def __getitem__(self, key: str) -> bool:
        ...


class Client(Protocol):
    async def get_flag(self, key: str) -> Optional[Flag]:  # pragma:no cover
        ...


class FeatureFlagsProxy:
    """Proxy for feature flags.

    A FeatureFlagsProxy class that acts as a proxy for feature flags.
    It takes a dictionary of feature flags as input and a Client object
    that is used to retrieve the feature flags from a server.
    The __getitem__ method is overridden to return the value of a feature flag.
    If the value is not in the cache, it is retrieved from the server using the get_flag
    method of the Client object.
    If the flag is not found on the server,
    a FeatureFlagNotFound exception is raised,
    unless the skip_not_found_error parameter is set to True.
    If the flag is found, its value is returned.
    """

    def __init__(
        self,
        feature_flags: FeatureFlags,
        *,
        client: Client,
        skip_not_defined_error: bool = True,
        skip_not_found_error: bool = True,
    ) -> None:
        self._feature_flags = feature_flags
        self._client = client
        self._skip_not_found_error = skip_not_found_error
        self._skip_not_defined_error = skip_not_defined_error
        self._cache: Dict[str, bool] = {}

    def __getitem__(self, key: str) -> Any:
        original_val = self._feature_flags[key]
        val = self._cache.get(key, original_val)
        return self._get_from_server(key, val)

    async def _get_from_server(self, key: str, default: bool) -> bool:
        flag = await self._client.get_flag(key)
        if not flag:
            if not self._skip_not_found_error:
                raise FeatureFlagNotFound(f"Feature flag {key} not found")
            logger.warning("Feature flag %s not found", key)
            return default
        if flag.enabled is None:
            if not self._skip_not_defined_error:
                raise FeatureFlagNotDefined(f"Feature flag {key} is None")
            logger.warning("Feature flag %s is None", key)
            return default
        if flag.enabled == default:
            return default
        logger.info(
            "Feature flag %s was changed from %s to %s",
            key,
            str(default),
            str(flag.enabled),
        )
        self._cache[key] = flag.enabled
        return flag.enabled


class FeatureFlagsUpdater:
    """Feature flags updater.

    A FeatureFlagsUpdater class that is responsible
    for updating the feature flags periodically.
    It takes a list of FeatureFlags objects as input,
    along with a Client object that is used to retrieve the feature flags from a server.
    The interval parameter specifies the time interval (in seconds) between updates.
    The skip_client_errors, skip_not_defined_error, and skip_not_found_error parameters
    control whether errors are skipped
    when retrieving the feature flags from the server.
    """

    def __init__(
        self,
        feature_flags: List[FeatureFlags],
        *,
        client: Client,
        interval: int,
        skip_client_errors: bool = True,
        skip_not_defined_error: bool = True,
        skip_not_found_error: bool = True,
    ) -> None:
        if interval < 0:
            raise ValueError("interval should be > 0")
        self._client = client
        self._feature_flags = feature_flags
        self._skip_client_errors = skip_client_errors
        self._skip_not_found_error = skip_not_found_error
        self._skip_not_defined_error = skip_not_defined_error
        self._interval = interval
        self._keys = self._get_keys()
        self._stoped = False

    def _get_keys(self) -> List[str]:
        keys: Set[str] = set()
        for feature_flags in self._feature_flags:
            for key in feature_flags.keys():
                keys.add(key)
        return list(keys)

    def _update_feature_flags(self, flags_by_keys: Dict[str, bool]) -> None:
        for feature_flags in self._feature_flags:
            for key in feature_flags.keys():
                if key not in flags_by_keys:
                    continue
                current_val = feature_flags[key]
                new_val = flags_by_keys[key]
                if current_val != new_val:
                    feature_flags[key] = new_val
                    logger.info(
                        "Feature flag %s was changed from %s to %s",
                        key,
                        str(current_val),
                        str(new_val),
                    )

    async def _get_flag(
        self, flags: List[Union[Flag, Exception, None]], key: str
    ) -> None:
        try:
            flags.append(await self._client.get_flag(key))
        except Exception as e:
            flags.append(e)

    async def update_feature_flags(self) -> None:
        keys = self._keys.copy()
        flags: List[Union[Flag, Exception, None]] = []
        async with anyio.create_task_group() as tg:
            for key in keys:
                tg.start_soon(self._get_flag, flags, key)

        flags_by_keys: Dict[str, bool] = {}
        for i, flag in enumerate(flags):
            if isinstance(flag, Exception):
                if not self._skip_client_errors:
                    raise flag
                logger.error("Fetch feature flag error: %s", str(flag))
                continue
            if not flag:
                key = keys[i]
                if not self._skip_not_found_error:
                    raise FeatureFlagNotFound(f"Feature flag {key} not found")
                logger.warning("Feature flag %s not found", key)
                continue
            if flag.enabled is None:
                key = keys[i]
                if not self._skip_not_defined_error:
                    raise FeatureFlagNotDefined(f"Feature flag {key} is None")
                logger.warning("Feature flag %s is None", key)
                continue
            flags_by_keys[flag.key] = flag.enabled
        self._update_feature_flags(flags_by_keys)
        return

    def stop(self) -> None:  # pragma: no cover
        self._stoped = True

    async def run(self) -> None:  # pragma: no cover
        while not self._stoped:
            await self.update_feature_flags()
            await anyio.sleep(self._interval)
