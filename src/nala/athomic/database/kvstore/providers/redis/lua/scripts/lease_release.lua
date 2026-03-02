-- lease_release.lua
-- Purpose: Release a lease only if owned by the caller
--
-- KEYS[1] = lease key
-- ARGV[1] = owner id

local lease_json = redis.call('GET', KEYS[1])

if not lease_json then
    return 0
end

local lease = cjson.decode(lease_json)

if lease['owner_id'] == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end