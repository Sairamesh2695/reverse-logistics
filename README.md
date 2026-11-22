# 🔄 Reverse Logistics — Synthetic Dataset Generator

> End-to-end synthetic data pipeline for **Return Merchandise Authorization (RMA)** and **Reusable Asset Tracking** across locations and custody transitions.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Synthetic%20%2F%20Open-green)](./README.md)
[![Seed](https://img.shields.io/badge/Fixed%20Seed-20261022-orange)](./generate_data.py)
[![Reproducible](https://img.shields.io/badge/Reproducible-Yes%20%E2%80%94%20MD5%20Verified-brightgreen)](./generate_data.py)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Generated Entities](#-generated-entities)
- [ID Naming Conventions](#-id-naming-conventions)
- [Edge Cases & Anomalies](#-edge-cases--anomalies)
- [Validation Rules](#-validation-rules)
- [Reproducibility](#-reproducibility)
- [Schema & SQL](#-schema--sql)
- [Data Provenance](#-data-provenance)
- [Evaluation Checklist](#-evaluation-checklist)

---

## 🔍 Overview

This project generates a **fully synthetic, deterministic dataset** for a reverse logistics system. It models the complete lifecycle of reusable assets (pallets, crates, containers, totes, etc.) — from initial dispatch and custody handoffs through inspections, repairs, return authorizations, and deposit reconciliation.

### Key Numbers (Full Scale)

| Entity | Count |
|---|---|
| Reusable Assets | **20,000** |
| Shipments | **10,000** |
| Custody Events | **100,000+** |
| Return Authorizations | ~7,000 |
| Inspections | ~34,000 |
| Repairs | ~10,000 |
| Deposit Ledger Entries | ~22,000 |
| Labelled Anomalies (Ground Truth) | **45** |

### Why Synthetic?

- 100% deterministic — same seed → same output, every time
- No personal, confidential, or proprietary data
- Labelled edge cases for anomaly detection evaluation
- Fully self-contained — no external API or database needed

---

## 📁 Project Structure

```
reverse-logistics/
│
├── generate_data.py          # Main data generator (pure Python stdlib)
├── schema.sql                # SQL DDL — tables, indexes, constraints, views
├── DATA_DICTIONARY.md        # Per-field specs for all 10 entities
├── README.md                 # This file
│
└── output/
    ├── full/                 # Full-scale dataset (20K assets)
    │   ├── asset_types.csv
    │   ├── owners.csv
    │   ├── locations.csv
    │   ├── assets.csv
    │   ├── shipments.csv
    │   ├── custody_events.csv
    │   ├── return_authorizations.csv
    │   ├── inspections.csv
    │   ├── repairs.csv
    │   ├── deposit_ledger.csv
    │   ├── ground_truth.csv          ← Anomaly labels (evaluation only)
    │   ├── validation_summary.json   ← PK/FK checks, checksums
    │   └── source_manifest.json      ← Provenance & metadata
    │
    ├── starter/              # Starter dataset (200 assets — fast preview)
    │
    ├── repro_run1/           # Reproducibility proof — Run 1
    └── repro_run2/           # Reproducibility proof — Run 2 (identical checksums)
```

---

## ✅ Prerequisites

- **Python 3.8 or higher**
- **No external dependencies** — uses only the Python standard library (`csv`, `json`, `hashlib`, `random`, `argparse`, `datetime`, `collections`, `os`)

Check your Python version:

```bash
python --version
# or
python3 --version
```

---

## 🚀 Quick Start

### 1. Clone or download the repository

```bash
git clone https://github.com/your-username/reverse-logistics.git
cd reverse-logistics
```

### 2. Generate the full dataset

```bash
python generate_data.py --seed 20261022 --scale full
```

Output will appear in `output/full/`. Expect ~30–60 seconds for the full scale.

### 3. Preview with the starter dataset (fast — under 2 seconds)

```bash
python generate_data.py --seed 20261022 --scale starter
```

Output will appear in `output/starter/`.

---

## 🛠 Usage

```
python generate_data.py [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--seed` | `int` | `20261022` | Random seed — controls all data generation |
| `--scale` | `full` \| `starter` | `full` | Dataset size (full = 20K assets; starter = 200 assets) |
| `--repro-check` | flag | — | Generate twice and compare MD5 checksums |
| `--out` | `path` | `output` | Output directory |

### Examples

```bash
# Full dataset with default seed
python generate_data.py --seed 20261022 --scale full

# Starter dataset (great for quick inspection / CI)
python generate_data.py --seed 20261022 --scale starter

# Custom output directory
python generate_data.py --seed 20261022 --scale full --out ./my_data

# Reproducibility check — generates twice, compares every file's MD5
python generate_data.py --seed 20261022 --repro-check

# Use a different seed (creates a different valid dataset)
python generate_data.py --seed 99999 --scale full
```

### Expected Output

```
============================================================
  Reverse Logistics Data Generator
  Seed: 20261022  |  Scale: full
  Assets: 20,000  Shipments: 10,000  Custody Events: 100,000
============================================================

[1/10] Generating master tables...
[2/10] Generating assets...
[3/10] Generating shipments...
[4/10] Generating custody events...
[5/10] Generating return authorizations...
[6/10] Generating inspections...
[7/10] Generating repairs...
[8/10] Generating deposit ledger...
[9/10] Injecting edge cases...
[10/10] Validating...

Exporting CSV files...
  Wrote      23 rows -> output\full\asset_types.csv
  Wrote     120 rows -> output\full\owners.csv
  Wrote      80 rows -> output\full\locations.csv
  Wrote  20,000 rows -> output\full\assets.csv
  Wrote  10,000 rows -> output\full\shipments.csv
  Wrote 100,030 rows -> output\full\custody_events.csv
  Wrote   7,000 rows -> output\full\return_authorizations.csv
  Wrote  34,343 rows -> output\full\inspections.csv
  Wrote  10,309 rows -> output\full\repairs.csv
  Wrote  22,331 rows -> output\full\deposit_ledger.csv
  Wrote      45 rows -> output\full\ground_truth.csv

  Validation: 0 error(s), 1 warning(s)
    WARN:  [LEDGER] 5 asset(s) have negative deposit balance (expected for edge cases)

[OK] All files written to: output/full/
  Validation summary : validation_summary.json
  Source manifest    : source_manifest.json
  Ground truth       : ground_truth.csv (45 anomalies)
```

> **Note:** The 1 warning about negative deposit balances is **expected** — it reflects the 5 intentionally injected duplicate-refund anomalies (EC3).

---

## 📦 Generated Entities

The generator produces **10 CSV files** in dependency order (parents before children):

```
AssetType  ──< ReusableAsset >── Owner
                    │
        ┌───────────┼──────────────────┐
        │           │                  │
   CustodyEvent    RMA            Inspection
        │                              │
    Shipment                        Repair

ReusableAsset ──< DepositLedger
```

| File | Entity | Primary Key | Key Foreign Keys |
|---|---|---|---|
| `asset_types.csv` | AssetType | `asset_type_id` | — |
| `owners.csv` | Owner | `owner_id` | — |
| `locations.csv` | Location | `location_id` | — |
| `assets.csv` | ReusableAsset | `asset_id` | `asset_type_id`, `owner_id`, `current_location_id` |
| `shipments.csv` | Shipment | `shipment_id` | `origin_location_id`, `dest_location_id`, `carrier_id` |
| `custody_events.csv` | CustodyEvent | `event_id` | `asset_id`, `from_location_id`, `to_location_id`, `actor_id`, `shipment_id` |
| `return_authorizations.csv` | ReturnAuthorization | `rma_id` | `asset_id`, `issued_by_owner_id`, `return_to_location_id` |
| `inspections.csv` | Inspection | `inspection_id` | `asset_id`, `inspector_id`, `location_id` |
| `repairs.csv` | Repair | `repair_id` | `asset_id`, `inspection_id` *(nullable)*, `repair_facility_id` |
| `deposit_ledger.csv` | DepositLedger | `ledger_id` | `asset_id`, `rma_id` *(nullable)*, `owner_id` |
| `ground_truth.csv` | GroundTruth | `issue_id` | `asset_id` |

---

## 🏷 ID Naming Conventions

All IDs are **immutable** after generation, **zero-padded**, and **consistent across all files**.

| Entity | Format | Example |
|---|---|---|
| Reusable Asset | `ASSET-NNNNNNN` | `ASSET-0000001` |
| Return Authorization | `RMA-2026-NNNNNN` | `RMA-2026-000001` |
| Shipment | `SHP-2026-NNNNNN` | `SHP-2026-000001` |
| Custody Event | `CUST-<asset_id>-NNNNNN` | `CUST-ASSET-0000001-000001` |
| Repair | `REP-2026-NNNNNN` | `REP-2026-000001` |
| Asset Type | `AT-NNNN` | `AT-0001` |
| Owner | `OWN-NNNNN` | `OWN-00001` |
| Location | `LOC-NNNNN` | `LOC-00001` |
| Inspection | `INSP-<asset_id>-NNNN` | `INSP-ASSET-0000001-0001` |
| Deposit Entry | `DEP-NNNNNNNN` | `DEP-00000001` |
| Ground Truth | `GT-EC<N>-NNNN` | `GT-EC1-0001` |

---

## ⚠️ Edge Cases & Anomalies

Five types of labelled anomalies are injected **deterministically** into the operational data. Each is flagged in the row's `notes` field (`EDGE_CASE: <type>`) and recorded in `ground_truth.csv`.

> **Important:** `ground_truth.csv` is **never merged** into input feature files. It is an evaluation-only file.

| Code | Anomaly Type | Count | Severity | How It Manifests |
|---|---|---|---|---|
| **EC1** | `simultaneous_location` | 10 | 🔴 High | Two `received` custody events with identical `event_timestamp` but different `to_location_id` |
| **EC2** | `return_before_dispatch` | 5 | 🔴 High | A `return` event timestamp precedes the asset's `dispatch` event timestamp |
| **EC3** | `duplicate_refund` | 5 | 🟡 Medium | A second `refund` entry in `DepositLedger` for the same RMA that was already refunded |
| **EC4** | `repair_without_inspection` | 5 | 🟡 Medium | A `Repair` row with `status=completed` and an empty `inspection_id` |
| **EC5** | `missing_actor` | 20 | 🟢 Low | A `CustodyEvent` with a blank `actor_id` (no recorded handler) |

### Ground Truth Schema

```csv
issue_id,issue_type,entity,asset_id,description,severity
GT-EC1-0001,simultaneous_location,CustodyEvent,ASSET-0003421,...,high
GT-EC2-0001,return_before_dispatch,CustodyEvent,ASSET-0007812,...,high
...
```

---

## ✔️ Validation Rules

The generator runs 10 validation checks after generation and writes results to `validation_summary.json`:

| # | Check | Description |
|---|---|---|
| 1 | **PK Uniqueness** | Every primary key is unique within its table |
| 2 | **FK Integrity** | All foreign keys reference valid parent rows |
| 3 | **Enum Validation** | `lifecycle_state`, `event_type`, `result`, `status`, etc. are constrained to allowed values |
| 4 | **Date Ordering** | RMA `issued_date` ≤ `due_date`; `received_date` ≥ `issued_date` for baseline records |
| 5 | **Deposit Reconciliation** | Sum of `amount_usd` per asset = current balance; negatives flagged as EC3 |
| 6 | **Asset Traceability** | Current location can be reconstructed from the last `received` custody event |
| 7 | **Lifecycle Rules** | `is_lost = true` iff `lifecycle_state = lost` |
| 8 | **Outstanding Age** | `days_outstanding` = (received_date or today) − issued_date, computed deterministically |
| 9 | **Duplicate Detection** | No silent duplicate rows |
| 10 | **Anomaly Labels** | Edge cases are tagged, not silently corrupted |

---

## 🔁 Reproducibility

The generator uses Python's built-in `random.Random(seed)` — **not** the global `random` module state — ensuring perfect isolation.

```bash
# Run the reproducibility check: generates twice, compares every file's MD5
python generate_data.py --seed 20261022 --repro-check
```

Expected output:

```
Checksum comparison:
  [OK]  asset_types.csv
  [OK]  owners.csv
  [OK]  locations.csv
  [OK]  assets.csv
  [OK]  shipments.csv
  [OK]  custody_events.csv
  [OK]  return_authorizations.csv
  [OK]  inspections.csv
  [OK]  repairs.csv
  [OK]  deposit_ledger.csv
  [OK]  ground_truth.csv

[OK] Both runs produce identical output -- reproducibility confirmed.
```

Both runs produce **identical row counts and MD5 checksums** for all 11 output files.

---

## 🗄 Schema & SQL

The file [`schema.sql`](./schema.sql) contains a full **SQLite / PostgreSQL compatible** DDL with:

- 10 `CREATE TABLE` statements with `PRIMARY KEY`, `FOREIGN KEY`, and `CHECK` constraints
- `CREATE INDEX` statements for common query patterns (asset lookup, overdue RMAs, etc.)
- 4 analytical `CREATE VIEW` statements:

| View | Purpose |
|---|---|
| `vw_asset_current_location` | Reconstructs each asset's current location from its last `received` event |
| `vw_asset_deposit_balance` | Running deposit balance per asset |
| `vw_overdue_rma` | All overdue return authorizations with days outstanding |
| `vw_asset_lifecycle_summary` | Aggregate counts by lifecycle state and damage level |

### Load into SQLite (example)

```bash
# Create database and load schema
sqlite3 reverse_logistics.db < schema.sql

# Import a CSV (repeat for each table)
sqlite3 reverse_logistics.db ".mode csv" ".import output/full/assets.csv reusable_asset"

# Query
sqlite3 reverse_logistics.db "SELECT lifecycle_state, COUNT(*) FROM reusable_asset GROUP BY lifecycle_state;"
```

### Load into PostgreSQL (example)

```bash
psql -U postgres -d reverse_logistics -f schema.sql

COPY reusable_asset FROM '/path/to/output/full/assets.csv' CSV HEADER;
```

---

## 🔬 Data Provenance

| Attribute | Value |
|---|---|
| Data type | 100% synthetic |
| External datasets used | None |
| Personal / confidential data | None |
| Schema inspiration | GS1 / EPCIS logistics standards (public reference only) |
| Fixed seed | `20261022` |
| Generation date | 2026-11-22 |
| License | Freely usable for academic and demonstration purposes |

All provenance details are also recorded in `output/full/source_manifest.json` per the submission requirements.

---

## 📊 Evaluation Checklist

| Criterion | Status |
|---|---|
| Realistic distributions and meaningful variation | ✅ Asset types, damage levels, geographies, shipment modes all vary |
| Consistent IDs and valid FK joins across all tables | ✅ Zero FK errors in validation |
| Dependency / lifecycle consistency | ✅ Master → child generation order enforced; event history preserved |
| Correct derived values | ✅ `days_outstanding`, `is_overdue`, `balance_after`, `is_lost` computed from source records |
| Normal, boundary, failure and exception coverage | ✅ 45 labelled anomalies across 5 categories |
| Separate ground truth (never leaked into features) | ✅ `ground_truth.csv` is a standalone evaluation-only file |
| Fixed-seed reproducibility with checksum verification | ✅ MD5 verified — 11/11 files match across two independent runs |
| Documentation and lawful provenance | ✅ README, data dictionary, schema, source manifest |

---

## 👥 Primary Actors

| Actor | Role in Dataset |
|---|---|
| **Supplier** | `owner_type = supplier`; initiates RMAs, holds asset deposits |
| **Planner** | `owner_type = third_party_logistics`; sets shipment schedules and due dates |
| **Carrier / Warehouse Operator** | `owner_type = carrier / warehouse`; records custody events and inspections |
| **Logistics Analyst** | Queries `vw_overdue_rma`, `vw_asset_deposit_balance` |
| **Operations Manager** | Reviews `ground_truth.csv` anomalies and loss status reports |

---

## 📄 License

This dataset is **fully synthetic** and contains no real or personally identifiable information. It may be freely used for academic research, demonstration, and evaluation purposes.

---

*Generated with fixed seed `20261022` · Python 3.8+ · No external dependencies*
