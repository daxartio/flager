import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

from flager import FeatureFlagsUpdater


async def show_flags(flags: Dict[str, bool]) -> None:
    while True:
        print(flags)
        await asyncio.sleep(1)


async def main() -> None:
    flags = {"flag_1": False}
    ff_updater = FeatureFlagsUpdater([flags], client=Client(), interval=5)
    await asyncio.gather(ff_updater.run(), show_flags(flags))


@dataclass
class Flag:
    key: str
    enabled: Optional[bool]


class Client:
    flags = {"flag_1": Flag("flag_1", True)}

    async def get_flag(self, key: str) -> Optional[Flag]:
        return self.flags[key]


asyncio.run(main())
