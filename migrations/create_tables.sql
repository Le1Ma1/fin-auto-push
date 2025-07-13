-- 1. 全球資產市值
create table if not exists global_assets (
    id bigserial primary key,
    symbol text not null,
    name text,
    asset_type text,
    date date not null,
    market_cap float,
    rank integer,
    data_json jsonb,
    created_at timestamp default now(),
    unique (symbol, date)
);

-- 2. ETF 標的清單
create table if not exists etf_targets (
    id bigserial primary key,
    symbol text not null unique,
    name text,
    url text,
    is_active boolean default true,
    created_at timestamp default now()
);

-- 3. ETF 資金流向
create table if not exists etf_flows (
    id bigserial primary key,
    symbol text not null,
    date date not null,
    net_flow float,
    aum float,
    price float,
    data_json jsonb,
    created_at timestamp default now(),
    unique (symbol, date),
    foreign key (symbol) references etf_targets(symbol)
);

-- 4. 推播紀錄
create table if not exists push_logs (
    id bigserial primary key,
    group_id text,
    message_type text,
    content text,
    image_url text,
    sent_at timestamp,
    created_at timestamp default now()
);

-- 5. 異常監控
create table if not exists alerts (
    id bigserial primary key,
    alert_type text,
    ref_table text,
    ref_id bigint,
    message text,
    status text default 'new',
    created_at timestamp default now()
);
