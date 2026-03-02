-- lease_renew.lua
-- KEYS[1] = lease key
-- ARGV[1] = owner_id
-- ARGV[2] = current version
-- ARGV[3] = ttl seconds
-- ARGV[4] = new lease json

local lease_json = redis.call('GET', KEYS[1])
if not lease_json then
    return 0
end

local lease = cjson.decode(lease_json)

-- Atomically checks owner AND version before renewing
if lease['owner_id'] ~= ARGV[1] or lease['version'] ~= tonumber(ARGV[2]) then
    return 0
end

-- Sets the new lease content (with incremented version and new expiration)
redis.call('SET', KEYS[1], ARGV[4], 'EX', ARGV[3])
return 1