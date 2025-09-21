"""Utility helpers for the Workday scraper project."""

from __future__ import annotations

from typing import Iterable


def find_id_by_descriptor(
    facets: Iterable[dict], target_descriptor: str
) -> tuple[str | None, str | None]:
    """Recursively find the ID for a descriptor in Workday facets."""

    normalized_descriptor = target_descriptor.strip().lower()

    for facet in facets:
        facet_parameter = facet.get("facetParameter", "")
        values = facet.get("values", [])

        for value in values:
            descriptor = value.get("descriptor", "").strip().lower()
            if descriptor == normalized_descriptor and "id" in value:
                return facet_parameter, value["id"]

            if "facetParameter" in value and "values" in value:
                nested_facet_parameter = value["facetParameter"]
                nested_values = value["values"]

                found_facet_parameter, found_id = find_id_by_descriptor(
                    [{"facetParameter": nested_facet_parameter, "values": nested_values}],
                    target_descriptor,
                )

                if found_id:
                    return found_facet_parameter, found_id

    return None, None

