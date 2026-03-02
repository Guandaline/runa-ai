from pathlib import Path

from nala.athomic.base.instance_registry import BaseInstanceRegistry


class RedisLuaScriptRegistry(BaseInstanceRegistry[Path]):
    """
    Registry for Redis Lua script files.

    This registry maps a logical script name to its corresponding
    filesystem path. Scripts are loaded and executed by the
    RedisLuaLoader and RedisLuaExecutor.
    """

    def __init__(self) -> None:
        super().__init__(protocol=Path)

        base_dir = Path(__file__).parent / "scripts"

        self.register("zpopbyscore", base_dir / "zpopbyscore.lua")
        self.register("lease_renew", base_dir / "lease_renew.lua")
        self.register("lease_release", base_dir / "lease_release.lua")
        self.register("rate_limit", base_dir / "rate_limit.lua")


redis_lua_script_registry = RedisLuaScriptRegistry()
