from sqlalchemy import select
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from apps.core.models import Location


DEFAULT_LOCATIONS = [
    {
        "slug": "chamoli",
        "name": "Chamoli",
        "state": "Uttarakhand",
        "latitude": 30.41,
        "longitude": 79.32,
    },
    {
        "slug": "shimla",
        "name": "Shimla",
        "state": "Himachal Pradesh",
        "latitude": 31.10,
        "longitude": 77.17,
    },
    {
        "slug": "gangtok",
        "name": "Gangtok",
        "state": "Sikkim",
        "latitude": 27.33,
        "longitude": 88.61,
    },
    {
        "slug": "itanagar",
        "name": "Itanagar",
        "state": "Arunachal Pradesh",
        "latitude": 27.08,
        "longitude": 93.62,
    },
]


def seed_default_locations(db: Session):
    for item in DEFAULT_LOCATIONS:
        exists = db.scalar(select(Location).where(Location.slug == item["slug"]))
        if not exists:
            point = WKTElement(
                f'POINT({item["longitude"]} {item["latitude"]})',
                srid=4326,
            )
            db.add(Location(**item, geom=point))
    db.commit()


def find_locations(db, query=None):
    stmt = select(Location).order_by(Location.name)
    if query:
        value = f"%{query.strip()}%"
        stmt = stmt.where(
            (Location.name.ilike(value))
            | (Location.state.ilike(value))
            | (Location.slug.ilike(value))
        )
    return list(db.scalars(stmt).all())


def get_or_create_location(
    db,
    slug,
    name,
    state,
    latitude,
    longitude,
):
    location = db.scalar(select(Location).where(Location.slug == slug))
    if location:
        return location

    location = Location(
        slug=slug,
        name=name,
        state=state,
        latitude=latitude,
        longitude=longitude,
        geom=WKTElement(f"POINT({longitude} {latitude})", srid=4326),
    )
    db.add(location)
    db.flush()
    return location
