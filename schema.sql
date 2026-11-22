-- ============================================================
-- Reverse Logistics — SQL Schema (SQLite / PostgreSQL compatible)
-- Seed: 20261022  |  Generated: 2026-11-22
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- MASTER / REFERENCE TABLES
-- ─────────────────────────────────────────────────────────────

CREATE TABLE asset_type (
    asset_type_id            VARCHAR(10)  NOT NULL,
    category                 VARCHAR(50)  NOT NULL
        CHECK (category IN ('Pallet','Crate','Container','Tote','Drum','Roll Cage','IBC','Reel')),
    variant_name             VARCHAR(100) NOT NULL UNIQUE,
    description              TEXT,
    max_capacity_kg          NUMERIC(8,2) NOT NULL CHECK (max_capacity_kg > 0),
    tare_weight_kg           NUMERIC(8,2) NOT NULL CHECK (tare_weight_kg > 0),
    material                 VARCHAR(20)  NOT NULL
        CHECK (material IN ('plastic','wood','steel','aluminium','composite')),
    max_lifetime_days        INTEGER      NOT NULL CHECK (max_lifetime_days > 0),
    inspection_interval_days INTEGER      NOT NULL CHECK (inspection_interval_days > 0),
    deposit_amount_usd       NUMERIC(10,2) NOT NULL CHECK (deposit_amount_usd > 0),
    is_returnable            BOOLEAN      NOT NULL DEFAULT TRUE,
    lifecycle_rule           VARCHAR(30)  NOT NULL
        CHECK (lifecycle_rule IN ('reuse_until_damaged','fixed_cycles','age_based')),
    max_reuse_cycles         INTEGER      NOT NULL CHECK (max_reuse_cycles > 0),
    created_at               DATE         NOT NULL,
    PRIMARY KEY (asset_type_id)
);

CREATE TABLE owner (
    owner_id      VARCHAR(12)  NOT NULL,
    owner_name    VARCHAR(200) NOT NULL,
    owner_type    VARCHAR(30)  NOT NULL
        CHECK (owner_type IN ('supplier','carrier','warehouse','customer','third_party_logistics')),
    contact_email VARCHAR(200),
    contact_phone VARCHAR(30),
    country       CHAR(2)      NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    DATE         NOT NULL,
    PRIMARY KEY (owner_id)
);

CREATE TABLE location (
    location_id    VARCHAR(12)   NOT NULL,
    location_name  VARCHAR(200)  NOT NULL,
    location_type  VARCHAR(30)   NOT NULL
        CHECK (location_type IN ('warehouse','distribution_center','supplier_site','customer_site','port','repair_center')),
    address_line1  VARCHAR(200),
    city           VARCHAR(100)  NOT NULL,
    country        CHAR(2)       NOT NULL,
    latitude       NUMERIC(9,6),
    longitude      NUMERIC(9,6),
    capacity_units INTEGER,
    is_active      BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at     DATE          NOT NULL,
    PRIMARY KEY (location_id)
);

-- ─────────────────────────────────────────────────────────────
-- CORE ASSET TABLE
-- ─────────────────────────────────────────────────────────────

CREATE TABLE reusable_asset (
    asset_id              VARCHAR(14)  NOT NULL,
    asset_type_id         VARCHAR(10)  NOT NULL,
    serial_number         VARCHAR(20)  NOT NULL UNIQUE,
    owner_id              VARCHAR(12)  NOT NULL,
    current_location_id   VARCHAR(12)  NOT NULL,
    manufacture_date      DATE         NOT NULL,
    last_inspection_date  DATE,
    lifecycle_state       VARCHAR(20)  NOT NULL
        CHECK (lifecycle_state IN ('active','in_transit','at_location','under_repair','lost','retired','decommissioned')),
    damage_level          VARCHAR(10)  NOT NULL DEFAULT 'none'
        CHECK (damage_level IN ('none','minor','moderate','severe')),
    reuse_cycle_count     INTEGER      NOT NULL DEFAULT 0 CHECK (reuse_cycle_count >= 0),
    is_lost               BOOLEAN      NOT NULL DEFAULT FALSE,
    deposit_held_usd      NUMERIC(10,2) NOT NULL CHECK (deposit_held_usd >= 0),
    created_at            DATE         NOT NULL,
    updated_at            DATE         NOT NULL,
    PRIMARY KEY (asset_id),
    FOREIGN KEY (asset_type_id)       REFERENCES asset_type (asset_type_id),
    FOREIGN KEY (owner_id)            REFERENCES owner       (owner_id),
    FOREIGN KEY (current_location_id) REFERENCES location    (location_id)
);

-- ─────────────────────────────────────────────────────────────
-- SHIPMENT TABLE
-- ─────────────────────────────────────────────────────────────

CREATE TABLE shipment (
    shipment_id          VARCHAR(18)  NOT NULL,
    origin_location_id   VARCHAR(12)  NOT NULL,
    dest_location_id     VARCHAR(12)  NOT NULL,
    carrier_id           VARCHAR(12)  NOT NULL,
    shipper_id           VARCHAR(12)  NOT NULL,
    planned_departure    DATE         NOT NULL,
    actual_departure     DATE,
    planned_arrival      DATE         NOT NULL,
    actual_arrival       DATE,
    status               VARCHAR(15)  NOT NULL
        CHECK (status IN ('scheduled','in_transit','delivered','cancelled','delayed')),
    mode                 VARCHAR(15)  NOT NULL
        CHECK (mode IN ('road','rail','air','sea','multimodal')),
    total_assets         INTEGER,
    is_return_shipment   BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at           DATE         NOT NULL,
    PRIMARY KEY (shipment_id),
    FOREIGN KEY (origin_location_id) REFERENCES location (location_id),
    FOREIGN KEY (dest_location_id)   REFERENCES location (location_id),
    FOREIGN KEY (carrier_id)         REFERENCES owner    (owner_id),
    FOREIGN KEY (shipper_id)         REFERENCES owner    (owner_id),
    CHECK (origin_location_id != dest_location_id),
    CHECK (planned_arrival >= planned_departure)
);

-- ─────────────────────────────────────────────────────────────
-- CUSTODY EVENT (APPEND-ONLY EVENT LOG)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE custody_event (
    event_id          VARCHAR(50)   NOT NULL,
    asset_id          VARCHAR(14)   NOT NULL,
    event_type        VARCHAR(30)   NOT NULL
        CHECK (event_type IN ('dispatch','in_transit','received','transfer','return','inspection_checkpoint')),
    event_timestamp   TIMESTAMP     NOT NULL,
    from_location_id  VARCHAR(12)   NOT NULL,
    to_location_id    VARCHAR(12)   NOT NULL,
    actor_id          VARCHAR(12),                   -- nullable: edge case = missing actor
    shipment_id       VARCHAR(18),                   -- optional
    notes             TEXT,
    is_disputed       BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP     NOT NULL,
    PRIMARY KEY (event_id),
    FOREIGN KEY (asset_id)          REFERENCES reusable_asset (asset_id),
    FOREIGN KEY (from_location_id)  REFERENCES location       (location_id),
    FOREIGN KEY (to_location_id)    REFERENCES location       (location_id),
    FOREIGN KEY (actor_id)          REFERENCES owner          (owner_id),
    FOREIGN KEY (shipment_id)       REFERENCES shipment       (shipment_id)
);

CREATE INDEX idx_custody_asset     ON custody_event (asset_id, event_timestamp);
CREATE INDEX idx_custody_shipment  ON custody_event (shipment_id);
CREATE INDEX idx_custody_disputed  ON custody_event (is_disputed);

-- ─────────────────────────────────────────────────────────────
-- RETURN AUTHORIZATION (RMA)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE return_authorization (
    rma_id                 VARCHAR(18)  NOT NULL,
    asset_id               VARCHAR(14)  NOT NULL,
    issued_by_owner_id     VARCHAR(12)  NOT NULL,
    return_to_location_id  VARCHAR(12)  NOT NULL,
    shipment_id            VARCHAR(18),
    issued_date            DATE         NOT NULL,
    due_date               DATE         NOT NULL,
    received_date          DATE,
    status                 VARCHAR(15)  NOT NULL
        CHECK (status IN ('pending','approved','in_transit','received','closed','disputed')),
    reason                 VARCHAR(30)  NOT NULL
        CHECK (reason IN ('end_of_lease','damaged','wrong_delivery','overstock','recall')),
    days_outstanding       INTEGER      NOT NULL CHECK (days_outstanding >= 0),   -- derived
    is_overdue             BOOLEAN      NOT NULL,                                  -- derived
    created_at             DATE         NOT NULL,
    PRIMARY KEY (rma_id),
    FOREIGN KEY (asset_id)              REFERENCES reusable_asset  (asset_id),
    FOREIGN KEY (issued_by_owner_id)    REFERENCES owner            (owner_id),
    FOREIGN KEY (return_to_location_id) REFERENCES location         (location_id),
    FOREIGN KEY (shipment_id)           REFERENCES shipment         (shipment_id),
    CHECK (due_date >= issued_date)
);

CREATE INDEX idx_rma_asset    ON return_authorization (asset_id);
CREATE INDEX idx_rma_status   ON return_authorization (status);
CREATE INDEX idx_rma_overdue  ON return_authorization (is_overdue);

-- ─────────────────────────────────────────────────────────────
-- INSPECTION
-- ─────────────────────────────────────────────────────────────

CREATE TABLE inspection (
    inspection_id        VARCHAR(30)   NOT NULL,
    asset_id             VARCHAR(14)   NOT NULL,
    inspector_id         VARCHAR(12)   NOT NULL,
    location_id          VARCHAR(12)   NOT NULL,
    inspection_date      DATE          NOT NULL,
    result               VARCHAR(20)   NOT NULL
        CHECK (result IN ('pass','fail','conditional_pass')),
    damage_level         VARCHAR(10)   NOT NULL
        CHECK (damage_level IN ('none','minor','moderate','severe')),
    notes                TEXT,
    next_inspection_due  DATE          NOT NULL,
    created_at           DATE          NOT NULL,
    PRIMARY KEY (inspection_id),
    FOREIGN KEY (asset_id)     REFERENCES reusable_asset (asset_id),
    FOREIGN KEY (inspector_id) REFERENCES owner          (owner_id),
    FOREIGN KEY (location_id)  REFERENCES location       (location_id),
    CHECK (next_inspection_due > inspection_date)
);

CREATE INDEX idx_inspection_asset  ON inspection (asset_id);
CREATE INDEX idx_inspection_result ON inspection (result);

-- ─────────────────────────────────────────────────────────────
-- REPAIR
-- ─────────────────────────────────────────────────────────────

CREATE TABLE repair (
    repair_id           VARCHAR(18)   NOT NULL,
    asset_id            VARCHAR(14)   NOT NULL,
    inspection_id       VARCHAR(30),              -- nullable: edge case = repair without inspection
    repair_facility_id  VARCHAR(12)   NOT NULL,
    technician_id       VARCHAR(12)   NOT NULL,
    start_date          DATE          NOT NULL,
    end_date            DATE,
    status              VARCHAR(15)   NOT NULL
        CHECK (status IN ('open','in_progress','completed','cancelled')),
    repair_type         VARCHAR(30)   NOT NULL
        CHECK (repair_type IN ('structural','cleaning','component_replacement','cosmetic','electrical')),
    cost_usd            NUMERIC(10,2) NOT NULL CHECK (cost_usd > 0),
    parts_replaced      VARCHAR(50),
    created_at          DATE          NOT NULL,
    PRIMARY KEY (repair_id),
    FOREIGN KEY (asset_id)          REFERENCES reusable_asset (asset_id),
    FOREIGN KEY (inspection_id)     REFERENCES inspection     (inspection_id),
    FOREIGN KEY (repair_facility_id) REFERENCES location      (location_id),
    FOREIGN KEY (technician_id)     REFERENCES owner          (owner_id)
);

CREATE INDEX idx_repair_asset  ON repair (asset_id);
CREATE INDEX idx_repair_status ON repair (status);

-- ─────────────────────────────────────────────────────────────
-- DEPOSIT LEDGER (APPEND-ONLY FINANCIAL LOG)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE deposit_ledger (
    ledger_id     VARCHAR(14)   NOT NULL,
    asset_id      VARCHAR(14)   NOT NULL,
    rma_id        VARCHAR(18),
    owner_id      VARCHAR(12)   NOT NULL,
    event_type    VARCHAR(15)   NOT NULL
        CHECK (event_type IN ('charge','refund','adjustment','penalty')),
    amount_usd    NUMERIC(10,2) NOT NULL CHECK (amount_usd != 0),
    currency      CHAR(3)       NOT NULL DEFAULT 'USD',
    event_date    DATE          NOT NULL,
    balance_after NUMERIC(10,2) NOT NULL,
    notes         TEXT,
    created_at    DATE          NOT NULL,
    PRIMARY KEY (ledger_id),
    FOREIGN KEY (asset_id) REFERENCES reusable_asset    (asset_id),
    FOREIGN KEY (rma_id)   REFERENCES return_authorization (rma_id),
    FOREIGN KEY (owner_id) REFERENCES owner              (owner_id)
);

CREATE INDEX idx_ledger_asset      ON deposit_ledger (asset_id, event_date);
CREATE INDEX idx_ledger_event_type ON deposit_ledger (event_type);

-- ─────────────────────────────────────────────────────────────
-- GROUND TRUTH (ANOMALY LABELS — evaluation only)
-- ─────────────────────────────────────────────────────────────

CREATE TABLE ground_truth (
    issue_id    VARCHAR(20)  NOT NULL,
    issue_type  VARCHAR(50)  NOT NULL
        CHECK (issue_type IN ('simultaneous_location','return_before_dispatch','duplicate_refund','repair_without_inspection','missing_actor')),
    entity      VARCHAR(30)  NOT NULL,
    asset_id    VARCHAR(14)  NOT NULL,
    description TEXT         NOT NULL,
    severity    VARCHAR(10)  NOT NULL
        CHECK (severity IN ('high','medium','low')),
    PRIMARY KEY (issue_id),
    FOREIGN KEY (asset_id) REFERENCES reusable_asset (asset_id)
);

-- ─────────────────────────────────────────────────────────────
-- USEFUL ANALYTICAL VIEWS
-- ─────────────────────────────────────────────────────────────

-- Current asset location (last received event per asset)
CREATE VIEW vw_asset_current_location AS
SELECT
    ce.asset_id,
    ce.to_location_id  AS current_location_id,
    ce.event_timestamp AS last_event_timestamp,
    ce.event_type
FROM custody_event ce
WHERE ce.event_id = (
    SELECT ce2.event_id
    FROM   custody_event ce2
    WHERE  ce2.asset_id = ce.asset_id
      AND  ce2.event_type = 'received'
    ORDER  BY ce2.event_timestamp DESC
    LIMIT  1
);

-- Deposit balance per asset
CREATE VIEW vw_asset_deposit_balance AS
SELECT
    asset_id,
    SUM(amount_usd) AS total_balance_usd,
    COUNT(*)        AS total_transactions
FROM deposit_ledger
GROUP BY asset_id;

-- Overdue RMAs with days outstanding
CREATE VIEW vw_overdue_rma AS
SELECT
    rma_id,
    asset_id,
    issued_date,
    due_date,
    days_outstanding,
    status,
    reason
FROM return_authorization
WHERE is_overdue = TRUE
ORDER BY days_outstanding DESC;

-- Asset lifecycle state summary
CREATE VIEW vw_asset_lifecycle_summary AS
SELECT
    lifecycle_state,
    damage_level,
    COUNT(*)                   AS asset_count,
    AVG(reuse_cycle_count)     AS avg_reuse_cycles,
    AVG(deposit_held_usd)      AS avg_deposit_usd
FROM reusable_asset
GROUP BY lifecycle_state, damage_level
ORDER BY lifecycle_state, damage_level;
