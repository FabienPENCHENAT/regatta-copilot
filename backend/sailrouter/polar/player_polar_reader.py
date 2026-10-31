from __future__ import annotations

import json
from collections import deque
from typing import Any

from sailrouter.polar.vr_polar_parser import SAIL_NAMES_BY_ID, VrPolarParser

POLAR_KEYS = ("sail", "tws", "twa")
MAX_DEPTH = 8


class InvalidPolarError(ValueError):
    """The JSON pasted by the player holds no usable VR polar; the message says what is wrong."""


class PlayerPolarReader:
    """Finds the VR polar in the JSON the player copied from the game's network tab (the raw polar, or a wrapper
    such as a `LogEventResponse` with the polar nested at any depth, possibly as a JSON string) and checks that
    the routing engine can use it: 7 sails, speed tables matching the TWS/TWA axes, a `winch` block.

    Returns only the polar object: anything else in the wrapper (session data...) is never kept.
    """

    def read(self, payload: Any) -> dict[str, Any]:
        polar = self._find(payload)
        if polar is None:
            raise InvalidPolarError("no VR polar found: expected an object with 'sail', 'tws' and 'twa'")
        self._check(polar)
        return polar

    @staticmethod
    def _find(payload: Any) -> dict[str, Any] | None:
        """Breadth-first: the shallowest object holding the polar keys."""
        queue = deque([(payload, 0)])
        while queue:
            value, depth = queue.popleft()
            if isinstance(value, str) and value.lstrip().startswith(("{", "[")):
                try:
                    value = json.loads(value)
                except ValueError:
                    continue
            if isinstance(value, dict):
                if all(key in value for key in POLAR_KEYS):
                    return value
                children = value.values()
            elif isinstance(value, list):
                children = value
            else:
                continue
            if depth < MAX_DEPTH:
                queue.extend((child, depth + 1) for child in children)
        return None

    @staticmethod
    def _check(polar: dict[str, Any]) -> None:
        sails = polar["sail"]
        if not isinstance(sails, list) or len(sails) != len(SAIL_NAMES_BY_ID):
            raise InvalidPolarError(f"the polar must have {len(SAIL_NAMES_BY_ID)} sails")
        if "winch" not in polar:
            raise InvalidPolarError("the polar has no 'winch' block (manoeuvre times)")
        try:
            ids = sorted(int(sail.get("id", sail.get("_id"))) for sail in sails)
            if ids != sorted(SAIL_NAMES_BY_ID):
                raise InvalidPolarError(f"sail ids must be 1 to 7, got {ids}")
            VrPolarParser().parse(polar)
        except InvalidPolarError:
            raise
        except KeyError as error:
            raise InvalidPolarError(f"the polar misses the field {error}") from error
        except (TypeError, ValueError, AttributeError) as error:
            raise InvalidPolarError(f"the polar tables are not consistent: {error}") from error
