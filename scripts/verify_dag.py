from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from curriculum.graph import (  # noqa: E402
    get_all_prerequisites,
    get_direct_prerequisites,
    has_cycle,
    load_graph,
    topological_sort,
)


def main() -> int:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript((PROJECT_ROOT / "database" / "schema.sql").read_text(encoding="utf-8"))
        conn.executescript((PROJECT_ROOT / "database" / "seed.sql").read_text(encoding="utf-8"))

        courses, prerequisites = load_graph(conn)
        cyclic = has_cycle(courses, prerequisites)
        order = topological_sort(courses, prerequisites)

        direct_com3026 = get_direct_prerequisites("COM3026", prerequisites)
        all_com3026 = get_all_prerequisites("COM3026", prerequisites)
        direct_com3005 = get_direct_prerequisites("COM3005", prerequisites)
        direct_cftd067 = get_direct_prerequisites("CFTD067", prerequisites)

        print(f"Total courses: {len(courses)}")
        print(f"Total prerequisite edges: {len(prerequisites)}")
        print(f"Valid DAG: {not cyclic}")
        print(f"Topological order preview: {', '.join(order[:15])}")
        print(f"Direct prerequisites of COM3026: {', '.join(direct_com3026)}")
        print(f"All prerequisites of COM3026: {', '.join(all_com3026)}")
        print(f"Direct prerequisites of COM3005: {', '.join(direct_com3005)}")
        print(f"Direct prerequisites of CFTD067: {', '.join(direct_cftd067)}")

        _require("COM2012" in direct_com3026, "COM3026 must directly depend on COM2012")
        _require("COM2002" in get_direct_prerequisites("COM2012", prerequisites), "COM2012 must directly depend on COM2002")
        _require("COM2002" in all_com3026, "COM3026 must indirectly depend on COM2002")
        _require("COM3004" in direct_com3005, "COM3005 must directly depend on COM3004")
        _require("COM3009" in direct_cftd067, "CFTD067 must directly depend on COM3009")
        _require(not cyclic, "Prerequisite graph must be acyclic")

        cftd067_edges = [
            edge
            for edge in prerequisites
            if edge["from_course_id"] == "COM3009" and edge["to_course_id"] == "CFTD067"
        ]
        _require(
            cftd067_edges and cftd067_edges[0]["relation_type"] == "RECOMMENDED",
            "CFTD067 prerequisite edge from COM3009 must be RECOMMENDED",
        )

        print("DAG verification passed.")
        return 0
    finally:
        conn.close()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
