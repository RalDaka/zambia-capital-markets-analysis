-- Run this in Supabase SQL Editor (https://supabase.com/dashboard/project/pkqekyvzwtarmjujcfva/sql/new)

-- 1. Create a function to get table summary stats
CREATE OR REPLACE FUNCTION public.get_luse_historical_summary()
RETURNS TABLE (
    total_rows bigint,
    number_of_companies bigint,
    earliest_date date,
    latest_date date
)
LANGUAGE sql
AS $$
    SELECT
        count(*)::bigint as total_rows,
        count(distinct ticker)::bigint as number_of_companies,
        min(trade_date)::date as earliest_date,
        max(trade_date)::date as latest_date
    FROM public.luse_historical_prices;
$$;

-- 2. Create a function to get distinct tickers
CREATE OR REPLACE FUNCTION public.get_luse_distinct_tickers()
RETURNS TABLE (ticker text)
LANGUAGE sql
AS $$
    SELECT distinct ticker::text
    FROM public.luse_historical_prices
    ORDER BY ticker;
$$;

-- 3. Create a function to get luse_index summary
CREATE OR REPLACE FUNCTION public.get_luse_index_summary()
RETURNS TABLE (
    total_rows bigint,
    earliest_date date,
    latest_date date
)
LANGUAGE sql
AS $$
    SELECT
        count(*)::bigint as total_rows,
        min(index_date)::date as earliest_date,
        max(index_date)::date as latest_date
    FROM public.luse_index;
$$;

-- 4. Create a function to get all historical prices (efficient server-side query)
CREATE OR REPLACE FUNCTION public.get_luse_all_prices()
RETURNS TABLE (
    ticker text,
    trade_date date,
    price numeric,
    volume bigint,
    daily_return numeric
)
LANGUAGE sql
AS $$
    SELECT
        ticker::text,
        trade_date::date,
        price::numeric,
        volume::bigint,
        daily_return::numeric
    FROM public.luse_historical_prices
    ORDER BY ticker, trade_date;
$$;

-- 5. Create a function to get all index data
CREATE OR REPLACE FUNCTION public.get_luse_all_index()
RETURNS TABLE (
    index_date date,
    luse_index numeric
)
LANGUAGE sql
AS $$
    SELECT
        index_date::date,
        luse_index::numeric
    FROM public.luse_index
    ORDER BY index_date;
$$;
