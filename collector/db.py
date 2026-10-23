import os

import psycopg


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql:///javahouse")

COLUMNS = [
    "listing_id", "type", "title", "url", "price", "currency", "location",
    "neighborhood", "city", "surface_m2", "rooms", "bedrooms", "bathrooms",
    "amenities", "description",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    source        TEXT        NOT NULL DEFAULT 'mubawab',
    listing_id    TEXT        NOT NULL,
    type          TEXT        NOT NULL DEFAULT 'ad',
    title         TEXT        NOT NULL,
    url           TEXT,
    price         BIGINT,
    currency      TEXT,
    location      TEXT,
    neighborhood  TEXT,
    city          TEXT,
    surface_m2    INTEGER,
    rooms         INTEGER,
    bedrooms      INTEGER,
    bathrooms     INTEGER,
    amenities     TEXT,
    description   TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source, type, listing_id)
);
CREATE INDEX IF NOT EXISTS listings_city_idx ON listings (city, neighborhood);
CREATE INDEX IF NOT EXISTS listings_price_idx ON listings (price);
"""

# Re-scraped listings keep first_seen_at and get their fields and last_seen_at refreshed
UPSERT = f"""
INSERT INTO listings (source, {", ".join(COLUMNS)})
VALUES (%(source)s, {", ".join(f"%({c})s" for c in COLUMNS)})
ON CONFLICT (source, type, listing_id) DO UPDATE SET
    {", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS if c not in ("listing_id", "type"))},
    last_seen_at = now()
"""


def init_db(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
    conn.commit()


def save_listings(listings, source="mubawab", dsn=DATABASE_URL):
    rows = [
        {"source": source, "listing_id": r["id"], **{c: r.get(c) for c in COLUMNS if c != "listing_id"}}
        for r in listings
        if r.get("id")
    ]
    with psycopg.connect(dsn) as conn:
        init_db(conn)
        with conn.cursor() as cur:
            cur.executemany(UPSERT, rows)
    return len(rows)
