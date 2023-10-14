import asyncio
from dataclasses import dataclass
from typing import Optional

from flager import FeatureFlagsProxy


async def main() -> None:
    flags = {"flag_1": False}
    flags_proxy = FeatureFlagsProxy(flags, client=Client())
    print(await flags_proxy["flag_1"])


@dataclass
class Flag:
    key: str
    enabled: Optional[bool]


class Client:
    flags = {"flag_1": Flag("flag_1", True)}

    async def get_flag(self, key: str) -> Optional[Flag]:
        return self.flags[key]


asyncio.run(main())
