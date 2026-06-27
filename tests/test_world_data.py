from typing import Any, cast

from ghostliness.protocol.types import Buffer
from ghostliness.world_data import empty_tags, encode_empty_chunk_data, minimal_registries


def test_overworld_dimension_type_matches_26_2_required_fields():
    dimension_registry = next(
        registry
        for registry in minimal_registries()
        if registry["id"] == "minecraft:dimension_type"
    )
    entries = cast(list[dict[str, Any]], dimension_registry["entries"])
    entry = entries[0]
    value = cast(dict[str, Any], entry["value"])

    assert value["has_ender_dragon_fight"] is False
    assert value["infiniburn"] == "#minecraft:infiniburn_overworld"


def test_infiniburn_overworld_tag_is_declared():
    block_tags = empty_tags()[0]

    assert block_tags == {
        "tagType": "minecraft:block",
        "tags": [{"tagName": "minecraft:infiniburn_overworld", "entries": []}],
    }


def test_26_2_required_synchronized_registries_are_non_empty():
    required = {
        "minecraft:cat_sound_variant",
        "minecraft:cat_variant",
        "minecraft:chicken_sound_variant",
        "minecraft:chicken_variant",
        "minecraft:cow_sound_variant",
        "minecraft:cow_variant",
        "minecraft:frog_variant",
        "minecraft:painting_variant",
        "minecraft:pig_sound_variant",
        "minecraft:pig_variant",
        "minecraft:wolf_sound_variant",
        "minecraft:wolf_variant",
        "minecraft:zombie_nautilus_variant",
    }
    registries = {str(registry["id"]): registry for registry in minimal_registries()}

    assert required <= registries.keys()
    for registry_id in required:
        entries = cast(list[dict[str, Any]], registries[registry_id]["entries"])
        assert entries, registry_id


def test_damage_type_registry_contains_fire_damage_types_required_by_items():
    registries = {str(registry["id"]): registry for registry in minimal_registries()}
    damage_type_registry = registries["minecraft:damage_type"]
    entries = cast(list[dict[str, Any]], damage_type_registry["entries"])
    keys = {str(entry["key"]) for entry in entries}

    assert {
        "minecraft:in_fire",
        "minecraft:campfire",
        "minecraft:on_fire",
        "minecraft:lava",
        "minecraft:hot_floor",
        "minecraft:sulfur_cube_hot",
        "minecraft:unattributed_fireball",
        "minecraft:fireball",
    } <= keys


def test_trim_registries_contain_item_component_dependencies():
    registries = {str(registry["id"]): registry for registry in minimal_registries()}
    trim_material_entries = cast(
        list[dict[str, Any]], registries["minecraft:trim_material"]["entries"]
    )
    trim_pattern_entries = cast(
        list[dict[str, Any]], registries["minecraft:trim_pattern"]["entries"]
    )

    assert "minecraft:redstone" in {
        str(entry["key"]) for entry in trim_material_entries
    }
    assert "minecraft:bolt" in {str(entry["key"]) for entry in trim_pattern_entries}
    assert len(trim_material_entries) == 11
    assert len(trim_pattern_entries) == 18


def test_jukebox_song_registry_contains_music_disc_component_dependencies():
    registries = {str(registry["id"]): registry for registry in minimal_registries()}
    jukebox_song_entries = cast(
        list[dict[str, Any]], registries["minecraft:jukebox_song"]["entries"]
    )
    entries_by_key = {str(entry["key"]): entry for entry in jukebox_song_entries}

    assert "minecraft:13" in entries_by_key
    assert len(jukebox_song_entries) == 22
    assert entries_by_key["minecraft:13"]["value"] == {
        "comparator_output": 1,
        "description": {"translate": "jukebox_song.minecraft.13"},
        "length_in_seconds": 178.0,
        "sound_event": "minecraft:music_disc.13",
    }


def test_banner_pattern_registry_contains_pattern_item_tag_dependencies():
    registries = {str(registry["id"]): registry for registry in minimal_registries()}
    banner_pattern_entries = cast(
        list[dict[str, Any]], registries["minecraft:banner_pattern"]["entries"]
    )
    registry_key_by_id = {
        index: str(entry["key"]) for index, entry in enumerate(banner_pattern_entries)
    }
    banner_pattern_tags = next(
        tags
        for tags in empty_tags()
        if tags["tagType"] == "minecraft:banner_pattern"
    )
    tags_by_name = {
        str(tag["tagName"]): cast(list[int], tag["entries"])
        for tag in cast(list[dict[str, object]], banner_pattern_tags["tags"])
    }

    assert len(banner_pattern_entries) == 43
    assert "minecraft:flower" in registry_key_by_id.values()
    assert tags_by_name["minecraft:pattern_item/flower"]
    assert {
        registry_key_by_id[index]
        for index in tags_by_name["minecraft:pattern_item/flower"]
    } == {"minecraft:flower"}
    for tag_entries in tags_by_name.values():
        assert all(index in registry_key_by_id for index in tag_entries)


def test_instrument_registry_contains_goat_horn_component_dependencies():
    registries = {str(registry["id"]): registry for registry in minimal_registries()}
    instrument_entries = cast(
        list[dict[str, Any]], registries["minecraft:instrument"]["entries"]
    )
    registry_key_by_id = {
        index: str(entry["key"]) for index, entry in enumerate(instrument_entries)
    }
    instrument_tags = next(
        tags for tags in empty_tags() if tags["tagType"] == "minecraft:instrument"
    )
    tags_by_name = {
        str(tag["tagName"]): cast(list[int], tag["entries"])
        for tag in cast(list[dict[str, object]], instrument_tags["tags"])
    }

    assert len(instrument_entries) == 8
    assert "minecraft:ponder_goat_horn" in registry_key_by_id.values()
    assert {
        registry_key_by_id[index] for index in tags_by_name["minecraft:goat_horns"]
    } == set(registry_key_by_id.values())
    assert {
        registry_key_by_id[index]
        for index in tags_by_name["minecraft:regular_goat_horns"]
    } == {
        "minecraft:ponder_goat_horn",
        "minecraft:sing_goat_horn",
        "minecraft:seek_goat_horn",
        "minecraft:feel_goat_horn",
    }
    for tag_entries in tags_by_name.values():
        assert all(index in registry_key_by_id for index in tag_entries)


def test_animal_variant_registries_include_26_2_vanilla_variants():
    registries = {str(registry["id"]): registry for registry in minimal_registries()}

    expected_keys = {
        "minecraft:chicken_variant": {
            "minecraft:cold",
            "minecraft:temperate",
            "minecraft:warm",
        },
        "minecraft:cow_variant": {
            "minecraft:cold",
            "minecraft:temperate",
            "minecraft:warm",
        },
        "minecraft:pig_variant": {
            "minecraft:cold",
            "minecraft:temperate",
            "minecraft:warm",
        },
        "minecraft:frog_variant": {
            "minecraft:cold",
            "minecraft:temperate",
            "minecraft:warm",
        },
        "minecraft:cat_variant": {
            "minecraft:all_black",
            "minecraft:tabby",
            "minecraft:white",
        },
        "minecraft:wolf_variant": {
            "minecraft:ashen",
            "minecraft:pale",
            "minecraft:woods",
        },
        "minecraft:zombie_nautilus_variant": {
            "minecraft:temperate",
            "minecraft:warm",
        },
    }

    for registry_id, keys in expected_keys.items():
        entries = cast(list[dict[str, Any]], registries[registry_id]["entries"])
        assert keys <= {str(entry["key"]) for entry in entries}


def test_damage_type_is_fire_tag_is_declared_with_valid_registry_ids():
    registries = {str(registry["id"]): registry for registry in minimal_registries()}
    damage_type_registry = registries["minecraft:damage_type"]
    registry_entries = cast(list[dict[str, Any]], damage_type_registry["entries"])
    registry_key_by_id = {
        index: str(entry["key"]) for index, entry in enumerate(registry_entries)
    }
    damage_type_tags = next(
        tags for tags in empty_tags() if tags["tagType"] == "minecraft:damage_type"
    )
    tags_by_name = {
        str(tag["tagName"]): cast(list[int], tag["entries"])
        for tag in cast(list[dict[str, object]], damage_type_tags["tags"])
    }

    assert "minecraft:is_fire" in tags_by_name
    assert {
        registry_key_by_id[index] for index in tags_by_name["minecraft:is_fire"]
    } == {
        "minecraft:in_fire",
        "minecraft:campfire",
        "minecraft:on_fire",
        "minecraft:lava",
        "minecraft:hot_floor",
        "minecraft:sulfur_cube_hot",
        "minecraft:unattributed_fireball",
        "minecraft:fireball",
    }
    for tag_entries in tags_by_name.values():
        assert all(index in registry_key_by_id for index in tag_entries)


def test_empty_chunk_uses_synchronized_biome_registry_id():
    chunk_data = encode_empty_chunk_data(section_count=1)
    buffer = Buffer(chunk_data)

    assert buffer.read_short() == 0
    assert buffer.read_unsigned_byte() == 0
    assert buffer.read_varint() == 0
    assert buffer.read_varint() == 0
    assert buffer.read_unsigned_byte() == 0
    assert buffer.read_varint() == 0
    assert buffer.read_varint() == 0
    buffer.ensure_consumed()
