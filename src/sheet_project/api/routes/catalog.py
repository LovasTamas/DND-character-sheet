"""Read-only, cacheable catalog endpoints.

Per docs/webui-architecture.md#Catalog, these never change at runtime,
so every response gets `Cache-Control: public, max-age=3600`.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query, Response

from sheet_project.engine.backgrounds.background_loader import BackgroundLoader
from sheet_project.engine.classes.class_loader import ClassLoader
from sheet_project.engine.equipment.armor_loader import ArmorLoader
from sheet_project.engine.equipment.item_loader import ItemLoader
from sheet_project.engine.equipment.weapon_loader import WeaponLoader
from sheet_project.engine.features.feat_loader import FeatLoader
from sheet_project.engine.races.race_loader import RaceLoader
from sheet_project.engine.subclasses.subclass_loader import SubclassLoader

router = APIRouter(prefix="/catalog", tags=["catalog"])

CACHE_CONTROL = "public, max-age=3600"


def _set_cache(response: Response) -> None:
    response.headers["Cache-Control"] = CACHE_CONTROL


def _filter_by_q(items: List[dict], q: Optional[str]) -> List[dict]:
    if not q:
        return items
    needle = q.lower()
    return [
        item
        for item in items
        if needle in str(item.get("id", "")).lower() or needle in str(item.get("name", "")).lower()
    ]


@router.get("/classes")
def get_classes(response: Response) -> List[dict]:
    _set_cache(response)
    return ClassLoader.list_classes()


@router.get("/races")
def get_races(response: Response) -> List[dict]:
    _set_cache(response)
    return RaceLoader.list_races()


@router.get("/backgrounds")
def get_backgrounds(response: Response) -> List[dict]:
    _set_cache(response)
    return BackgroundLoader.list_backgrounds()


@router.get("/subclasses")
def get_subclasses(response: Response, class_id: str = Query(...)) -> List[dict]:
    _set_cache(response)
    return SubclassLoader().list_for_class(class_id)


@router.get("/feats")
def get_feats(response: Response) -> List[dict]:
    _set_cache(response)
    return FeatLoader.list_feats()


@router.get("/weapons")
def get_weapons(response: Response, q: Optional[str] = Query(None)) -> List[dict]:
    _set_cache(response)
    return _filter_by_q(WeaponLoader.list_weapons(), q)


@router.get("/armors")
def get_armors(response: Response, q: Optional[str] = Query(None)) -> List[dict]:
    _set_cache(response)
    return _filter_by_q(ArmorLoader.list_armors(), q)


@router.get("/items")
def get_items(response: Response, q: Optional[str] = Query(None)) -> List[dict]:
    _set_cache(response)
    return _filter_by_q(ItemLoader.list_items(), q)


@router.get("/fighting-styles")
def get_fighting_styles(response: Response) -> List[dict]:
    _set_cache(response)
    # No fighting-styles data file exists yet in data/ - content TBD by
    # PLAN_webui_backend.md followups. Empty list keeps the contract stable.
    return []
