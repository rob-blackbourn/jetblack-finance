-- Active: 1731135592331@@127.0.0.1@3306@trading
SELECT * FROM trading.trade;
SELECT * FROM trading.unmatched_trade;
SELECT * FROM trading.matched_trade;
SELECT * FROM trading.pnl;

SELECT
    *
FROM
    trading.pnl
WHERE
    ticker = 'AAPL'
AND
    book = 'tech'
AND
    valid_from <= '2000-01-01 09:00:10' AND '2000-01-01 09:00:10' < valid_to;

SELECT
    COUNT(*)
FROM
    trading.pnl
WHERE
    ticker = 'AAPL'
AND
    book = 'tech'
AND
    valid_from >= '2000-01-01 09:00:04';
