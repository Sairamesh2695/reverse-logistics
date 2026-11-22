"""
Reverse Logistics Synthetic Data Generator
==========================================
Generates master data, transactional data, edge cases, and ground truth
for the Reverse Logistics / Reusable Asset Tracking system.

Usage:
    python generate_data.py --seed 20261022 --scale full
    python generate_data.py --seed 20261022 --scale starter

Fixed seed: 20261022
Full scale: 20,000 assets, 10,000 shipments, 100,000 custody events
Starter scale: 200 assets, 100 shipments, 1,000 custody events
"""

import csv
import json
import hashlib
import os
import argparse
import random
import math
from datetime import datetime, timedelta
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

SCALE_CONFIG = {
    "full":    {"assets": 20000, "shipments": 10000, "custody_events": 100000},
    "starter": {"assets": 200,   "shipments": 100,   "custody_events": 1000},
}

FIXED_SEED = 20261022
OUTPUT_DIR = "output"

# Enumerations
ASSET_TYPE_CATEGORIES = ["Pallet", "Crate", "Container", "Tote", "Drum", "Roll Cage", "IBC", "Reel"]
LIFECYCLE_STATES      = ["active", "in_transit", "at_location", "under_repair", "lost", "retired", "decommissioned"]
DAMAGE_LEVELS         = ["none", "minor", "moderate", "severe"]
INSPECTION_RESULTS    = ["pass", "fail", "conditional_pass"]
REPAIR_STATUSES       = ["open", "in_progress", "completed", "cancelled"]
RA_STATUSES           = ["pending", "approved", "in_transit", "received", "closed", "disputed"]
CUSTODY_EVENT_TYPES   = ["dispatch", "in_transit", "received", "transfer", "return", "inspection_checkpoint"]
OWNER_TYPES           = ["supplier", "carrier", "warehouse", "customer", "third_party_logistics"]
LOCATION_TYPES        = ["warehouse", "distribution_center", "supplier_site", "customer_site", "port", "repair_center"]
DEPOSIT_TYPES         = ["charge", "refund", "adjustment", "penalty"]
CURRENCY              = "USD"

BASE_DATE = datetime(2026, 1, 1)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def fmt_date(dt):
    return dt.strftime("%Y-%m-%d")

def fmt_datetime(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def rnd_date(rng, start, end):
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, max(0, delta)))

def rnd_datetime(rng, start, end):
    delta = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, max(0, delta)))

def days_between(d1_str, d2_str):
    try:
        d1 = datetime.strptime(d1_str[:10], "%Y-%m-%d")
        d2 = datetime.strptime(d2_str[:10], "%Y-%m-%d")
        return (d2 - d1).days
    except Exception:
        return 0

def write_csv(path, rows, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows):>7,} rows -> {path}")

def file_checksum(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — MASTER / PARENT TABLES
# ─────────────────────────────────────────────────────────────────────────────

def gen_asset_types(rng):
    rows = []
    at_id = 1
    for cat in ASSET_TYPE_CATEGORIES:
        for variant in range(1, rng.randint(3, 6)):
            max_life = rng.randint(60, 1200)   # days
            deposit  = round(rng.uniform(5, 500), 2)
            rows.append({
                "asset_type_id":          f"AT-{at_id:04d}",
                "category":               cat,
                "variant_name":           f"{cat}-V{variant}",
                "description":            f"{cat} variant {variant} for logistics use",
                "max_capacity_kg":        round(rng.uniform(50, 2000), 1),
                "tare_weight_kg":         round(rng.uniform(2, 150), 1),
                "material":               rng.choice(["plastic", "wood", "steel", "aluminium", "composite"]),
                "max_lifetime_days":      max_life,
                "inspection_interval_days": rng.randint(30, 180),
                "deposit_amount_usd":     deposit,
                "is_returnable":          "true",
                "lifecycle_rule":         rng.choice(["reuse_until_damaged", "fixed_cycles", "age_based"]),
                "max_reuse_cycles":       rng.randint(10, 500),
                "created_at":             fmt_date(BASE_DATE),
            })
            at_id += 1
    return rows

def gen_owners(rng, n=120):
    rows = []
    for i in range(1, n + 1):
        otype = rng.choice(OWNER_TYPES)
        rows.append({
            "owner_id":      f"OWN-{i:05d}",
            "owner_name":    f"{otype.replace('_',' ').title()} Corp {i}",
            "owner_type":    otype,
            "contact_email": f"contact{i}@owner{i}.example.com",
            "contact_phone": f"+1-555-{rng.randint(1000,9999)}-{rng.randint(1000,9999)}",
            "country":       rng.choice(["US", "DE", "CN", "IN", "GB", "JP", "AU", "CA", "MX", "BR"]),
            "is_active":     "true",
            "created_at":    fmt_date(rnd_date(rng, BASE_DATE - timedelta(days=365*3), BASE_DATE)),
        })
    return rows

def gen_locations(rng, n=80):
    rows = []
    for i in range(1, n + 1):
        ltype = rng.choice(LOCATION_TYPES)
        rows.append({
            "location_id":   f"LOC-{i:05d}",
            "location_name": f"{ltype.replace('_',' ').title()} {i}",
            "location_type": ltype,
            "address_line1": f"{rng.randint(1,9999)} Industrial Blvd",
            "city":          rng.choice(["Chicago", "Hamburg", "Shanghai", "Mumbai", "London", "Tokyo", "Sydney", "Toronto", "Mexico City", "São Paulo"]),
            "country":       rng.choice(["US", "DE", "CN", "IN", "GB", "JP", "AU", "CA", "MX", "BR"]),
            "latitude":      round(rng.uniform(-60, 70), 6),
            "longitude":     round(rng.uniform(-180, 180), 6),
            "capacity_units": rng.randint(100, 50000),
            "is_active":     "true",
            "created_at":    fmt_date(rnd_date(rng, BASE_DATE - timedelta(days=365*3), BASE_DATE)),
        })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — REUSABLE ASSETS
# ─────────────────────────────────────────────────────────────────────────────

def gen_assets(rng, asset_types, owners, locations, n_assets):
    rows = []
    at_ids   = [a["asset_type_id"]   for a in asset_types]
    own_ids  = [o["owner_id"]        for o in owners]
    loc_ids  = [l["location_id"]     for l in locations]

    for i in range(1, n_assets + 1):
        at = rng.choice(asset_types)
        manufacture_date = rnd_date(rng, BASE_DATE - timedelta(days=365*5), BASE_DATE - timedelta(days=30))
        state = rng.choices(
            LIFECYCLE_STATES,
            weights=[40, 10, 25, 5, 3, 7, 10],
            k=1
        )[0]
        rows.append({
            "asset_id":               f"ASSET-{i:07d}",
            "asset_type_id":          at["asset_type_id"],
            "serial_number":          f"SN-{rng.randint(100000,9999999):07d}",
            "owner_id":               rng.choice(own_ids),
            "current_location_id":    rng.choice(loc_ids),
            "manufacture_date":       fmt_date(manufacture_date),
            "last_inspection_date":   fmt_date(rnd_date(rng, manufacture_date, BASE_DATE)),
            "lifecycle_state":        state,
            "damage_level":           rng.choice(DAMAGE_LEVELS) if state in ["under_repair","retired"] else rng.choices(DAMAGE_LEVELS, weights=[70,20,8,2], k=1)[0],
            "reuse_cycle_count":      rng.randint(0, int(at["max_reuse_cycles"])),
            "is_lost":                "true" if state == "lost" else "false",
            "deposit_held_usd":       at["deposit_amount_usd"],
            "created_at":             fmt_date(manufacture_date),
            "updated_at":             fmt_date(BASE_DATE),
        })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — SHIPMENTS
# ─────────────────────────────────────────────────────────────────────────────

def gen_shipments(rng, owners, locations, n_shipments):
    rows = []
    own_ids = [o["owner_id"]   for o in owners]
    loc_ids = [l["location_id"] for l in locations]

    for i in range(1, n_shipments + 1):
        origin      = rng.choice(loc_ids)
        destination = rng.choice([l for l in loc_ids if l != origin])
        planned_dep = rnd_date(rng, BASE_DATE, BASE_DATE + timedelta(days=180))
        planned_arr = planned_dep + timedelta(days=rng.randint(1, 30))
        late = rng.random() < 0.15
        actual_arr_offset = rng.randint(1, 20) if late else rng.randint(-1, 2)
        actual_arr = planned_arr + timedelta(days=actual_arr_offset)
        carrier_id = rng.choice(own_ids)
        rows.append({
            "shipment_id":         f"SHP-2026-{i:06d}",
            "origin_location_id":  origin,
            "dest_location_id":    destination,
            "carrier_id":          carrier_id,
            "shipper_id":          rng.choice(own_ids),
            "planned_departure":   fmt_date(planned_dep),
            "actual_departure":    fmt_date(planned_dep + timedelta(days=rng.randint(0, 2))),
            "planned_arrival":     fmt_date(planned_arr),
            "actual_arrival":      fmt_date(actual_arr),
            "status":              rng.choice(["scheduled","in_transit","delivered","cancelled","delayed"]),
            "mode":                rng.choice(["road","rail","air","sea","multimodal"]),
            "total_assets":        rng.randint(1, 200),
            "is_return_shipment":  rng.choice(["true","false"]),
            "created_at":          fmt_date(planned_dep - timedelta(days=rng.randint(1,10))),
        })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — CUSTODY EVENTS
# ─────────────────────────────────────────────────────────────────────────────

def gen_custody_events(rng, assets, shipments, owners, locations, n_events):
    rows = []
    asset_ids   = [a["asset_id"]     for a in assets]
    shp_ids     = [s["shipment_id"]  for s in shipments]
    own_ids     = [o["owner_id"]     for o in owners]
    loc_ids     = [l["location_id"]  for l in locations]

    # Track last event per asset for counter
    asset_ctr = defaultdict(int)
    asset_last_time = {}

    total = n_events
    for i in range(1, total + 1):
        asset_id = rng.choice(asset_ids)
        asset_ctr[asset_id] += 1
        ctr = asset_ctr[asset_id]
        event_id = f"CUST-{asset_id}-{ctr:06d}"

        # Advance time
        last_dt = asset_last_time.get(asset_id, BASE_DATE)
        event_dt = last_dt + timedelta(hours=rng.randint(1, 72))
        asset_last_time[asset_id] = event_dt

        actor_id = rng.choice(own_ids) if rng.random() > 0.02 else ""   # 2% missing actor (edge case injected later cleanly)
        rows.append({
            "event_id":           event_id,
            "asset_id":           asset_id,
            "event_type":         rng.choice(CUSTODY_EVENT_TYPES),
            "event_timestamp":    fmt_datetime(event_dt),
            "from_location_id":   rng.choice(loc_ids),
            "to_location_id":     rng.choice(loc_ids),
            "actor_id":           actor_id,
            "shipment_id":        rng.choice(shp_ids) if rng.random() > 0.1 else "",
            "notes":              "",
            "is_disputed":        "true" if rng.random() < 0.03 else "false",
            "created_at":         fmt_datetime(event_dt),
        })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — RETURN AUTHORIZATIONS
# ─────────────────────────────────────────────────────────────────────────────

def gen_return_authorizations(rng, assets, owners, locations, shipments):
    rows = []
    n = max(1, int(len(assets) * 0.35))
    asset_sample = rng.sample(assets, n)
    own_ids = [o["owner_id"]   for o in owners]
    loc_ids = [l["location_id"] for l in locations]
    shp_ids = [s["shipment_id"] for s in shipments]

    for idx, asset in enumerate(asset_sample, 1):
        issued = rnd_date(rng, BASE_DATE + timedelta(days=1), BASE_DATE + timedelta(days=120))
        due    = issued + timedelta(days=rng.randint(7, 60))
        status = rng.choice(RA_STATUSES)
        rows.append({
            "rma_id":              f"RMA-2026-{idx:06d}",
            "asset_id":            asset["asset_id"],
            "issued_by_owner_id":  rng.choice(own_ids),
            "return_to_location_id": rng.choice(loc_ids),
            "shipment_id":         rng.choice(shp_ids) if rng.random() > 0.1 else "",
            "issued_date":         fmt_date(issued),
            "due_date":            fmt_date(due),
            "received_date":       fmt_date(rnd_date(rng, due - timedelta(days=5), due + timedelta(days=30))) if status in ["received","closed"] else "",
            "status":              status,
            "reason":              rng.choice(["end_of_lease","damaged","wrong_delivery","overstock","recall"]),
            "days_outstanding":    "",   # derived below
            "is_overdue":          "",   # derived below
            "created_at":          fmt_date(issued),
        })

    # Derive days_outstanding and is_overdue
    today_str = fmt_date(BASE_DATE + timedelta(days=180))
    for row in rows:
        ref_date = row["received_date"] if row["received_date"] else today_str
        row["days_outstanding"] = days_between(row["issued_date"], ref_date)
        due_days = days_between(row["issued_date"], row["due_date"])
        row["is_overdue"] = "true" if row["days_outstanding"] > due_days and row["status"] not in ["closed","received"] else "false"

    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — INSPECTIONS
# ─────────────────────────────────────────────────────────────────────────────

def gen_inspections(rng, assets, owners, locations):
    rows = []
    n = max(1, int(len(assets) * 0.6))
    asset_sample = rng.sample(assets, n)
    own_ids = [o["owner_id"]   for o in owners]
    loc_ids = [l["location_id"] for l in locations]
    insp_ctr = defaultdict(int)

    for asset in asset_sample:
        num_insp = rng.randint(1, 5)
        last_dt = datetime.strptime(asset["manufacture_date"], "%Y-%m-%d")
        for _ in range(num_insp):
            last_dt += timedelta(days=rng.randint(30, 200))
            if last_dt > BASE_DATE + timedelta(days=180):
                break
            insp_ctr[asset["asset_id"]] += 1
            ctr = insp_ctr[asset["asset_id"]]
            result = rng.choices(INSPECTION_RESULTS, weights=[70,20,10], k=1)[0]
            rows.append({
                "inspection_id":      f"INSP-{asset['asset_id']}-{ctr:04d}",
                "asset_id":           asset["asset_id"],
                "inspector_id":       rng.choice(own_ids),
                "location_id":        rng.choice(loc_ids),
                "inspection_date":    fmt_date(last_dt),
                "result":             result,
                "damage_level":       rng.choice(DAMAGE_LEVELS) if result == "fail" else rng.choices(DAMAGE_LEVELS, weights=[80,15,4,1], k=1)[0],
                "notes":              f"Inspection #{ctr} result: {result}",
                "next_inspection_due": fmt_date(last_dt + timedelta(days=rng.randint(30,180))),
                "created_at":         fmt_date(last_dt),
            })
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — REPAIRS
# ─────────────────────────────────────────────────────────────────────────────

def gen_repairs(rng, inspections, owners, locations):
    rows = []
    # Repairs for failed or conditional-pass inspections
    failed = [i for i in inspections if i["result"] in ["fail", "conditional_pass"]]
    rep_ctr = 1
    own_ids = [o["owner_id"]   for o in owners]
    loc_ids = [l["location_id"] for l in locations]

    for insp in failed:
        start = datetime.strptime(insp["inspection_date"], "%Y-%m-%d") + timedelta(days=rng.randint(1, 10))
        status = rng.choice(REPAIR_STATUSES)
        end_date = ""
        if status == "completed":
            end_date = fmt_date(start + timedelta(days=rng.randint(1, 30)))
        rows.append({
            "repair_id":           f"REP-2026-{rep_ctr:06d}",
            "asset_id":            insp["asset_id"],
            "inspection_id":       insp["inspection_id"],
            "repair_facility_id":  rng.choice(loc_ids),
            "technician_id":       rng.choice(own_ids),
            "start_date":          fmt_date(start),
            "end_date":            end_date,
            "status":              status,
            "repair_type":         rng.choice(["structural","cleaning","component_replacement","cosmetic","electrical"]),
            "cost_usd":            round(rng.uniform(10, 2000), 2),
            "parts_replaced":      rng.choice(["none","bracket","corner_piece","locking_pin","base_plate","wall_panel"]),
            "created_at":          fmt_date(start),
        })
        rep_ctr += 1
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — DEPOSIT LEDGER
# ─────────────────────────────────────────────────────────────────────────────

def gen_deposit_ledger(rng, assets, return_authorizations, owners):
    rows = []
    ledger_ctr = 1
    own_ids = [o["owner_id"] for o in owners]

    # Charges on asset creation
    for asset in assets:
        rows.append({
            "ledger_id":     f"DEP-{ledger_ctr:08d}",
            "asset_id":      asset["asset_id"],
            "rma_id":        "",
            "owner_id":      asset["owner_id"],
            "event_type":    "charge",
            "amount_usd":    asset["deposit_held_usd"],
            "currency":      CURRENCY,
            "event_date":    asset["created_at"],
            "balance_after": asset["deposit_held_usd"],
            "notes":         "Initial deposit charge on asset creation",
            "created_at":    asset["created_at"],
        })
        ledger_ctr += 1

    # Refunds on closed RMAs
    closed_rmas = [r for r in return_authorizations if r["status"] in ["closed", "received"]]
    for rma in closed_rmas:
        # find asset deposit
        deposit = float(next((a["deposit_held_usd"] for a in assets if a["asset_id"] == rma["asset_id"]), 0))
        refund_date = rma["received_date"] or rma["due_date"]
        rows.append({
            "ledger_id":     f"DEP-{ledger_ctr:08d}",
            "asset_id":      rma["asset_id"],
            "rma_id":        rma["rma_id"],
            "owner_id":      rng.choice(own_ids),
            "event_type":    "refund",
            "amount_usd":    -deposit,
            "currency":      CURRENCY,
            "event_date":    refund_date,
            "balance_after": 0.0,
            "notes":         "Deposit refund on RMA closure",
            "created_at":    refund_date,
        })
        ledger_ctr += 1

    return rows

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — EDGE CASE INJECTION
# ─────────────────────────────────────────────────────────────────────────────

def inject_edge_cases(rng, assets, custody_events, return_authorizations, deposit_ledger, repairs, inspections, owners, locations, shipments):
    """Inject labelled anomalies. Returns ground_truth list."""
    ground_truth = []
    own_ids = [o["owner_id"]   for o in owners]
    loc_ids = [l["location_id"] for l in locations]
    shp_ids = [s["shipment_id"] for s in shipments]

    ec_assets  = rng.sample(assets, min(25, len(assets)))
    asset_pool = iter(ec_assets)

    def next_asset():
        try:
            return next(asset_pool)
        except StopIteration:
            return rng.choice(assets)

    # ── EC1: Asset has two simultaneous locations (10 cases) ──────────────
    for k in range(10):
        asset = next_asset()
        t = rnd_datetime(rng, BASE_DATE, BASE_DATE + timedelta(days=60))
        for suffix, loc in enumerate(rng.sample(loc_ids, 2)):
            ctr = 900000 + k * 10 + suffix
            custody_events.append({
                "event_id":        f"CUST-{asset['asset_id']}-EC{ctr:06d}",
                "asset_id":        asset["asset_id"],
                "event_type":      "received",
                "event_timestamp": fmt_datetime(t),          # same timestamp → two locations
                "from_location_id": rng.choice(loc_ids),
                "to_location_id":  loc,
                "actor_id":        rng.choice(own_ids),
                "shipment_id":     rng.choice(shp_ids),
                "notes":           "EDGE_CASE: simultaneous_location",
                "is_disputed":     "true",
                "created_at":      fmt_datetime(t),
            })
        ground_truth.append({
            "issue_id":    f"GT-EC1-{k+1:04d}",
            "issue_type":  "simultaneous_location",
            "entity":      "CustodyEvent",
            "asset_id":    asset["asset_id"],
            "description": "Asset recorded at two locations simultaneously",
            "severity":    "high",
        })

    # ── EC2: Return processed before dispatch (5 cases) ──────────────────
    for k in range(5):
        asset = next_asset()
        dispatch_time = rnd_datetime(rng, BASE_DATE + timedelta(days=10), BASE_DATE + timedelta(days=50))
        return_time   = dispatch_time - timedelta(hours=rng.randint(1, 48))  # before dispatch
        ctr_base = 950000 + k * 10
        custody_events.append({
            "event_id":        f"CUST-{asset['asset_id']}-EC{ctr_base:06d}",
            "asset_id":        asset["asset_id"],
            "event_type":      "dispatch",
            "event_timestamp": fmt_datetime(dispatch_time),
            "from_location_id": rng.choice(loc_ids),
            "to_location_id":  rng.choice(loc_ids),
            "actor_id":        rng.choice(own_ids),
            "shipment_id":     rng.choice(shp_ids),
            "notes":           "",
            "is_disputed":     "false",
            "created_at":      fmt_datetime(dispatch_time),
        })
        custody_events.append({
            "event_id":        f"CUST-{asset['asset_id']}-EC{ctr_base+1:06d}",
            "asset_id":        asset["asset_id"],
            "event_type":      "return",
            "event_timestamp": fmt_datetime(return_time),
            "from_location_id": rng.choice(loc_ids),
            "to_location_id":  rng.choice(loc_ids),
            "actor_id":        rng.choice(own_ids),
            "shipment_id":     rng.choice(shp_ids),
            "notes":           "EDGE_CASE: return_before_dispatch",
            "is_disputed":     "true",
            "created_at":      fmt_datetime(return_time),
        })
        ground_truth.append({
            "issue_id":    f"GT-EC2-{k+1:04d}",
            "issue_type":  "return_before_dispatch",
            "entity":      "CustodyEvent",
            "asset_id":    asset["asset_id"],
            "description": "Return event timestamp precedes dispatch event timestamp",
            "severity":    "high",
        })

    # ── EC3: Deposit refunded twice (5 cases) ─────────────────────────────
    closed = [r for r in return_authorizations if r["status"] in ["closed","received"]]
    sample_rmas = rng.sample(closed, min(5, len(closed)))
    for k, rma in enumerate(sample_rmas):
        dep = float(next((a["deposit_held_usd"] for a in assets if a["asset_id"] == rma["asset_id"]), 50.0))
        ref_date = rma["received_date"] or rma["due_date"]
        ledger_id = f"DEP-EC3-{k+1:04d}"
        deposit_ledger.append({
            "ledger_id":     ledger_id,
            "asset_id":      rma["asset_id"],
            "rma_id":        rma["rma_id"],
            "owner_id":      rng.choice(own_ids),
            "event_type":    "refund",
            "amount_usd":    -dep,
            "currency":      CURRENCY,
            "event_date":    ref_date,
            "balance_after": -dep,
            "notes":         "EDGE_CASE: duplicate_refund",
            "created_at":    ref_date,
        })
        ground_truth.append({
            "issue_id":    f"GT-EC3-{k+1:04d}",
            "issue_type":  "duplicate_refund",
            "entity":      "DepositLedger",
            "asset_id":    rma["asset_id"],
            "description": f"Deposit refunded twice for RMA {rma['rma_id']}",
            "severity":    "medium",
        })

    # ── EC4: Repair closes without inspection (5 cases) ───────────────────
    for k in range(5):
        asset = next_asset()
        start = rnd_date(rng, BASE_DATE, BASE_DATE + timedelta(days=60))
        end   = start + timedelta(days=rng.randint(1, 10))
        rep_id = f"REP-EC4-{k+1:06d}"
        repairs.append({
            "repair_id":           rep_id,
            "asset_id":            asset["asset_id"],
            "inspection_id":       "",           # no inspection
            "repair_facility_id":  rng.choice(loc_ids),
            "technician_id":       rng.choice(own_ids),
            "start_date":          fmt_date(start),
            "end_date":            fmt_date(end),
            "status":              "completed",
            "repair_type":         rng.choice(["structural","cleaning","component_replacement"]),
            "cost_usd":            round(rng.uniform(10, 500), 2),
            "parts_replaced":      "none",
            "created_at":          fmt_date(start),
        })
        ground_truth.append({
            "issue_id":    f"GT-EC4-{k+1:04d}",
            "issue_type":  "repair_without_inspection",
            "entity":      "Repair",
            "asset_id":    asset["asset_id"],
            "description": f"Repair {rep_id} closed/completed without a linked inspection",
            "severity":    "medium",
        })

    # ── EC5: Custody event lacks actor (20 cases, flagged) ────────────────
    no_actor = [e for e in custody_events if e["actor_id"] == ""]
    sample_no_actor = rng.sample(no_actor, min(20, len(no_actor)))
    for k, evt in enumerate(sample_no_actor):
        ground_truth.append({
            "issue_id":    f"GT-EC5-{k+1:04d}",
            "issue_type":  "missing_actor",
            "entity":      "CustodyEvent",
            "asset_id":    evt["asset_id"],
            "description": f"Custody event {evt['event_id']} has no recorded actor/handler",
            "severity":    "low",
        })

    return ground_truth

# ─────────────────────────────────────────────────────────────────────────────
# STEP 10 — VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def validate(asset_types, owners, locations, assets, shipments,
             custody_events, return_authorizations, inspections,
             repairs, deposit_ledger):
    errors = []
    warnings = []

    # PK uniqueness
    for name, rows, pk in [
        ("AssetType", asset_types, "asset_type_id"),
        ("Owner",     owners,      "owner_id"),
        ("Location",  locations,   "location_id"),
        ("Asset",     assets,      "asset_id"),
        ("Shipment",  shipments,   "shipment_id"),
        ("CustodyEvent", custody_events, "event_id"),
        ("ReturnAuthorization", return_authorizations, "rma_id"),
        ("Inspection",  inspections,  "inspection_id"),
        ("Repair",      repairs,      "repair_id"),
        ("DepositLedger", deposit_ledger, "ledger_id"),
    ]:
        ids = [r[pk] for r in rows]
        dups = len(ids) - len(set(ids))
        if dups:
            errors.append(f"[PK] {name}.{pk}: {dups} duplicate(s)")

    # FK integrity
    asset_id_set   = {a["asset_id"]      for a in assets}
    loc_id_set     = {l["location_id"]   for l in locations}
    own_id_set     = {o["owner_id"]      for o in owners}
    at_id_set      = {t["asset_type_id"] for t in asset_types}
    shp_id_set     = {s["shipment_id"]   for s in shipments}
    insp_id_set    = {i["inspection_id"] for i in inspections}

    for asset in assets:
        if asset["asset_type_id"] not in at_id_set:
            errors.append(f"[FK] Asset {asset['asset_id']} -> invalid asset_type_id")
        if asset["owner_id"] not in own_id_set:
            errors.append(f"[FK] Asset {asset['asset_id']} -> invalid owner_id")
        if asset["current_location_id"] not in loc_id_set:
            errors.append(f"[FK] Asset {asset['asset_id']} -> invalid current_location_id")

    for ce in custody_events:
        if ce["asset_id"] not in asset_id_set:
            errors.append(f"[FK] CustodyEvent {ce['event_id']} -> invalid asset_id")
        if ce["from_location_id"] not in loc_id_set:
            errors.append(f"[FK] CustodyEvent {ce['event_id']} -> invalid from_location_id")
        if ce["to_location_id"] not in loc_id_set:
            errors.append(f"[FK] CustodyEvent {ce['event_id']} -> invalid to_location_id")

    for rma in return_authorizations:
        if rma["asset_id"] not in asset_id_set:
            errors.append(f"[FK] RMA {rma['rma_id']} -> invalid asset_id")

    for insp in inspections:
        if insp["asset_id"] not in asset_id_set:
            errors.append(f"[FK] Inspection {insp['inspection_id']} -> invalid asset_id")

    for rep in repairs:
        if rep["asset_id"] not in asset_id_set:
            errors.append(f"[FK] Repair {rep['repair_id']} -> invalid asset_id")
        if rep["inspection_id"] and rep["inspection_id"] not in insp_id_set:
            errors.append(f"[FK] Repair {rep['repair_id']} -> invalid inspection_id")

    for dl in deposit_ledger:
        if dl["asset_id"] not in asset_id_set:
            errors.append(f"[FK] DepositLedger {dl['ledger_id']} -> invalid asset_id")

    # Deposit ledger reconciliation (sample check)
    asset_balance = defaultdict(float)
    for dl in deposit_ledger:
        asset_balance[dl["asset_id"]] += float(dl["amount_usd"])

    negative_balances = sum(1 for v in asset_balance.values() if v < -0.01)
    if negative_balances:
        warnings.append(f"[LEDGER] {negative_balances} asset(s) have negative deposit balance (expected for edge cases)")

    # Date ordering: RMA issued_date <= due_date
    for rma in return_authorizations:
        if rma["received_date"] and rma["received_date"] < rma["issued_date"]:
            errors.append(f"[DATE] RMA {rma['rma_id']}: received_date < issued_date")

    # Enum validation
    valid_states = set(LIFECYCLE_STATES)
    for asset in assets:
        if asset["lifecycle_state"] not in valid_states:
            errors.append(f"[ENUM] Asset {asset['asset_id']}: invalid lifecycle_state '{asset['lifecycle_state']}'")

    return errors, warnings

# ─────────────────────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate(seed=FIXED_SEED, scale="full", out_dir=OUTPUT_DIR):
    rng = random.Random(seed)
    cfg = SCALE_CONFIG[scale]
    n_assets   = cfg["assets"]
    n_shipments = cfg["shipments"]
    n_events   = cfg["custody_events"]

    print(f"\n{'='*60}")
    print(f"  Reverse Logistics Data Generator")
    print(f"  Seed: {seed}  |  Scale: {scale}")
    print(f"  Assets: {n_assets:,}  Shipments: {n_shipments:,}  Custody Events: {n_events:,}")
    print(f"{'='*60}")

    out = os.path.join(out_dir, scale)
    os.makedirs(out, exist_ok=True)

    # ── Master tables ──────────────────────────────────────────────────────
    print("\n[1/10] Generating master tables...")
    asset_types = gen_asset_types(rng)
    owners      = gen_owners(rng, 120)
    locations   = gen_locations(rng, 80)

    # ── Dependent tables ───────────────────────────────────────────────────
    print("[2/10] Generating assets...")
    assets = gen_assets(rng, asset_types, owners, locations, n_assets)

    print("[3/10] Generating shipments...")
    shipments = gen_shipments(rng, owners, locations, n_shipments)

    print("[4/10] Generating custody events...")
    custody_events = gen_custody_events(rng, assets, shipments, owners, locations, n_events)

    print("[5/10] Generating return authorizations...")
    return_authorizations = gen_return_authorizations(rng, assets, owners, locations, shipments)

    print("[6/10] Generating inspections...")
    inspections = gen_inspections(rng, assets, owners, locations)

    print("[7/10] Generating repairs...")
    repairs = gen_repairs(rng, inspections, owners, locations)

    print("[8/10] Generating deposit ledger...")
    deposit_ledger = gen_deposit_ledger(rng, assets, return_authorizations, owners)

    print("[9/10] Injecting edge cases...")
    ground_truth = inject_edge_cases(
        rng, assets, custody_events, return_authorizations,
        deposit_ledger, repairs, inspections, owners, locations, shipments
    )

    # ── Validation ─────────────────────────────────────────────────────────
    print("[10/10] Validating...")
    errors, warnings = validate(
        asset_types, owners, locations, assets, shipments,
        custody_events, return_authorizations, inspections,
        repairs, deposit_ledger
    )

    # ── Export CSV ─────────────────────────────────────────────────────────
    print("\nExporting CSV files...")
    datasets = {
        "asset_types.csv":           (asset_types,          list(asset_types[0].keys()) if asset_types else []),
        "owners.csv":                (owners,               list(owners[0].keys()) if owners else []),
        "locations.csv":             (locations,            list(locations[0].keys()) if locations else []),
        "assets.csv":                (assets,               list(assets[0].keys()) if assets else []),
        "shipments.csv":             (shipments,            list(shipments[0].keys()) if shipments else []),
        "custody_events.csv":        (custody_events,       list(custody_events[0].keys()) if custody_events else []),
        "return_authorizations.csv": (return_authorizations, list(return_authorizations[0].keys()) if return_authorizations else []),
        "inspections.csv":           (inspections,          list(inspections[0].keys()) if inspections else []),
        "repairs.csv":               (repairs,              list(repairs[0].keys()) if repairs else []),
        "deposit_ledger.csv":        (deposit_ledger,       list(deposit_ledger[0].keys()) if deposit_ledger else []),
        "ground_truth.csv":          (ground_truth,         list(ground_truth[0].keys()) if ground_truth else []),
    }

    checksums = {}
    for fname, (rows, fields) in datasets.items():
        path = os.path.join(out, fname)
        write_csv(path, rows, fields)
        checksums[fname] = file_checksum(path)

    # ── Validation Summary ─────────────────────────────────────────────────
    val_summary = {
        "seed": seed,
        "scale": scale,
        "row_counts": {fname: len(rows) for fname, (rows, _) in datasets.items()},
        "checksums": checksums,
        "errors": errors,
        "warnings": warnings,
        "edge_cases_injected": len(ground_truth),
    }
    val_path = os.path.join(out, "validation_summary.json")
    with open(val_path, "w") as f:
        json.dump(val_summary, f, indent=2)
    print(f"\n  Validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    if errors:
        for e in errors[:10]:
            print(f"    ERROR: {e}")
    if warnings:
        for w in warnings[:5]:
            print(f"    WARN:  {w}")

    # ── Source Manifest ─────────────────────────────────────────────────────
    manifest = {
        "project": "Reverse Logistics Synthetic Data",
        "generated_at": fmt_datetime(datetime.now()),
        "seed": seed,
        "scale": scale,
        "generator_command": f"python generate_data.py --seed {seed} --scale {scale}",
        "data_provenance": "Fully synthetic; no real personal or confidential data used.",
        "license": "Synthetic data, freely usable for demonstration and academic purposes.",
        "entities": list(datasets.keys()),
        "row_counts": val_summary["row_counts"],
        "checksums_md5": checksums,
    }
    manifest_path = os.path.join(out, "source_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[OK] All files written to: {out}/")
    print(f"  Validation summary : validation_summary.json")
    print(f"  Source manifest    : source_manifest.json")
    print(f"  Ground truth       : ground_truth.csv ({len(ground_truth)} anomalies)\n")

    return val_summary

# ─────────────────────────────────────────────────────────────────────────────
# REPRODUCIBILITY CHECK
# ─────────────────────────────────────────────────────────────────────────────

def reproducibility_check(seed=FIXED_SEED, scale="starter"):
    """Regenerate twice and compare checksums."""
    print("\n" + "="*60)
    print("  REPRODUCIBILITY CHECK (2 runs, same seed)")
    print("="*60)
    r1 = generate(seed=seed, scale=scale, out_dir="output/repro_run1")
    r2 = generate(seed=seed, scale=scale, out_dir="output/repro_run2")

    all_match = True
    print("\nChecksum comparison:")
    for fname in r1["checksums"]:
        c1 = r1["checksums"].get(fname, "?")
        c2 = r2["checksums"].get(fname, "?")
        match = "[OK]" if c1 == c2 else "[!!] MISMATCH"
        print(f"  {match}  {fname}")
        if c1 != c2:
            all_match = False
    if all_match:
        print("\n[OK] Both runs produce identical output -- reproducibility confirmed.")
    else:
        print("\n[!!] Checksums differ -- investigate RNG state leakage.")

# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reverse Logistics Synthetic Data Generator")
    parser.add_argument("--seed",  type=int, default=FIXED_SEED,  help="Random seed (default: 20261022)")
    parser.add_argument("--scale", choices=["full","starter"],    default="full", help="Dataset scale")
    parser.add_argument("--repro-check", action="store_true",     help="Run reproducibility check (uses starter scale)")
    parser.add_argument("--out",   default=OUTPUT_DIR,            help="Output directory")
    args = parser.parse_args()

    if args.repro_check:
        reproducibility_check(seed=args.seed, scale="starter")
    else:
        generate(seed=args.seed, scale=args.scale, out_dir=args.out)
