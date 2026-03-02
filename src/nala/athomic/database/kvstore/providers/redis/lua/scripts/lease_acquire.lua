-- lease_acquire.lua
-- Purpose: Acquire or renew a lease if owned by the same owner
--
-- KEYS[1] = lease key
-- ARGV[1] = owner id
-- ARGV[2] = ttl in milliseconds

if redis.call("EXISTS", KEYS[1]) == 0 then
    redis.call("SET", KEYS[1], ARGV[1], "PX", ARGV[2])
    return 1
end

local current_owner = redis.call("GET", KEYS[1])

if current_owner == ARGV[1] then
    redis.call("PEXPIRE", KEYS[1], ARGV[2])
    return 1
end

return 0
