# nala/athomic/config/schemas/server/server_config.py
from pydantic import BaseModel, ConfigDict, Field


class ServerSettings(BaseModel):
    """Defines the network binding settings for the application server.

    This model configures the host and port on which the web server (e.g., Uvicorn)
    will listen for incoming HTTP requests.

    Attributes:
        host (str): The hostname or IP address to bind to.
        port (int): The TCP port number to listen on.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    host: str = Field(
        default="127.0.0.1",
        alias="SERVER_HOST",
        description="The hostname or IP address to which the server will bind. Use '0.0.0.0' to listen on all available network interfaces.",
    )
    port: int = Field(
        default=8000,
        alias="SERVER_PORT",
        description="The TCP port number on which the server will listen for incoming connections.",
    )
