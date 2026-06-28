from ghostliness.auth import GameProfile, offline_uuid
from ghostliness.server.player import Player, PlayerPose
from ghostliness.world import BlockPosition, Position


def test_player_bounding_box_uses_standing_dimensions_and_open_intersection():
    player = Player(
        profile=GameProfile(offline_uuid("Tester"), "Tester"),
        position=Position(x=0.5, y=65.0, z=0.5),
        connection_id="test",
    )

    box = player.bounding_box

    assert box.min_x == 0.2
    assert box.max_x == 0.8
    assert box.min_y == 65.0
    assert box.max_y == 66.8
    assert box.intersects_block(BlockPosition(0, 65, 0)) is True
    assert box.intersects_block(BlockPosition(0, 66, 0)) is True
    assert box.intersects_block(BlockPosition(0, 67, 0)) is False
    assert box.intersects_block(BlockPosition(1, 65, 0)) is False


def test_player_sneaking_pose_uses_shorter_height():
    player = Player(
        profile=GameProfile(offline_uuid("Tester"), "Tester"),
        position=Position(x=0.5, y=65.0, z=0.5),
        connection_id="test",
    )

    player.set_sneaking(True)

    assert player.sneaking is True
    assert player.pose == PlayerPose.SNEAKING
    assert player.bounding_box.max_y == 66.5
    player.set_sneaking(False)
    assert player.sneaking is False
    assert player.pose == PlayerPose.STANDING
    assert player.bounding_box.max_y == 66.8
