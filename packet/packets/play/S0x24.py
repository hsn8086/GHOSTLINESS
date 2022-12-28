from data_types import Byte, Array, NBT, Long, VarInt, Position
from packet.base_packet import BasePacket


class S0x24(BasePacket):
    def __init__(self):
        super().__init__()
        self.packet_id = 24
        self.fields_structure = \
            [int,  # Entity ID      The player's Entity ID (EID).
             bool,  # Is hardcore
             Byte,  # Gamemode      0: Survival, 1: Creative, 2: Adventure, 3: Spectator.
             Byte,
             # Previous Gamemode        0: survival, 1: creative, 2: adventure, 3: spectator. The hardcore flag is not included. The previous gamemode. Defaults to -1 if there is no previous gamemode. (More information needed)
             Array,  # Dimension Names     Identifiers for all dimensions on the server.
             NBT,
             # Registry Codec       Represents certain registries that are sent from the server and are applied on the client.
             str,  # Dimension Type        Identifier	Name of the dimension type being spawned into.
             str,  # Dimension Name        Identifier	Name of the dimension being spawned into.
             Long,
             # Hashed seed      First 8 bytes of the SHA-256 hash of the world's seed. Used client side for biome noise
             VarInt,  # Max Players        Was once used by the client to draw the player list, but now is ignored.
             VarInt,  # View Distance      Render distance (2-32).
             VarInt,
             # Simulation Distance        The distance that the client will process specific things, such as entities.
             bool,
             # Reduced Debug Info       If true, a Notchian client shows reduced information on the debug screen. For servers in development, this should almost always be false.
             bool,  # Enable respawn screen        Set to false when the doImmediateRespawn gamerule is true.
             bool,
             # Is Debug     True if the world is a debug mode world; debug mode worlds cannot be modified and have predefined blocks.
             bool,
             # Is Flat      True if the world is a superflat world; flat worlds have different void fog and a horizon at y=0 instead of y=63.
             bool,  # Has death location       If true, then the next two fields are present.
             str,  # Death dimension name      Name of the dimension the player died in.
             Position  # Death location        The location that the player died at.
             ]
