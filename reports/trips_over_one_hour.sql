-- Bonus report: count of trips whose duration (pickup -> dropoff) exceeded one
-- hour, grouped by month and driver.
--
-- A trip's duration is the time between its 'Status changed to pickup' and
-- 'Status changed to dropoff' RideEvents. The driver label matches the sample
-- output format: first name + a space + the last-name initial (e.g. "Chris H").
--
-- Tables: rides, ride_events, users (explicit db_table names); FK columns
-- id_ride and id_driver.
--
-- Note: this self-join assumes a single pickup and a single dropoff event per
-- ride (per the brief). If a ride could have duplicate status events, replace
-- the two joins with a per-ride aggregate, e.g.:
--   SELECT id_ride,
--          min(created_at) FILTER (WHERE description = 'Status changed to pickup')  AS pickup_at,
--          min(created_at) FILTER (WHERE description = 'Status changed to dropoff') AS dropoff_at
--   FROM ride_events GROUP BY id_ride
-- and filter on (dropoff_at - pickup_at) > interval '1 hour'.

SELECT
    to_char(pickup.created_at, 'YYYY-MM')                      AS month,
    concat(driver.first_name, ' ', left(driver.last_name, 1))  AS driver,
    count(*)                                                   AS trips_over_one_hour
FROM rides r
JOIN ride_events pickup
    ON pickup.id_ride = r.id_ride
   AND pickup.description = 'Status changed to pickup'
JOIN ride_events dropoff
    ON dropoff.id_ride = r.id_ride
   AND dropoff.description = 'Status changed to dropoff'
JOIN users driver
    ON driver.id_user = r.id_driver
WHERE dropoff.created_at - pickup.created_at > interval '1 hour'
GROUP BY month, driver
ORDER BY month, driver;
