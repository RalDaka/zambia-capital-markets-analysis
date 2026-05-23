-- Preview data
select *
from luse_historical_prices
limit 10;

-- Records per ticker
select 
    ticker,
    count(*) as records,
    min(trade_date) as first_date,
    max(trade_date) as latest_date
from luse_historical_prices
group by ticker
order by ticker;

-- Latest price per ticker
select distinct on (ticker)
    ticker,
    trade_date,
    price,
    volume
from luse_historical_prices
order by ticker, trade_date desc;

-- Top stocks by total return
with first_last as (
    select
        ticker,
        first_value(price) over (
            partition by ticker order by trade_date
        ) as first_price,
        first_value(price) over (
            partition by ticker order by trade_date desc
        ) as latest_price
    from luse_historical_prices
)
select distinct
    ticker,
    first_price,
    latest_price,
    round(((latest_price - first_price) / first_price) * 100, 2) as total_return_percent
from first_last
where first_price > 0
order by total_return_percent desc;

-- Most volatile stocks
select
    ticker,
    round(stddev(daily_return) * 100, 4) as volatility_percent
from luse_historical_prices
where daily_return is not null
group by ticker
order by volatility_percent desc;

-- Most traded stocks
select
    ticker,
    sum(volume) as total_volume
from luse_historical_prices
group by ticker
order by total_volume desc;