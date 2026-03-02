-- rate_limit.lua
--
-- Fixed window rate limiting using Redis.
-- This script implements the same semantics as:
--   INCR key
--   if value == 1 then EXPIRE key window_seconds
--   allow if value <= max_requests
--
-- KEYS[1] = rate limit key
-- ARGV[1] = max_requests (int)
-- ARGV[2] = window_seconds (int)
--
-- Returns:
--   1 -> allowed
--   0 -> denied

local key = KEYS[1]
local max_requests = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])

-- Increment the counter
local current = redis.call("INCR", key)

-- If this is the first request in the window, set expiration
if current == 1 then
    redis.call("EXPIRE", key, window_seconds)
end

-- Allow if under or equal the limit
if current <= max_requests then
    return 1
end

-- Otherwise deny
return 0
