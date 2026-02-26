"""
Example: run auto-swipe (after filling discovery + swipe endpoints in config).
Usage (from backend): python -m examples.auto_swipe_example
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from okcupid_api import OkCupidClient
from okcupid_api import swipe


def main() -> None:
    from okcupid_api.load_sample import get_graphql_settings, get_swipe_settings

    client = OkCupidClient.from_sample()
    swipe_cfg = get_swipe_settings()
    gql_cfg = get_graphql_settings()
    # Support multiple directions in a single run:
    # Priority:
    #   1) SWIPE_DIRECTIONS env var (comma-separated)
    #   2) swipe.directions in sample.json (list)
    #   3) SWIPE_DIRECTION env var
    #   4) swipe.direction in sample.json (string, legacy)
    directions_env = os.getenv("SWIPE_DIRECTIONS")
    if directions_env:
        directions = [d.strip() for d in directions_env.split(",") if d.strip()]
    else:
        cfg_dirs = swipe_cfg.get("directions")
        if isinstance(cfg_dirs, list) and cfg_dirs:
            directions = [str(d).strip() for d in cfg_dirs if str(d).strip()]
        else:
            directions = [os.getenv("SWIPE_DIRECTION") or swipe_cfg.get("direction", "like")]

    max_swipes = int(os.getenv("MAX_SWIPES") or swipe_cfg.get("max_swipes", 10))
    like_pct = swipe_cfg.get("like_percentage")
    delay = float(os.getenv("SWIPE_DELAY") or swipe_cfg.get("delay_seconds", 1.5))
    discovery_path = gql_cfg.get("discovery_path") or None
    initial_stacks_path = gql_cfg.get("initial_stacks_path") or None
    swipe_path = gql_cfg.get("swipe_path") or None

    def on_swipe(user_id: str, dir: str, resp: dict) -> None:
        print(f"  {dir} -> {user_id}")

    def on_error(uid: str, err: Exception) -> None:
        print(f"  error for {uid}: {err}")

    totals = {}
    for direction in directions:
        # If both pass and like are present and like_percentage is set,
        # split the total max_swipes between them.
        dir_max = max_swipes
        if (
            isinstance(like_pct, (int, float))
            and "like" in directions
            and "pass" in directions
            and len(directions) == 2
        ):
            like_count = int(round(max_swipes * (float(like_pct) / 100.0)))
            like_count = max(0, min(max_swipes, like_count))
            pass_count = max_swipes - like_count
            if direction == "like":
                dir_max = like_count
            elif direction == "pass":
                dir_max = pass_count

        print(f"Auto-swipe: direction={direction}, max={dir_max}, delay={delay}s")
        summary = swipe.auto_swipe(
            client,
            direction=direction,
            max_swipes=dir_max,
            delay_seconds=delay,
            discovery_graphql_path=discovery_path,
            initial_stacks_path=initial_stacks_path,
            swipe_graphql_path=swipe_path,
            on_swipe=on_swipe,
            on_error=on_error,
        )
        totals[direction] = summary
        print(
            f"Done ({direction}): swiped={summary['swiped']}, skipped={summary['skipped']}, errors={summary['errors']}"
        )

    if len(directions) > 1:
        print("Summary by direction:")
        for d in directions:
            s = totals[d]
            print(f"  {d}: swiped={s['swiped']}, skipped={s['skipped']}, errors={s['errors']}")


if __name__ == "__main__":
    main()
