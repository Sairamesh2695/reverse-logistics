# Data Dictionary — Reverse Logistics Synthetic Dataset

## 1. AssetType

**Primary Key:** `asset_type_id`
**Cardinality:** 1 AssetType → N ReusableAssets

| Field | Type | Req | Allowed Values / Units | Unique | Validation Rule |
|---|---|---|---|---|---|
| asset_type_id | STRING | Yes | AT-NNNN | Yes (PK) | Format: AT-[0-9]{4} |
| category | STRING | Yes | Pallet, Crate, Container, Tote, Drum, Roll Cage, IBC, Reel | No | Must be from allowed list |
| variant_name | STRING | Yes | Free text, max 50 chars | Yes | Non-null |
| description | STRING | No | Free text | No | — |
| max_capacity_kg | FLOAT | Yes | 50–2000 kg | No | > 0 |
| tare_weight_kg | FLOAT | Yes | 2–150 kg | No | > 0 and < max_capacity_kg |
| material | STRING | Yes | plastic, wood, steel, aluminium, composite | No | Enum |
| max_lifetime_days | INT | Yes | 60–1200 days | No | > 0 |
| inspection_interval_days | INT | Yes | 30–180 days | No | > 0 and ≤ max_lifetime_days |
| deposit_amount_usd | FLOAT | Yes | 5.00–500.00 USD | No | > 0 |
| is_returnable | BOOL | Yes | true, false | No | Always true for reusable assets |
| lifecycle_rule | STRING | Yes | reuse_until_damaged, fixed_cycles, age_based | No | Enum |
| max_reuse_cycles | INT | Yes | 10–500 | No | > 0 |
| created_at | DATE | Yes | YYYY-MM-DD | No | ≤ today |

---

## 2. Owner

**Primary Key:** `owner_id`
**Cardinality:** 1 Owner → N Assets, N Shipments, N CustodyEvents

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| owner_id | STRING | Yes | OWN-NNNNN | Yes (PK) | Format |
| owner_name | STRING | Yes | Free text | No | Non-null |
| owner_type | STRING | Yes | supplier, carrier, warehouse, customer, third_party_logistics | No | Enum |
| contact_email | STRING | No | Valid email | No | RFC 5322 format |
| contact_phone | STRING | No | +1-555-XXXX-XXXX | No | — |
| country | STRING | Yes | ISO 3166-1 alpha-2 | No | 2-char code |
| is_active | BOOL | Yes | true, false | No | — |
| created_at | DATE | Yes | YYYY-MM-DD | No | ≤ today |

---

## 3. Location

**Primary Key:** `location_id`
**Cardinality:** 1 Location → N Assets, N CustodyEvents (from/to), N Inspections

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| location_id | STRING | Yes | LOC-NNNNN | Yes (PK) | Format |
| location_name | STRING | Yes | Free text | No | Non-null |
| location_type | STRING | Yes | warehouse, distribution_center, supplier_site, customer_site, port, repair_center | No | Enum |
| address_line1 | STRING | No | Free text | No | — |
| city | STRING | Yes | Free text | No | Non-null |
| country | STRING | Yes | ISO 3166-1 alpha-2 | No | 2-char code |
| latitude | FLOAT | No | -90 to 90 | No | Valid WGS84 |
| longitude | FLOAT | No | -180 to 180 | No | Valid WGS84 |
| capacity_units | INT | No | 100–50000 | No | > 0 |
| is_active | BOOL | Yes | true, false | No | — |
| created_at | DATE | Yes | YYYY-MM-DD | No | ≤ today |

---

## 4. ReusableAsset

**Primary Key:** `asset_id`
**Foreign Keys:** asset_type_id → AssetType, owner_id → Owner, current_location_id → Location
**Cardinality:** N Assets → 1 AssetType; N CustodyEvents → 1 Asset; N RMAs → 1 Asset

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| asset_id | STRING | Yes | ASSET-NNNNNNN | Yes (PK) | Zero-padded 7 digits |
| asset_type_id | STRING | Yes | AT-NNNN | No (FK) | Must exist in AssetType |
| serial_number | STRING | Yes | SN-NNNNNNN | Yes | Non-null |
| owner_id | STRING | Yes | OWN-NNNNN | No (FK) | Must exist in Owner |
| current_location_id | STRING | Yes | LOC-NNNNN | No (FK) | Must exist in Location |
| manufacture_date | DATE | Yes | YYYY-MM-DD | No | ≤ today |
| last_inspection_date | DATE | No | YYYY-MM-DD | No | ≥ manufacture_date |
| lifecycle_state | STRING | Yes | active, in_transit, at_location, under_repair, lost, retired, decommissioned | No | Enum |
| damage_level | STRING | Yes | none, minor, moderate, severe | No | Enum |
| reuse_cycle_count | INT | Yes | 0 – max_reuse_cycles | No | ≥ 0 |
| is_lost | BOOL | Yes | true, false | No | true iff lifecycle_state = lost |
| deposit_held_usd | FLOAT | Yes | ≥ 0 USD | No | Matches asset_type deposit_amount |
| created_at | DATE | Yes | YYYY-MM-DD | No | = manufacture_date |
| updated_at | DATE | Yes | YYYY-MM-DD | No | ≥ created_at |

---

## 5. Shipment

**Primary Key:** `shipment_id`
**Foreign Keys:** origin_location_id, dest_location_id → Location; carrier_id, shipper_id → Owner
**Cardinality:** 1 Shipment → N CustodyEvents

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| shipment_id | STRING | Yes | SHP-2026-NNNNNN | Yes (PK) | Format |
| origin_location_id | STRING | Yes | LOC-NNNNN | No (FK) | ≠ dest_location_id |
| dest_location_id | STRING | Yes | LOC-NNNNN | No (FK) | ≠ origin_location_id |
| carrier_id | STRING | Yes | OWN-NNNNN | No (FK) | Must exist in Owner |
| shipper_id | STRING | Yes | OWN-NNNNN | No (FK) | Must exist in Owner |
| planned_departure | DATE | Yes | YYYY-MM-DD | No | ≤ planned_arrival |
| actual_departure | DATE | No | YYYY-MM-DD | No | ≥ planned_departure - 1 day |
| planned_arrival | DATE | Yes | YYYY-MM-DD | No | ≥ planned_departure |
| actual_arrival | DATE | No | YYYY-MM-DD | No | ≥ actual_departure |
| status | STRING | Yes | scheduled, in_transit, delivered, cancelled, delayed | No | Enum |
| mode | STRING | Yes | road, rail, air, sea, multimodal | No | Enum |
| total_assets | INT | No | 1–200 | No | > 0 |
| is_return_shipment | BOOL | Yes | true, false | No | — |
| created_at | DATE | Yes | YYYY-MM-DD | No | ≤ planned_departure |

---

## 6. CustodyEvent

**Primary Key:** `event_id`
**Foreign Keys:** asset_id → ReusableAsset; from_location_id, to_location_id → Location; actor_id → Owner (optional); shipment_id → Shipment (optional)
**Cardinality:** N CustodyEvents → 1 Asset (event log, append-only)

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| event_id | STRING | Yes | CUST-<asset_id>-NNNNNN | Yes (PK) | Format, counter per asset |
| asset_id | STRING | Yes | ASSET-NNNNNNN | No (FK) | Must exist in ReusableAsset |
| event_type | STRING | Yes | dispatch, in_transit, received, transfer, return, inspection_checkpoint | No | Enum |
| event_timestamp | DATETIME | Yes | ISO 8601 | No | Monotonically increasing per asset (baseline; edge cases violate this) |
| from_location_id | STRING | Yes | LOC-NNNNN | No (FK) | Must exist in Location |
| to_location_id | STRING | Yes | LOC-NNNNN | No (FK) | Must exist in Location |
| actor_id | STRING | **No** | OWN-NNNNN | No (FK) | Null allowed; edge case = missing actor |
| shipment_id | STRING | No | SHP-2026-NNNNNN | No (FK) | Must exist in Shipment if not empty |
| notes | STRING | No | Free text | No | Contains EDGE_CASE tag if anomaly |
| is_disputed | BOOL | Yes | true, false | No | — |
| created_at | DATETIME | Yes | ISO 8601 | No | = event_timestamp |

---

## 7. ReturnAuthorization (RMA)

**Primary Key:** `rma_id`
**Foreign Keys:** asset_id → ReusableAsset; issued_by_owner_id → Owner; return_to_location_id → Location; shipment_id → Shipment (optional)
**Cardinality:** 1 Asset → N RMAs (over lifecycle)

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| rma_id | STRING | Yes | RMA-2026-NNNNNN | Yes (PK) | Format |
| asset_id | STRING | Yes | ASSET-NNNNNNN | No (FK) | Must exist |
| issued_by_owner_id | STRING | Yes | OWN-NNNNN | No (FK) | Must exist |
| return_to_location_id | STRING | Yes | LOC-NNNNN | No (FK) | Must exist |
| shipment_id | STRING | No | SHP-2026-NNNNNN | No (FK) | Optional |
| issued_date | DATE | Yes | YYYY-MM-DD | No | ≤ due_date |
| due_date | DATE | Yes | YYYY-MM-DD | No | ≥ issued_date |
| received_date | DATE | No | YYYY-MM-DD | No | ≥ issued_date if set |
| status | STRING | Yes | pending, approved, in_transit, received, closed, disputed | No | Enum |
| reason | STRING | Yes | end_of_lease, damaged, wrong_delivery, overstock, recall | No | Enum |
| days_outstanding | INT | Yes | Derived: (received_date or today) - issued_date | No | ≥ 0 |
| is_overdue | BOOL | Yes | Derived: days_outstanding > (due_date - issued_date) and status not closed | No | Deterministic |
| created_at | DATE | Yes | YYYY-MM-DD | No | = issued_date |

---

## 8. Inspection

**Primary Key:** `inspection_id`
**Foreign Keys:** asset_id → ReusableAsset; inspector_id → Owner; location_id → Location
**Cardinality:** 1 Asset → N Inspections (history preserved)

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| inspection_id | STRING | Yes | INSP-<asset_id>-NNNN | Yes (PK) | Format |
| asset_id | STRING | Yes | ASSET-NNNNNNN | No (FK) | Must exist |
| inspector_id | STRING | Yes | OWN-NNNNN | No (FK) | Must exist |
| location_id | STRING | Yes | LOC-NNNNN | No (FK) | Must exist |
| inspection_date | DATE | Yes | YYYY-MM-DD | No | ≥ asset.manufacture_date |
| result | STRING | Yes | pass, fail, conditional_pass | No | Enum |
| damage_level | STRING | Yes | none, minor, moderate, severe | No | Enum |
| notes | STRING | No | Free text | No | — |
| next_inspection_due | DATE | Yes | YYYY-MM-DD | No | > inspection_date |
| created_at | DATE | Yes | YYYY-MM-DD | No | = inspection_date |

---

## 9. Repair

**Primary Key:** `repair_id`
**Foreign Keys:** asset_id → ReusableAsset; inspection_id → Inspection (optional — edge case if missing); repair_facility_id → Location; technician_id → Owner
**Cardinality:** 1 Inspection → 0–1 Repair (normally); edge case = Repair with no Inspection

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| repair_id | STRING | Yes | REP-2026-NNNNNN | Yes (PK) | Format |
| asset_id | STRING | Yes | ASSET-NNNNNNN | No (FK) | Must exist |
| inspection_id | STRING | **No** | INSP-<asset_id>-NNNN | No (FK) | Null = edge case EC4 |
| repair_facility_id | STRING | Yes | LOC-NNNNN | No (FK) | Must exist |
| technician_id | STRING | Yes | OWN-NNNNN | No (FK) | Must exist |
| start_date | DATE | Yes | YYYY-MM-DD | No | ≥ inspection_date if linked |
| end_date | DATE | No | YYYY-MM-DD | No | ≥ start_date if set |
| status | STRING | Yes | open, in_progress, completed, cancelled | No | Enum |
| repair_type | STRING | Yes | structural, cleaning, component_replacement, cosmetic, electrical | No | Enum |
| cost_usd | FLOAT | Yes | 10–2000 USD | No | > 0 |
| parts_replaced | STRING | No | none, bracket, corner_piece, locking_pin, base_plate, wall_panel | No | — |
| created_at | DATE | Yes | YYYY-MM-DD | No | = start_date |

---

## 10. DepositLedger

**Primary Key:** `ledger_id`
**Foreign Keys:** asset_id → ReusableAsset; rma_id → ReturnAuthorization (optional); owner_id → Owner
**Cardinality:** 1 Asset → N DepositLedger entries (append-only event log)

| Field | Type | Req | Allowed Values | Unique | Validation Rule |
|---|---|---|---|---|---|
| ledger_id | STRING | Yes | DEP-NNNNNNNN | Yes (PK) | Format |
| asset_id | STRING | Yes | ASSET-NNNNNNN | No (FK) | Must exist |
| rma_id | STRING | No | RMA-2026-NNNNNN | No (FK) | Optional |
| owner_id | STRING | Yes | OWN-NNNNN | No (FK) | Must exist |
| event_type | STRING | Yes | charge, refund, adjustment, penalty | No | Enum |
| amount_usd | FLOAT | Yes | Positive for charge, negative for refund | No | ≠ 0 |
| currency | STRING | Yes | USD | No | ISO 4217 |
| event_date | DATE | Yes | YYYY-MM-DD | No | Valid date |
| balance_after | FLOAT | Yes | Running balance per asset | No | Derived: sum of prior amounts + this amount |
| notes | STRING | No | Free text | No | Contains EDGE_CASE tag if anomaly |
| created_at | DATE | Yes | YYYY-MM-DD | No | = event_date |

---

## 11. GroundTruth (Anomaly Labels)

**Primary Key:** `issue_id`
**Note:** This file is **never** merged into input features. It is used for evaluation only.

| Field | Type | Req | Allowed Values | Unique | Validation |
|---|---|---|---|---|---|
| issue_id | STRING | Yes | GT-EC[1-5]-NNNN | Yes (PK) | Format |
| issue_type | STRING | Yes | simultaneous_location, return_before_dispatch, duplicate_refund, repair_without_inspection, missing_actor | No | Enum |
| entity | STRING | Yes | CustodyEvent, DepositLedger, Repair | No | — |
| asset_id | STRING | Yes | ASSET-NNNNNNN | No (FK) | Must exist in ReusableAsset |
| description | STRING | Yes | Human-readable description | No | Non-null |
| severity | STRING | Yes | high, medium, low | No | Enum |

---

## Cardinality Summary

```
AssetType  ──< ReusableAsset >── Owner
                    │
            ┌───────┴────────┐
            │                │
        Location         CustodyEvent ──> Shipment
            │                       ──> Owner (actor)
            │                       ──> Location (from/to)
         Inspection
            │
          Repair
            
ReusableAsset ──< ReturnAuthorization
ReusableAsset ──< DepositLedger
ReusableAsset ──< Inspection
ReusableAsset ──< Repair
```

Legend: `──<` = one-to-many; `>──` = many-to-one
