CREATE TABLE market_snapshot (
    id SERIAL PRIMARY KEY,
    pair VARCHAR(20) NOT NULL,
    market_price NUMERIC(20,8),
    buy_volume NUMERIC(20,8) DEFAULT 0,
    sell_volume NUMERIC(20,8) DEFAULT 0,
    remaining_volume NUMERIC(20,8) DEFAULT 0,
    buy_total NUMERIC(20,8) DEFAULT 0,
    sell_total NUMERIC(20,8) DEFAULT 0,
    cost NUMERIC(20,8) DEFAULT 0,
    current_value NUMERIC(20,8) DEFAULT 0,
    potential_value NUMERIC(20,8) DEFAULT 0,
    total_value NUMERIC(20,8) DEFAULT 0,
    realized_roi NUMERIC(10,4) DEFAULT 0,
    potential_roi NUMERIC(10,4) DEFAULT 0
);


CREATE TABLE main_summary_metrics (
    id SERIAL PRIMARY KEY,
    token VARCHAR(20) NOT NULL,
    pair VARCHAR(20) NOT NULL,
    total_cost NUMERIC(20,8) NOT NULL,
    realized_sells NUMERIC(20,8) NOT NULL,
    unrealized_value NUMERIC(20,8) NOT NULL,
    total_value NUMERIC(20,8) NOT NULL,
    roi NUMERIC(10,4),          -- % realized ROI
    potential_roi NUMERIC(10,4) -- % potential ROI
);

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    unique_id VARCHAR(50) NOT NULL,
    trade_date TIMESTAMP NOT NULL,
    pair VARCHAR(20) NOT NULL,
    trade_type VARCHAR(10) NOT NULL, -- Buy or Sell
    execution_type VARCHAR(10) NOT NULL, -- Limit or Market
    trade_price NUMERIC(20,8) NOT NULL,
    transaction_price NUMERIC(20,8) NOT NULL,
    transferred_volume NUMERIC(20,8) NOT NULL,
    fee NUMERIC(20,8) NOT NULL,
    token VARCHAR(20) NOT NULL,
    currency VARCHAR(10) NOT NULL
);
