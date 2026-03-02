-- zpopbyscore.lua
-- Purpose: Atomically pop one member from a sorted set with score <= max_score
--
-- KEYS[1] = zset key
-- ARGV[1] = max score (inclusive)

local zset_key = KEYS[1]
local max_score = ARGV[1]

local items = redis.call(
    "ZRANGEBYSCORE",
    zset_key,
    "-inf",
    max_score,
    "LIMIT",
    0,
    1
)

if #items == 0 then
    return nil
end

redis.call("ZREM", zset_key, items[1])
return items[1]
