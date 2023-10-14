# Flager

[![PyPI](https://img.shields.io/pypi/v/flager)](https://pypi.org/project/flager/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/flager)](https://www.python.org/downloads/)
[![GitHub last commit](https://img.shields.io/github/last-commit/daxartio/flager)](https://github.com/daxartio/flager)
[![GitHub stars](https://img.shields.io/github/stars/daxartio/flager?style=social)](https://github.com/daxartio/flager)

Feature flags updater for python

## Installation

```
pip install flager
```

## Features

- Anyio
- Abstract code for any backend, e.g., flipt, redis, etc.

## Usage

feature flags updater

```python
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
```

feature flag proxy

```python
from flager import FeatureFlagsProxy


async def main() -> None:
    flags = {"flag_1": False}
    flags_proxy = FeatureFlagsProxy(flags, client=Client())
    print(await flags_proxy["flag_1"])
```

## License

* [MIT LICENSE](LICENSE)

## Contribution

[Contribution guidelines for this project](CONTRIBUTING.md)
