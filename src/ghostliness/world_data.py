from __future__ import annotations

from dataclasses import dataclass

from ghostliness.protocol.types import Writer

WORLD_NAMES = ("minecraft:overworld",)
OVERWORLD_REGISTRY_ID = "minecraft:dimension_type"
OVERWORLD_DIMENSION_ID = 0
VOID_BIOME_ID = 0


@dataclass(frozen=True, slots=True)
class SpawnInfo:
    entity_id: int = 1
    dimension_name: str = "minecraft:overworld"
    gamemode: int = 1
    previous_gamemode: int = 255
    spawn_x: int = 0
    spawn_y: int = 64
    spawn_z: int = 0


def _banner_pattern_value(name: str) -> dict[str, object]:
    return {
        "asset_id": f"minecraft:{name}",
        "translation_key": f"block.minecraft.banner.{name}",
    }


REQUIRED_SYNCHRONIZED_REGISTRIES: tuple[dict[str, object], ...] = (
    {
        "id": "minecraft:cat_sound_variant",
        "entries": [
            {
                "key": "minecraft:classic",
                "value": {
                    "adult_sounds": {
                        "ambient_sound": "minecraft:entity.cat.ambient",
                        "beg_for_food_sound": "minecraft:entity.cat.beg_for_food",
                        "death_sound": "minecraft:entity.cat.death",
                        "eat_sound": "minecraft:entity.cat.eat",
                        "hiss_sound": "minecraft:entity.cat.hiss",
                        "hurt_sound": "minecraft:entity.cat.hurt",
                        "purr_sound": "minecraft:entity.cat.purr",
                        "purreow_sound": "minecraft:entity.cat.purreow",
                        "stray_ambient_sound": "minecraft:entity.cat.stray_ambient",
                    },
                    "baby_sounds": {
                        "ambient_sound": "minecraft:entity.baby_cat.ambient",
                        "beg_for_food_sound": "minecraft:entity.baby_cat.beg_for_food",
                        "death_sound": "minecraft:entity.baby_cat.death",
                        "eat_sound": "minecraft:entity.baby_cat.eat",
                        "hiss_sound": "minecraft:entity.baby_cat.hiss",
                        "hurt_sound": "minecraft:entity.baby_cat.hurt",
                        "purr_sound": "minecraft:entity.baby_cat.purr",
                        "purreow_sound": "minecraft:entity.baby_cat.purreow",
                        "stray_ambient_sound": "minecraft:entity.baby_cat.stray_ambient",
                    },
                },
            }
        ],
    },
    {
        "id": "minecraft:cat_variant",
        "entries": [
            {
                "key": "minecraft:tabby",
                "value": {
                    "asset_id": "minecraft:entity/cat/cat_tabby",
                    "baby_asset_id": "minecraft:entity/cat/cat_tabby_baby",
                    "spawn_conditions": [{"priority": 0}],
                },
            }
        ],
    },
    {
        "id": "minecraft:chicken_sound_variant",
        "entries": [
            {
                "key": "minecraft:classic",
                "value": {
                    "adult_sounds": {
                        "ambient_sound": "minecraft:entity.chicken.ambient",
                        "death_sound": "minecraft:entity.chicken.death",
                        "hurt_sound": "minecraft:entity.chicken.hurt",
                        "step_sound": "minecraft:entity.chicken.step",
                    },
                    "baby_sounds": {
                        "ambient_sound": "minecraft:entity.baby_chicken.ambient",
                        "death_sound": "minecraft:entity.baby_chicken.death",
                        "hurt_sound": "minecraft:entity.baby_chicken.hurt",
                        "step_sound": "minecraft:entity.baby_chicken.step",
                    },
                },
            }
        ],
    },
    {
        "id": "minecraft:chicken_variant",
        "entries": [
            {
                "key": "minecraft:temperate",
                "value": {
                    "asset_id": "minecraft:entity/chicken/chicken_temperate",
                    "baby_asset_id": "minecraft:entity/chicken/chicken_temperate_baby",
                    "spawn_conditions": [{"priority": 0}],
                },
            }
        ],
    },
    {
        "id": "minecraft:cow_sound_variant",
        "entries": [
            {
                "key": "minecraft:classic",
                "value": {
                    "ambient_sound": "minecraft:entity.cow.ambient",
                    "death_sound": "minecraft:entity.cow.death",
                    "hurt_sound": "minecraft:entity.cow.hurt",
                    "step_sound": "minecraft:entity.cow.step",
                },
            }
        ],
    },
    {
        "id": "minecraft:cow_variant",
        "entries": [
            {
                "key": "minecraft:temperate",
                "value": {
                    "asset_id": "minecraft:entity/cow/cow_temperate",
                    "baby_asset_id": "minecraft:entity/cow/cow_temperate_baby",
                    "spawn_conditions": [{"priority": 0}],
                },
            }
        ],
    },
    {
        "id": "minecraft:frog_variant",
        "entries": [
            {
                "key": "minecraft:temperate",
                "value": {
                    "asset_id": "minecraft:entity/frog/frog_temperate",
                    "spawn_conditions": [{"priority": 0}],
                },
            }
        ],
    },
    {
        "id": "minecraft:painting_variant",
        "entries": [
            {
                "key": "minecraft:kebab",
                "value": {
                    "asset_id": "minecraft:kebab",
                    "author": {
                        "color": "gray",
                        "translate": "painting.minecraft.kebab.author",
                    },
                    "height": 1,
                    "title": {
                        "color": "yellow",
                        "translate": "painting.minecraft.kebab.title",
                    },
                    "width": 1,
                },
            }
        ],
    },
    {
        "id": "minecraft:pig_sound_variant",
        "entries": [
            {
                "key": "minecraft:classic",
                "value": {
                    "adult_sounds": {
                        "ambient_sound": "minecraft:entity.pig.ambient",
                        "death_sound": "minecraft:entity.pig.death",
                        "eat_sound": "minecraft:entity.pig.eat",
                        "hurt_sound": "minecraft:entity.pig.hurt",
                        "step_sound": "minecraft:entity.pig.step",
                    },
                    "baby_sounds": {
                        "ambient_sound": "minecraft:entity.baby_pig.ambient",
                        "death_sound": "minecraft:entity.baby_pig.death",
                        "eat_sound": "minecraft:entity.baby_pig.eat",
                        "hurt_sound": "minecraft:entity.baby_pig.hurt",
                        "step_sound": "minecraft:entity.baby_pig.step",
                    },
                },
            }
        ],
    },
    {
        "id": "minecraft:pig_variant",
        "entries": [
            {
                "key": "minecraft:temperate",
                "value": {
                    "asset_id": "minecraft:entity/pig/pig_temperate",
                    "baby_asset_id": "minecraft:entity/pig/pig_temperate_baby",
                    "spawn_conditions": [{"priority": 0}],
                },
            }
        ],
    },
    {
        "id": "minecraft:wolf_sound_variant",
        "entries": [
            {
                "key": "minecraft:classic",
                "value": {
                    "adult_sounds": {
                        "ambient_sound": "minecraft:entity.wolf.ambient",
                        "death_sound": "minecraft:entity.wolf.death",
                        "growl_sound": "minecraft:entity.wolf.growl",
                        "hurt_sound": "minecraft:entity.wolf.hurt",
                        "pant_sound": "minecraft:entity.wolf.pant",
                        "step_sound": "minecraft:entity.wolf.step",
                        "whine_sound": "minecraft:entity.wolf.whine",
                    },
                    "baby_sounds": {
                        "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                        "death_sound": "minecraft:entity.baby_wolf.death",
                        "growl_sound": "minecraft:entity.baby_wolf.growl",
                        "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                        "pant_sound": "minecraft:entity.baby_wolf.pant",
                        "step_sound": "minecraft:entity.baby_wolf.step",
                        "whine_sound": "minecraft:entity.baby_wolf.whine",
                    },
                },
            }
        ],
    },
    {
        "id": "minecraft:wolf_variant",
        "entries": [
            {
                "key": "minecraft:pale",
                "value": {
                    "assets": {
                        "angry": "minecraft:entity/wolf/wolf_angry",
                        "tame": "minecraft:entity/wolf/wolf_tame",
                        "wild": "minecraft:entity/wolf/wolf",
                    },
                    "baby_assets": {
                        "angry": "minecraft:entity/wolf/wolf_angry_baby",
                        "tame": "minecraft:entity/wolf/wolf_tame_baby",
                        "wild": "minecraft:entity/wolf/wolf_baby",
                    },
                    "spawn_conditions": [{"priority": 0}],
                },
            }
        ],
    },
    {
        "id": "minecraft:zombie_nautilus_variant",
        "entries": [
            {
                "key": "minecraft:temperate",
                "value": {
                    "asset_id": "minecraft:entity/nautilus/zombie_nautilus",
                    "spawn_conditions": [{"priority": 0}],
                },
            }
        ],
    },
)


VANILLA_SYNCHRONIZED_REGISTRY_OVERRIDES: dict[
    str, tuple[tuple[str, dict[str, object]], ...]
] = {
    "minecraft:cat_sound_variant": (
        (
            "minecraft:classic",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.cat.ambient",
                    "beg_for_food_sound": "minecraft:entity.cat.beg_for_food",
                    "death_sound": "minecraft:entity.cat.death",
                    "eat_sound": "minecraft:entity.cat.eat",
                    "hiss_sound": "minecraft:entity.cat.hiss",
                    "hurt_sound": "minecraft:entity.cat.hurt",
                    "purr_sound": "minecraft:entity.cat.purr",
                    "purreow_sound": "minecraft:entity.cat.purreow",
                    "stray_ambient_sound": "minecraft:entity.cat.stray_ambient",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_cat.ambient",
                    "beg_for_food_sound": "minecraft:entity.baby_cat.beg_for_food",
                    "death_sound": "minecraft:entity.baby_cat.death",
                    "eat_sound": "minecraft:entity.baby_cat.eat",
                    "hiss_sound": "minecraft:entity.baby_cat.hiss",
                    "hurt_sound": "minecraft:entity.baby_cat.hurt",
                    "purr_sound": "minecraft:entity.baby_cat.purr",
                    "purreow_sound": "minecraft:entity.baby_cat.purreow",
                    "stray_ambient_sound": "minecraft:entity.baby_cat.stray_ambient",
                },
            },
        ),
        (
            "minecraft:royal",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.cat_royal.ambient",
                    "beg_for_food_sound": "minecraft:entity.cat_royal.beg_for_food",
                    "death_sound": "minecraft:entity.cat_royal.death",
                    "eat_sound": "minecraft:entity.cat_royal.eat",
                    "hiss_sound": "minecraft:entity.cat_royal.hiss",
                    "hurt_sound": "minecraft:entity.cat_royal.hurt",
                    "purr_sound": "minecraft:entity.cat_royal.purr",
                    "purreow_sound": "minecraft:entity.cat_royal.purreow",
                    "stray_ambient_sound": "minecraft:entity.cat_royal.stray_ambient",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_cat.ambient",
                    "beg_for_food_sound": "minecraft:entity.baby_cat.beg_for_food",
                    "death_sound": "minecraft:entity.baby_cat.death",
                    "eat_sound": "minecraft:entity.baby_cat.eat",
                    "hiss_sound": "minecraft:entity.baby_cat.hiss",
                    "hurt_sound": "minecraft:entity.baby_cat.hurt",
                    "purr_sound": "minecraft:entity.baby_cat.purr",
                    "purreow_sound": "minecraft:entity.baby_cat.purreow",
                    "stray_ambient_sound": "minecraft:entity.baby_cat.stray_ambient",
                },
            },
        ),
    ),
    "minecraft:cat_variant": (
        (
            "minecraft:all_black",
            {
                "asset_id": "minecraft:entity/cat/cat_all_black",
                "baby_asset_id": "minecraft:entity/cat/cat_all_black_baby",
                "spawn_conditions": [
                    {
                        "condition": {
                            "structures": "#minecraft:cats_spawn_as_black",
                            "type": "minecraft:structure",
                        },
                        "priority": 1,
                    },
                    {
                        "condition": {
                            "range": {"min": 0.9},
                            "type": "minecraft:moon_brightness",
                        },
                        "priority": 0,
                    },
                ],
            },
        ),
        (
            "minecraft:black",
            {
                "asset_id": "minecraft:entity/cat/cat_black",
                "baby_asset_id": "minecraft:entity/cat/cat_black_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:british_shorthair",
            {
                "asset_id": "minecraft:entity/cat/cat_british_shorthair",
                "baby_asset_id": "minecraft:entity/cat/cat_british_shorthair_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:calico",
            {
                "asset_id": "minecraft:entity/cat/cat_calico",
                "baby_asset_id": "minecraft:entity/cat/cat_calico_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:jellie",
            {
                "asset_id": "minecraft:entity/cat/cat_jellie",
                "baby_asset_id": "minecraft:entity/cat/cat_jellie_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:persian",
            {
                "asset_id": "minecraft:entity/cat/cat_persian",
                "baby_asset_id": "minecraft:entity/cat/cat_persian_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:ragdoll",
            {
                "asset_id": "minecraft:entity/cat/cat_ragdoll",
                "baby_asset_id": "minecraft:entity/cat/cat_ragdoll_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:red",
            {
                "asset_id": "minecraft:entity/cat/cat_red",
                "baby_asset_id": "minecraft:entity/cat/cat_red_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:siamese",
            {
                "asset_id": "minecraft:entity/cat/cat_siamese",
                "baby_asset_id": "minecraft:entity/cat/cat_siamese_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:tabby",
            {
                "asset_id": "minecraft:entity/cat/cat_tabby",
                "baby_asset_id": "minecraft:entity/cat/cat_tabby_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:white",
            {
                "asset_id": "minecraft:entity/cat/cat_white",
                "baby_asset_id": "minecraft:entity/cat/cat_white_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
    ),
    "minecraft:chicken_sound_variant": (
        (
            "minecraft:classic",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.chicken.ambient",
                    "death_sound": "minecraft:entity.chicken.death",
                    "hurt_sound": "minecraft:entity.chicken.hurt",
                    "step_sound": "minecraft:entity.chicken.step",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_chicken.ambient",
                    "death_sound": "minecraft:entity.baby_chicken.death",
                    "hurt_sound": "minecraft:entity.baby_chicken.hurt",
                    "step_sound": "minecraft:entity.baby_chicken.step",
                },
            },
        ),
        (
            "minecraft:picky",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.chicken_picky.ambient",
                    "death_sound": "minecraft:entity.chicken_picky.death",
                    "hurt_sound": "minecraft:entity.chicken_picky.hurt",
                    "step_sound": "minecraft:entity.chicken.step",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_chicken.ambient",
                    "death_sound": "minecraft:entity.baby_chicken.death",
                    "hurt_sound": "minecraft:entity.baby_chicken.hurt",
                    "step_sound": "minecraft:entity.baby_chicken.step",
                },
            },
        ),
    ),
    "minecraft:chicken_variant": (
        (
            "minecraft:cold",
            {
                "asset_id": "minecraft:entity/chicken/chicken_cold",
                "baby_asset_id": "minecraft:entity/chicken/chicken_cold_baby",
                "model": "cold",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_cold_variant_farm_animals",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:temperate",
            {
                "asset_id": "minecraft:entity/chicken/chicken_temperate",
                "baby_asset_id": "minecraft:entity/chicken/chicken_temperate_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:warm",
            {
                "asset_id": "minecraft:entity/chicken/chicken_warm",
                "baby_asset_id": "minecraft:entity/chicken/chicken_warm_baby",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_warm_variant_farm_animals",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
    ),
    "minecraft:cow_sound_variant": (
        (
            "minecraft:classic",
            {
                "ambient_sound": "minecraft:entity.cow.ambient",
                "death_sound": "minecraft:entity.cow.death",
                "hurt_sound": "minecraft:entity.cow.hurt",
                "step_sound": "minecraft:entity.cow.step",
            },
        ),
        (
            "minecraft:moody",
            {
                "ambient_sound": "minecraft:entity.cow_moody.ambient",
                "death_sound": "minecraft:entity.cow_moody.death",
                "hurt_sound": "minecraft:entity.cow_moody.hurt",
                "step_sound": "minecraft:entity.cow_moody.step",
            },
        ),
    ),
    "minecraft:cow_variant": (
        (
            "minecraft:cold",
            {
                "asset_id": "minecraft:entity/cow/cow_cold",
                "baby_asset_id": "minecraft:entity/cow/cow_cold_baby",
                "model": "cold",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_cold_variant_farm_animals",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:temperate",
            {
                "asset_id": "minecraft:entity/cow/cow_temperate",
                "baby_asset_id": "minecraft:entity/cow/cow_temperate_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:warm",
            {
                "asset_id": "minecraft:entity/cow/cow_warm",
                "baby_asset_id": "minecraft:entity/cow/cow_warm_baby",
                "model": "warm",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_warm_variant_farm_animals",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
    ),
    "minecraft:frog_variant": (
        (
            "minecraft:cold",
            {
                "asset_id": "minecraft:entity/frog/frog_cold",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_cold_variant_frogs",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:temperate",
            {
                "asset_id": "minecraft:entity/frog/frog_temperate",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:warm",
            {
                "asset_id": "minecraft:entity/frog/frog_warm",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_warm_variant_frogs",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
    ),
    "minecraft:pig_sound_variant": (
        (
            "minecraft:big",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.pig_big.ambient",
                    "death_sound": "minecraft:entity.pig_big.death",
                    "eat_sound": "minecraft:entity.pig_big.eat",
                    "hurt_sound": "minecraft:entity.pig_big.hurt",
                    "step_sound": "minecraft:entity.pig.step",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_pig.ambient",
                    "death_sound": "minecraft:entity.baby_pig.death",
                    "eat_sound": "minecraft:entity.baby_pig.eat",
                    "hurt_sound": "minecraft:entity.baby_pig.hurt",
                    "step_sound": "minecraft:entity.baby_pig.step",
                },
            },
        ),
        (
            "minecraft:classic",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.pig.ambient",
                    "death_sound": "minecraft:entity.pig.death",
                    "eat_sound": "minecraft:entity.pig.eat",
                    "hurt_sound": "minecraft:entity.pig.hurt",
                    "step_sound": "minecraft:entity.pig.step",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_pig.ambient",
                    "death_sound": "minecraft:entity.baby_pig.death",
                    "eat_sound": "minecraft:entity.baby_pig.eat",
                    "hurt_sound": "minecraft:entity.baby_pig.hurt",
                    "step_sound": "minecraft:entity.baby_pig.step",
                },
            },
        ),
        (
            "minecraft:mini",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.pig_mini.ambient",
                    "death_sound": "minecraft:entity.pig_mini.death",
                    "eat_sound": "minecraft:entity.pig_mini.eat",
                    "hurt_sound": "minecraft:entity.pig_mini.hurt",
                    "step_sound": "minecraft:entity.pig.step",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_pig.ambient",
                    "death_sound": "minecraft:entity.baby_pig.death",
                    "eat_sound": "minecraft:entity.baby_pig.eat",
                    "hurt_sound": "minecraft:entity.baby_pig.hurt",
                    "step_sound": "minecraft:entity.baby_pig.step",
                },
            },
        ),
    ),
    "minecraft:pig_variant": (
        (
            "minecraft:cold",
            {
                "asset_id": "minecraft:entity/pig/pig_cold",
                "baby_asset_id": "minecraft:entity/pig/pig_cold_baby",
                "model": "cold",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_cold_variant_farm_animals",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:temperate",
            {
                "asset_id": "minecraft:entity/pig/pig_temperate",
                "baby_asset_id": "minecraft:entity/pig/pig_temperate_baby",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:warm",
            {
                "asset_id": "minecraft:entity/pig/pig_warm",
                "baby_asset_id": "minecraft:entity/pig/pig_warm_baby",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_warm_variant_farm_animals",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
    ),
    "minecraft:wolf_sound_variant": (
        (
            "minecraft:angry",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.wolf_angry.ambient",
                    "death_sound": "minecraft:entity.wolf_angry.death",
                    "growl_sound": "minecraft:entity.wolf_angry.growl",
                    "hurt_sound": "minecraft:entity.wolf_angry.hurt",
                    "pant_sound": "minecraft:entity.wolf_angry.pant",
                    "step_sound": "minecraft:entity.wolf.step",
                    "whine_sound": "minecraft:entity.wolf_angry.whine",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                    "death_sound": "minecraft:entity.baby_wolf.death",
                    "growl_sound": "minecraft:entity.baby_wolf.growl",
                    "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                    "pant_sound": "minecraft:entity.baby_wolf.pant",
                    "step_sound": "minecraft:entity.baby_wolf.step",
                    "whine_sound": "minecraft:entity.baby_wolf.whine",
                },
            },
        ),
        (
            "minecraft:big",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.wolf_big.ambient",
                    "death_sound": "minecraft:entity.wolf_big.death",
                    "growl_sound": "minecraft:entity.wolf_big.growl",
                    "hurt_sound": "minecraft:entity.wolf_big.hurt",
                    "pant_sound": "minecraft:entity.wolf_big.pant",
                    "step_sound": "minecraft:entity.wolf.step",
                    "whine_sound": "minecraft:entity.wolf_big.whine",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                    "death_sound": "minecraft:entity.baby_wolf.death",
                    "growl_sound": "minecraft:entity.baby_wolf.growl",
                    "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                    "pant_sound": "minecraft:entity.baby_wolf.pant",
                    "step_sound": "minecraft:entity.baby_wolf.step",
                    "whine_sound": "minecraft:entity.baby_wolf.whine",
                },
            },
        ),
        (
            "minecraft:classic",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.wolf.ambient",
                    "death_sound": "minecraft:entity.wolf.death",
                    "growl_sound": "minecraft:entity.wolf.growl",
                    "hurt_sound": "minecraft:entity.wolf.hurt",
                    "pant_sound": "minecraft:entity.wolf.pant",
                    "step_sound": "minecraft:entity.wolf.step",
                    "whine_sound": "minecraft:entity.wolf.whine",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                    "death_sound": "minecraft:entity.baby_wolf.death",
                    "growl_sound": "minecraft:entity.baby_wolf.growl",
                    "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                    "pant_sound": "minecraft:entity.baby_wolf.pant",
                    "step_sound": "minecraft:entity.baby_wolf.step",
                    "whine_sound": "minecraft:entity.baby_wolf.whine",
                },
            },
        ),
        (
            "minecraft:cute",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.wolf_cute.ambient",
                    "death_sound": "minecraft:entity.wolf_cute.death",
                    "growl_sound": "minecraft:entity.wolf_cute.growl",
                    "hurt_sound": "minecraft:entity.wolf_cute.hurt",
                    "pant_sound": "minecraft:entity.wolf_cute.pant",
                    "step_sound": "minecraft:entity.wolf.step",
                    "whine_sound": "minecraft:entity.wolf_cute.whine",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                    "death_sound": "minecraft:entity.baby_wolf.death",
                    "growl_sound": "minecraft:entity.baby_wolf.growl",
                    "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                    "pant_sound": "minecraft:entity.baby_wolf.pant",
                    "step_sound": "minecraft:entity.baby_wolf.step",
                    "whine_sound": "minecraft:entity.baby_wolf.whine",
                },
            },
        ),
        (
            "minecraft:grumpy",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.wolf_grumpy.ambient",
                    "death_sound": "minecraft:entity.wolf_grumpy.death",
                    "growl_sound": "minecraft:entity.wolf_grumpy.growl",
                    "hurt_sound": "minecraft:entity.wolf_grumpy.hurt",
                    "pant_sound": "minecraft:entity.wolf_grumpy.pant",
                    "step_sound": "minecraft:entity.wolf.step",
                    "whine_sound": "minecraft:entity.wolf_grumpy.whine",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                    "death_sound": "minecraft:entity.baby_wolf.death",
                    "growl_sound": "minecraft:entity.baby_wolf.growl",
                    "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                    "pant_sound": "minecraft:entity.baby_wolf.pant",
                    "step_sound": "minecraft:entity.baby_wolf.step",
                    "whine_sound": "minecraft:entity.baby_wolf.whine",
                },
            },
        ),
        (
            "minecraft:puglin",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.wolf_puglin.ambient",
                    "death_sound": "minecraft:entity.wolf_puglin.death",
                    "growl_sound": "minecraft:entity.wolf_puglin.growl",
                    "hurt_sound": "minecraft:entity.wolf_puglin.hurt",
                    "pant_sound": "minecraft:entity.wolf_puglin.pant",
                    "step_sound": "minecraft:entity.wolf.step",
                    "whine_sound": "minecraft:entity.wolf_puglin.whine",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                    "death_sound": "minecraft:entity.baby_wolf.death",
                    "growl_sound": "minecraft:entity.baby_wolf.growl",
                    "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                    "pant_sound": "minecraft:entity.baby_wolf.pant",
                    "step_sound": "minecraft:entity.baby_wolf.step",
                    "whine_sound": "minecraft:entity.baby_wolf.whine",
                },
            },
        ),
        (
            "minecraft:sad",
            {
                "adult_sounds": {
                    "ambient_sound": "minecraft:entity.wolf_sad.ambient",
                    "death_sound": "minecraft:entity.wolf_sad.death",
                    "growl_sound": "minecraft:entity.wolf_sad.growl",
                    "hurt_sound": "minecraft:entity.wolf_sad.hurt",
                    "pant_sound": "minecraft:entity.wolf_sad.pant",
                    "step_sound": "minecraft:entity.wolf.step",
                    "whine_sound": "minecraft:entity.wolf_sad.whine",
                },
                "baby_sounds": {
                    "ambient_sound": "minecraft:entity.baby_wolf.ambient",
                    "death_sound": "minecraft:entity.baby_wolf.death",
                    "growl_sound": "minecraft:entity.baby_wolf.growl",
                    "hurt_sound": "minecraft:entity.baby_wolf.hurt",
                    "pant_sound": "minecraft:entity.baby_wolf.pant",
                    "step_sound": "minecraft:entity.baby_wolf.step",
                    "whine_sound": "minecraft:entity.baby_wolf.whine",
                },
            },
        ),
    ),
    "minecraft:wolf_variant": (
        (
            "minecraft:ashen",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_ashen_angry",
                    "tame": "minecraft:entity/wolf/wolf_ashen_tame",
                    "wild": "minecraft:entity/wolf/wolf_ashen",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_ashen_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_ashen_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_ashen_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "minecraft:snowy_taiga",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:black",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_black_angry",
                    "tame": "minecraft:entity/wolf/wolf_black_tame",
                    "wild": "minecraft:entity/wolf/wolf_black",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_black_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_black_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_black_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "minecraft:old_growth_pine_taiga",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:chestnut",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_chestnut_angry",
                    "tame": "minecraft:entity/wolf/wolf_chestnut_tame",
                    "wild": "minecraft:entity/wolf/wolf_chestnut",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_chestnut_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_chestnut_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_chestnut_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "minecraft:old_growth_spruce_taiga",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:pale",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_angry",
                    "tame": "minecraft:entity/wolf/wolf_tame",
                    "wild": "minecraft:entity/wolf/wolf",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_baby",
                },
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:rusty",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_rusty_angry",
                    "tame": "minecraft:entity/wolf/wolf_rusty_tame",
                    "wild": "minecraft:entity/wolf/wolf_rusty",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_rusty_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_rusty_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_rusty_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:is_jungle",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:snowy",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_snowy_angry",
                    "tame": "minecraft:entity/wolf/wolf_snowy_tame",
                    "wild": "minecraft:entity/wolf/wolf_snowy",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_snowy_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_snowy_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_snowy_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "minecraft:grove",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:spotted",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_spotted_angry",
                    "tame": "minecraft:entity/wolf/wolf_spotted_tame",
                    "wild": "minecraft:entity/wolf/wolf_spotted",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_spotted_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_spotted_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_spotted_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:is_savanna",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:striped",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_striped_angry",
                    "tame": "minecraft:entity/wolf/wolf_striped_tame",
                    "wild": "minecraft:entity/wolf/wolf_striped",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_striped_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_striped_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_striped_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:is_badlands",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
        (
            "minecraft:woods",
            {
                "assets": {
                    "angry": "minecraft:entity/wolf/wolf_woods_angry",
                    "tame": "minecraft:entity/wolf/wolf_woods_tame",
                    "wild": "minecraft:entity/wolf/wolf_woods",
                },
                "baby_assets": {
                    "angry": "minecraft:entity/wolf/wolf_woods_angry_baby",
                    "tame": "minecraft:entity/wolf/wolf_woods_tame_baby",
                    "wild": "minecraft:entity/wolf/wolf_woods_baby",
                },
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "minecraft:forest",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
    ),
    "minecraft:zombie_nautilus_variant": (
        (
            "minecraft:temperate",
            {
                "asset_id": "minecraft:entity/nautilus/zombie_nautilus",
                "spawn_conditions": [{"priority": 0}],
            },
        ),
        (
            "minecraft:warm",
            {
                "asset_id": "minecraft:entity/nautilus/zombie_nautilus_coral",
                "model": "warm",
                "spawn_conditions": [
                    {
                        "condition": {
                            "biomes": "#minecraft:spawns_coral_variant_zombie_nautilus",
                            "type": "minecraft:biome",
                        },
                        "priority": 1,
                    }
                ],
            },
        ),
    ),
}


TRIM_MATERIAL_DATA: tuple[tuple[str, dict[str, object]], ...] = (
    (
        "minecraft:amethyst",
        {
            "asset_name": "amethyst",
            "description": {
                "color": "#9A5CC6",
                "translate": "trim_material.minecraft.amethyst",
            },
        },
    ),
    (
        "minecraft:copper",
        {
            "asset_name": "copper",
            "description": {
                "color": "#B4684D",
                "translate": "trim_material.minecraft.copper",
            },
            "override_armor_assets": {"minecraft:copper": "copper_darker"},
        },
    ),
    (
        "minecraft:diamond",
        {
            "asset_name": "diamond",
            "description": {
                "color": "#6EECD2",
                "translate": "trim_material.minecraft.diamond",
            },
            "override_armor_assets": {"minecraft:diamond": "diamond_darker"},
        },
    ),
    (
        "minecraft:emerald",
        {
            "asset_name": "emerald",
            "description": {
                "color": "#11A036",
                "translate": "trim_material.minecraft.emerald",
            },
        },
    ),
    (
        "minecraft:gold",
        {
            "asset_name": "gold",
            "description": {
                "color": "#DEB12D",
                "translate": "trim_material.minecraft.gold",
            },
            "override_armor_assets": {"minecraft:gold": "gold_darker"},
        },
    ),
    (
        "minecraft:iron",
        {
            "asset_name": "iron",
            "description": {
                "color": "#ECECEC",
                "translate": "trim_material.minecraft.iron",
            },
            "override_armor_assets": {"minecraft:iron": "iron_darker"},
        },
    ),
    (
        "minecraft:lapis",
        {
            "asset_name": "lapis",
            "description": {
                "color": "#416E97",
                "translate": "trim_material.minecraft.lapis",
            },
        },
    ),
    (
        "minecraft:netherite",
        {
            "asset_name": "netherite",
            "description": {
                "color": "#625859",
                "translate": "trim_material.minecraft.netherite",
            },
            "override_armor_assets": {"minecraft:netherite": "netherite_darker"},
        },
    ),
    (
        "minecraft:quartz",
        {
            "asset_name": "quartz",
            "description": {
                "color": "#E3D4C4",
                "translate": "trim_material.minecraft.quartz",
            },
        },
    ),
    (
        "minecraft:redstone",
        {
            "asset_name": "redstone",
            "description": {
                "color": "#971607",
                "translate": "trim_material.minecraft.redstone",
            },
        },
    ),
    (
        "minecraft:resin",
        {
            "asset_name": "resin",
            "description": {
                "color": "#FC7812",
                "translate": "trim_material.minecraft.resin",
            },
        },
    ),
)

TRIM_PATTERN_DATA: tuple[tuple[str, dict[str, object]], ...] = (
    (
        "minecraft:bolt",
        {
            "asset_id": "minecraft:bolt",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.bolt"},
        },
    ),
    (
        "minecraft:coast",
        {
            "asset_id": "minecraft:coast",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.coast"},
        },
    ),
    (
        "minecraft:dune",
        {
            "asset_id": "minecraft:dune",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.dune"},
        },
    ),
    (
        "minecraft:eye",
        {
            "asset_id": "minecraft:eye",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.eye"},
        },
    ),
    (
        "minecraft:flow",
        {
            "asset_id": "minecraft:flow",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.flow"},
        },
    ),
    (
        "minecraft:host",
        {
            "asset_id": "minecraft:host",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.host"},
        },
    ),
    (
        "minecraft:raiser",
        {
            "asset_id": "minecraft:raiser",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.raiser"},
        },
    ),
    (
        "minecraft:rib",
        {
            "asset_id": "minecraft:rib",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.rib"},
        },
    ),
    (
        "minecraft:sentry",
        {
            "asset_id": "minecraft:sentry",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.sentry"},
        },
    ),
    (
        "minecraft:shaper",
        {
            "asset_id": "minecraft:shaper",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.shaper"},
        },
    ),
    (
        "minecraft:silence",
        {
            "asset_id": "minecraft:silence",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.silence"},
        },
    ),
    (
        "minecraft:snout",
        {
            "asset_id": "minecraft:snout",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.snout"},
        },
    ),
    (
        "minecraft:spire",
        {
            "asset_id": "minecraft:spire",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.spire"},
        },
    ),
    (
        "minecraft:tide",
        {
            "asset_id": "minecraft:tide",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.tide"},
        },
    ),
    (
        "minecraft:vex",
        {
            "asset_id": "minecraft:vex",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.vex"},
        },
    ),
    (
        "minecraft:ward",
        {
            "asset_id": "minecraft:ward",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.ward"},
        },
    ),
    (
        "minecraft:wayfinder",
        {
            "asset_id": "minecraft:wayfinder",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.wayfinder"},
        },
    ),
    (
        "minecraft:wild",
        {
            "asset_id": "minecraft:wild",
            "decal": False,
            "description": {"translate": "trim_pattern.minecraft.wild"},
        },
    ),
)

JUKEBOX_SONG_DATA: tuple[tuple[str, dict[str, object]], ...] = (
    (
        "minecraft:11",
        {
            "comparator_output": 11,
            "description": {"translate": "jukebox_song.minecraft.11"},
            "length_in_seconds": 71.0,
            "sound_event": "minecraft:music_disc.11",
        },
    ),
    (
        "minecraft:13",
        {
            "comparator_output": 1,
            "description": {"translate": "jukebox_song.minecraft.13"},
            "length_in_seconds": 178.0,
            "sound_event": "minecraft:music_disc.13",
        },
    ),
    (
        "minecraft:5",
        {
            "comparator_output": 15,
            "description": {"translate": "jukebox_song.minecraft.5"},
            "length_in_seconds": 178.0,
            "sound_event": "minecraft:music_disc.5",
        },
    ),
    (
        "minecraft:blocks",
        {
            "comparator_output": 3,
            "description": {"translate": "jukebox_song.minecraft.blocks"},
            "length_in_seconds": 345.0,
            "sound_event": "minecraft:music_disc.blocks",
        },
    ),
    (
        "minecraft:bounce",
        {
            "comparator_output": 8,
            "description": {"translate": "jukebox_song.minecraft.bounce"},
            "length_in_seconds": 234.0,
            "sound_event": "minecraft:music_disc.bounce",
        },
    ),
    (
        "minecraft:cat",
        {
            "comparator_output": 2,
            "description": {"translate": "jukebox_song.minecraft.cat"},
            "length_in_seconds": 185.0,
            "sound_event": "minecraft:music_disc.cat",
        },
    ),
    (
        "minecraft:chirp",
        {
            "comparator_output": 4,
            "description": {"translate": "jukebox_song.minecraft.chirp"},
            "length_in_seconds": 185.0,
            "sound_event": "minecraft:music_disc.chirp",
        },
    ),
    (
        "minecraft:creator",
        {
            "comparator_output": 12,
            "description": {"translate": "jukebox_song.minecraft.creator"},
            "length_in_seconds": 176.0,
            "sound_event": "minecraft:music_disc.creator",
        },
    ),
    (
        "minecraft:creator_music_box",
        {
            "comparator_output": 11,
            "description": {"translate": "jukebox_song.minecraft.creator_music_box"},
            "length_in_seconds": 73.0,
            "sound_event": "minecraft:music_disc.creator_music_box",
        },
    ),
    (
        "minecraft:far",
        {
            "comparator_output": 5,
            "description": {"translate": "jukebox_song.minecraft.far"},
            "length_in_seconds": 174.0,
            "sound_event": "minecraft:music_disc.far",
        },
    ),
    (
        "minecraft:lava_chicken",
        {
            "comparator_output": 9,
            "description": {"translate": "jukebox_song.minecraft.lava_chicken"},
            "length_in_seconds": 134.0,
            "sound_event": "minecraft:music_disc.lava_chicken",
        },
    ),
    (
        "minecraft:mall",
        {
            "comparator_output": 6,
            "description": {"translate": "jukebox_song.minecraft.mall"},
            "length_in_seconds": 197.0,
            "sound_event": "minecraft:music_disc.mall",
        },
    ),
    (
        "minecraft:mellohi",
        {
            "comparator_output": 7,
            "description": {"translate": "jukebox_song.minecraft.mellohi"},
            "length_in_seconds": 96.0,
            "sound_event": "minecraft:music_disc.mellohi",
        },
    ),
    (
        "minecraft:otherside",
        {
            "comparator_output": 14,
            "description": {"translate": "jukebox_song.minecraft.otherside"},
            "length_in_seconds": 195.0,
            "sound_event": "minecraft:music_disc.otherside",
        },
    ),
    (
        "minecraft:pigstep",
        {
            "comparator_output": 13,
            "description": {"translate": "jukebox_song.minecraft.pigstep"},
            "length_in_seconds": 149.0,
            "sound_event": "minecraft:music_disc.pigstep",
        },
    ),
    (
        "minecraft:precipice",
        {
            "comparator_output": 13,
            "description": {"translate": "jukebox_song.minecraft.precipice"},
            "length_in_seconds": 299.0,
            "sound_event": "minecraft:music_disc.precipice",
        },
    ),
    (
        "minecraft:relic",
        {
            "comparator_output": 14,
            "description": {"translate": "jukebox_song.minecraft.relic"},
            "length_in_seconds": 218.0,
            "sound_event": "minecraft:music_disc.relic",
        },
    ),
    (
        "minecraft:stal",
        {
            "comparator_output": 8,
            "description": {"translate": "jukebox_song.minecraft.stal"},
            "length_in_seconds": 150.0,
            "sound_event": "minecraft:music_disc.stal",
        },
    ),
    (
        "minecraft:strad",
        {
            "comparator_output": 9,
            "description": {"translate": "jukebox_song.minecraft.strad"},
            "length_in_seconds": 188.0,
            "sound_event": "minecraft:music_disc.strad",
        },
    ),
    (
        "minecraft:tears",
        {
            "comparator_output": 10,
            "description": {"translate": "jukebox_song.minecraft.tears"},
            "length_in_seconds": 175.0,
            "sound_event": "minecraft:music_disc.tears",
        },
    ),
    (
        "minecraft:wait",
        {
            "comparator_output": 12,
            "description": {"translate": "jukebox_song.minecraft.wait"},
            "length_in_seconds": 238.0,
            "sound_event": "minecraft:music_disc.wait",
        },
    ),
    (
        "minecraft:ward",
        {
            "comparator_output": 10,
            "description": {"translate": "jukebox_song.minecraft.ward"},
            "length_in_seconds": 251.0,
            "sound_event": "minecraft:music_disc.ward",
        },
    ),
)

BANNER_PATTERN_NAMES: tuple[str, ...] = (
    "base",
    "border",
    "bricks",
    "circle",
    "creeper",
    "cross",
    "curly_border",
    "diagonal_left",
    "diagonal_right",
    "diagonal_up_left",
    "diagonal_up_right",
    "flow",
    "flower",
    "globe",
    "gradient",
    "gradient_up",
    "guster",
    "half_horizontal",
    "half_horizontal_bottom",
    "half_vertical",
    "half_vertical_right",
    "mojang",
    "piglin",
    "rhombus",
    "skull",
    "small_stripes",
    "square_bottom_left",
    "square_bottom_right",
    "square_top_left",
    "square_top_right",
    "straight_cross",
    "stripe_bottom",
    "stripe_center",
    "stripe_downleft",
    "stripe_downright",
    "stripe_left",
    "stripe_middle",
    "stripe_right",
    "stripe_top",
    "triangle_bottom",
    "triangle_top",
    "triangles_bottom",
    "triangles_top",
)

BANNER_PATTERN_DATA: tuple[tuple[str, dict[str, object]], ...] = tuple(
    (f"minecraft:{name}", _banner_pattern_value(name))
    for name in BANNER_PATTERN_NAMES
)
BANNER_PATTERN_INDEX_BY_KEY: dict[str, int] = {
    key: index for index, (key, _value) in enumerate(BANNER_PATTERN_DATA)
}
BANNER_PATTERN_TAG_VALUES: dict[str, tuple[str, ...]] = {
    "minecraft:no_item_required": (
        "minecraft:square_bottom_left",
        "minecraft:square_bottom_right",
        "minecraft:square_top_left",
        "minecraft:square_top_right",
        "minecraft:stripe_bottom",
        "minecraft:stripe_top",
        "minecraft:stripe_left",
        "minecraft:stripe_right",
        "minecraft:stripe_center",
        "minecraft:stripe_middle",
        "minecraft:stripe_downright",
        "minecraft:stripe_downleft",
        "minecraft:small_stripes",
        "minecraft:cross",
        "minecraft:straight_cross",
        "minecraft:triangle_bottom",
        "minecraft:triangle_top",
        "minecraft:triangles_bottom",
        "minecraft:triangles_top",
        "minecraft:diagonal_left",
        "minecraft:diagonal_up_right",
        "minecraft:diagonal_up_left",
        "minecraft:diagonal_right",
        "minecraft:circle",
        "minecraft:rhombus",
        "minecraft:half_vertical",
        "minecraft:half_horizontal",
        "minecraft:half_vertical_right",
        "minecraft:half_horizontal_bottom",
        "minecraft:border",
        "minecraft:gradient",
        "minecraft:gradient_up",
    ),
    "minecraft:pattern_item/bordure_indented": ("minecraft:curly_border",),
    "minecraft:pattern_item/creeper": ("minecraft:creeper",),
    "minecraft:pattern_item/field_masoned": ("minecraft:bricks",),
    "minecraft:pattern_item/flow": ("minecraft:flow",),
    "minecraft:pattern_item/flower": ("minecraft:flower",),
    "minecraft:pattern_item/globe": ("minecraft:globe",),
    "minecraft:pattern_item/guster": ("minecraft:guster",),
    "minecraft:pattern_item/mojang": ("minecraft:mojang",),
    "minecraft:pattern_item/piglin": ("minecraft:piglin",),
    "minecraft:pattern_item/skull": ("minecraft:skull",),
}

INSTRUMENT_DATA: tuple[tuple[str, dict[str, object]], ...] = (
    (
        "minecraft:admire_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.admire_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.4",
            "use_duration": 7.0,
        },
    ),
    (
        "minecraft:call_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.call_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.5",
            "use_duration": 7.0,
        },
    ),
    (
        "minecraft:dream_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.dream_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.7",
            "use_duration": 7.0,
        },
    ),
    (
        "minecraft:feel_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.feel_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.3",
            "use_duration": 7.0,
        },
    ),
    (
        "minecraft:ponder_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.ponder_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.0",
            "use_duration": 7.0,
        },
    ),
    (
        "minecraft:seek_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.seek_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.2",
            "use_duration": 7.0,
        },
    ),
    (
        "minecraft:sing_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.sing_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.1",
            "use_duration": 7.0,
        },
    ),
    (
        "minecraft:yearn_goat_horn",
        {
            "description": {"translate": "instrument.minecraft.yearn_goat_horn"},
            "range": 256.0,
            "sound_event": "minecraft:item.goat_horn.sound.6",
            "use_duration": 7.0,
        },
    ),
)
INSTRUMENT_INDEX_BY_KEY = {
    key: index for index, (key, _value) in enumerate(INSTRUMENT_DATA)
}
INSTRUMENT_TAG_VALUES: dict[str, tuple[str, ...]] = {
    "minecraft:goat_horns": (
        "#minecraft:regular_goat_horns",
        "#minecraft:screaming_goat_horns",
    ),
    "minecraft:regular_goat_horns": (
        "minecraft:ponder_goat_horn",
        "minecraft:sing_goat_horn",
        "minecraft:seek_goat_horn",
        "minecraft:feel_goat_horn",
    ),
    "minecraft:screaming_goat_horns": (
        "minecraft:admire_goat_horn",
        "minecraft:call_goat_horn",
        "minecraft:yearn_goat_horn",
        "minecraft:dream_goat_horn",
    ),
}

DAMAGE_TYPE_DATA: tuple[tuple[str, dict[str, object]], ...] = (
    (
        "minecraft:arrow",
        {
            "message_id": "arrow",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:bad_respawn_point",
        {
            "message_id": "badRespawnPoint",
            "scaling": "always",
            "exhaustion": 0.1,
            "death_message_type": "intentional_game_design",
        },
    ),
    (
        "minecraft:cactus",
        {
            "message_id": "cactus",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:campfire",
        {
            "message_id": "inFire",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "burning",
        },
    ),
    (
        "minecraft:cramming",
        {
            "message_id": "cramming",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:dragon_breath",
        {
            "message_id": "dragonBreath",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:drown",
        {
            "message_id": "drown",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
            "effects": "drowning",
        },
    ),
    (
        "minecraft:dry_out",
        {
            "message_id": "dryout",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:ender_pearl",
        {
            "message_id": "fall",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
            "death_message_type": "fall_variants",
        },
    ),
    (
        "minecraft:explosion",
        {"message_id": "explosion", "scaling": "always", "exhaustion": 0.1},
    ),
    (
        "minecraft:fall",
        {
            "message_id": "fall",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
            "death_message_type": "fall_variants",
        },
    ),
    (
        "minecraft:falling_anvil",
        {
            "message_id": "anvil",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:falling_block",
        {
            "message_id": "fallingBlock",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:falling_stalactite",
        {
            "message_id": "fallingStalactite",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:fireball",
        {
            "message_id": "fireball",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "burning",
        },
    ),
    (
        "minecraft:fireworks",
        {
            "message_id": "fireworks",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:fly_into_wall",
        {
            "message_id": "flyIntoWall",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:freeze",
        {
            "message_id": "freeze",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
            "effects": "freezing",
        },
    ),
    (
        "minecraft:generic",
        {
            "message_id": "generic",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:generic_kill",
        {
            "message_id": "genericKill",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:hot_floor",
        {
            "message_id": "hotFloor",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "burning",
        },
    ),
    (
        "minecraft:in_fire",
        {
            "message_id": "inFire",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "burning",
        },
    ),
    (
        "minecraft:in_wall",
        {
            "message_id": "inWall",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:indirect_magic",
        {
            "message_id": "indirectMagic",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:lava",
        {
            "message_id": "lava",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "burning",
        },
    ),
    (
        "minecraft:lightning_bolt",
        {
            "message_id": "lightningBolt",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:mace_smash",
        {
            "message_id": "mace_smash",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:magic",
        {
            "message_id": "magic",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:mob_attack",
        {
            "message_id": "mob",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:mob_attack_no_aggro",
        {
            "message_id": "mob",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:mob_projectile",
        {
            "message_id": "mob",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:on_fire",
        {
            "message_id": "onFire",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
            "effects": "burning",
        },
    ),
    (
        "minecraft:out_of_world",
        {
            "message_id": "outOfWorld",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:outside_border",
        {
            "message_id": "outsideBorder",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:player_attack",
        {
            "message_id": "player",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:player_explosion",
        {
            "message_id": "explosion.player",
            "scaling": "always",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:sonic_boom",
        {"message_id": "sonic_boom", "scaling": "always", "exhaustion": 0.0},
    ),
    (
        "minecraft:spear",
        {
            "message_id": "spear",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:spit",
        {
            "message_id": "mob",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:stalagmite",
        {
            "message_id": "stalagmite",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:starve",
        {
            "message_id": "starve",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:sting",
        {
            "message_id": "sting",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:sulfur_cube_hot",
        {
            "message_id": "sulfurCubeHot",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "burning",
        },
    ),
    (
        "minecraft:sweet_berry_bush",
        {
            "message_id": "sweetBerryBush",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "poking",
        },
    ),
    (
        "minecraft:thorns",
        {
            "message_id": "thorns",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "thorns",
        },
    ),
    (
        "minecraft:thrown",
        {
            "message_id": "thrown",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:trident",
        {
            "message_id": "trident",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:unattributed_fireball",
        {
            "message_id": "onFire",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
            "effects": "burning",
        },
    ),
    (
        "minecraft:wind_charge",
        {
            "message_id": "mob",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
    (
        "minecraft:wither",
        {
            "message_id": "wither",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.0,
        },
    ),
    (
        "minecraft:wither_skull",
        {
            "message_id": "witherSkull",
            "scaling": "when_caused_by_living_non_player",
            "exhaustion": 0.1,
        },
    ),
)

DAMAGE_TYPE_INDEX_BY_KEY = {
    key: index for index, (key, _value) in enumerate(DAMAGE_TYPE_DATA)
}

DAMAGE_TYPE_TAG_VALUES: dict[str, tuple[str, ...]] = {
    "minecraft:always_hurts_ender_dragons": ("#minecraft:is_explosion",),
    "minecraft:always_kills_armor_stands": (
        "minecraft:arrow",
        "minecraft:trident",
        "minecraft:fireball",
        "minecraft:wither_skull",
        "minecraft:wind_charge",
    ),
    "minecraft:always_most_significant_fall": ("minecraft:out_of_world",),
    "minecraft:always_triggers_silverfish": ("minecraft:magic",),
    "minecraft:avoids_guardian_thorns": (
        "minecraft:magic",
        "minecraft:thorns",
        "#minecraft:is_explosion",
    ),
    "minecraft:burn_from_stepping": (
        "minecraft:campfire",
        "minecraft:hot_floor",
        "minecraft:sulfur_cube_hot",
    ),
    "minecraft:burns_armor_stands": ("minecraft:on_fire",),
    "minecraft:bypasses_armor": (
        "minecraft:on_fire",
        "minecraft:in_wall",
        "minecraft:cramming",
        "minecraft:drown",
        "minecraft:fly_into_wall",
        "minecraft:generic",
        "minecraft:wither",
        "minecraft:dragon_breath",
        "minecraft:starve",
        "minecraft:fall",
        "minecraft:ender_pearl",
        "minecraft:freeze",
        "minecraft:stalagmite",
        "minecraft:magic",
        "minecraft:indirect_magic",
        "minecraft:out_of_world",
        "minecraft:generic_kill",
        "minecraft:sonic_boom",
        "minecraft:outside_border",
    ),
    "minecraft:bypasses_effects": ("minecraft:starve",),
    "minecraft:bypasses_enchantments": ("minecraft:sonic_boom",),
    "minecraft:bypasses_invulnerability": (
        "minecraft:out_of_world",
        "minecraft:generic_kill",
    ),
    "minecraft:bypasses_resistance": (
        "minecraft:out_of_world",
        "minecraft:generic_kill",
    ),
    "minecraft:bypasses_shield": (
        "#minecraft:bypasses_armor",
        "minecraft:cactus",
        "minecraft:campfire",
        "minecraft:dry_out",
        "minecraft:falling_anvil",
        "minecraft:falling_stalactite",
        "minecraft:hot_floor",
        "minecraft:sulfur_cube_hot",
        "minecraft:in_fire",
        "minecraft:lava",
        "minecraft:lightning_bolt",
        "minecraft:sweet_berry_bush",
    ),
    "minecraft:bypasses_wolf_armor": (
        "#minecraft:bypasses_invulnerability",
        "minecraft:cramming",
        "minecraft:drown",
        "minecraft:dry_out",
        "minecraft:freeze",
        "minecraft:in_wall",
        "minecraft:indirect_magic",
        "minecraft:magic",
        "minecraft:outside_border",
        "minecraft:starve",
        "minecraft:thorns",
        "minecraft:wither",
    ),
    "minecraft:can_break_armor_stand": (
        "minecraft:player_explosion",
        "#minecraft:is_player_attack",
    ),
    "minecraft:damages_helmet": (
        "minecraft:falling_anvil",
        "minecraft:falling_block",
        "minecraft:falling_stalactite",
    ),
    "minecraft:ignites_armor_stands": (
        "minecraft:in_fire",
        "minecraft:campfire",
    ),
    "minecraft:is_drowning": ("minecraft:drown",),
    "minecraft:is_explosion": (
        "minecraft:fireworks",
        "minecraft:explosion",
        "minecraft:player_explosion",
        "minecraft:bad_respawn_point",
    ),
    "minecraft:is_fall": (
        "minecraft:fall",
        "minecraft:ender_pearl",
        "minecraft:stalagmite",
    ),
    "minecraft:is_fire": (
        "minecraft:in_fire",
        "minecraft:campfire",
        "minecraft:on_fire",
        "minecraft:lava",
        "minecraft:hot_floor",
        "minecraft:sulfur_cube_hot",
        "minecraft:unattributed_fireball",
        "minecraft:fireball",
    ),
    "minecraft:is_freezing": ("minecraft:freeze",),
    "minecraft:is_lightning": ("minecraft:lightning_bolt",),
    "minecraft:is_player_attack": (
        "minecraft:player_attack",
        "minecraft:spear",
        "minecraft:mace_smash",
    ),
    "minecraft:is_projectile": (
        "minecraft:arrow",
        "minecraft:trident",
        "minecraft:mob_projectile",
        "minecraft:unattributed_fireball",
        "minecraft:fireball",
        "minecraft:wither_skull",
        "minecraft:thrown",
        "minecraft:wind_charge",
    ),
    "minecraft:mace_smash": ("minecraft:mace_smash",),
    "minecraft:no_anger": ("minecraft:mob_attack_no_aggro",),
    "minecraft:no_impact": ("minecraft:drown",),
    "minecraft:no_knockback": (
        "minecraft:explosion",
        "minecraft:player_explosion",
        "minecraft:bad_respawn_point",
        "minecraft:in_fire",
        "minecraft:lightning_bolt",
        "minecraft:on_fire",
        "minecraft:lava",
        "minecraft:hot_floor",
        "minecraft:sulfur_cube_hot",
        "minecraft:in_wall",
        "minecraft:cramming",
        "minecraft:drown",
        "minecraft:starve",
        "minecraft:cactus",
        "minecraft:fall",
        "minecraft:ender_pearl",
        "minecraft:fly_into_wall",
        "minecraft:out_of_world",
        "minecraft:generic",
        "minecraft:magic",
        "minecraft:wither",
        "minecraft:dragon_breath",
        "minecraft:dry_out",
        "minecraft:sweet_berry_bush",
        "minecraft:freeze",
        "minecraft:stalagmite",
        "minecraft:outside_border",
        "minecraft:generic_kill",
        "minecraft:campfire",
        "minecraft:spear",
    ),
    "minecraft:panic_causes": (
        "#minecraft:panic_environmental_causes",
        "minecraft:arrow",
        "minecraft:dragon_breath",
        "minecraft:explosion",
        "minecraft:fireball",
        "minecraft:fireworks",
        "minecraft:indirect_magic",
        "minecraft:magic",
        "minecraft:mob_attack",
        "minecraft:mob_projectile",
        "minecraft:player_explosion",
        "minecraft:sonic_boom",
        "minecraft:sting",
        "minecraft:thrown",
        "minecraft:trident",
        "minecraft:unattributed_fireball",
        "minecraft:wind_charge",
        "minecraft:wither",
        "minecraft:wither_skull",
        "#minecraft:is_player_attack",
    ),
    "minecraft:panic_environmental_causes": (
        "minecraft:cactus",
        "minecraft:freeze",
        "minecraft:hot_floor",
        "minecraft:sulfur_cube_hot",
        "minecraft:in_fire",
        "minecraft:lava",
        "minecraft:lightning_bolt",
        "minecraft:on_fire",
    ),
    "minecraft:sulfur_cube_with_block_immune_to": (
        "minecraft:arrow",
        "minecraft:cactus",
        "minecraft:dry_out",
        "minecraft:fall",
        "minecraft:falling_anvil",
        "minecraft:falling_block",
        "minecraft:falling_stalactite",
        "minecraft:freeze",
        "minecraft:mace_smash",
        "minecraft:hot_floor",
        "minecraft:mob_attack",
        "minecraft:mob_attack_no_aggro",
        "minecraft:mob_projectile",
        "minecraft:player_attack",
        "minecraft:spear",
        "minecraft:spit",
        "minecraft:stalagmite",
        "minecraft:sting",
        "minecraft:sulfur_cube_hot",
        "minecraft:sweet_berry_bush",
        "minecraft:thrown",
        "minecraft:trident",
        "minecraft:wind_charge",
        "#minecraft:is_explosion",
    ),
    "minecraft:witch_resistant_to": (
        "minecraft:magic",
        "minecraft:indirect_magic",
        "minecraft:sonic_boom",
        "minecraft:thorns",
    ),
    "minecraft:wither_immune_to": ("minecraft:drown",),
}


def minimal_registries() -> list[dict[str, object]]:
    return [
        *_required_synchronized_registries(),
        {
            "id": "minecraft:trim_material",
            "entries": _registry_entries(TRIM_MATERIAL_DATA),
        },
        {
            "id": "minecraft:trim_pattern",
            "entries": _registry_entries(TRIM_PATTERN_DATA),
        },
        {
            "id": "minecraft:jukebox_song",
            "entries": _registry_entries(JUKEBOX_SONG_DATA),
        },
        {
            "id": "minecraft:banner_pattern",
            "entries": _registry_entries(BANNER_PATTERN_DATA),
        },
        {
            "id": "minecraft:instrument",
            "entries": _registry_entries(INSTRUMENT_DATA),
        },
        {
            "id": "minecraft:dimension_type",
            "entries": [
                {
                    "key": "minecraft:overworld",
                    "value": {
                        "fixed_time": 6000,
                        "has_skylight": True,
                        "has_ceiling": False,
                        "has_ender_dragon_fight": False,
                        "ultrawarm": False,
                        "natural": True,
                        "coordinate_scale": 1.0,
                        "bed_works": True,
                        "respawn_anchor_works": False,
                        "min_y": 0,
                        "height": 384,
                        "logical_height": 384,
                        "infiniburn": "#minecraft:infiniburn_overworld",
                        "effects": "minecraft:overworld",
                        "ambient_light": 0.0,
                        "piglin_safe": False,
                        "has_raids": True,
                        "monster_spawn_light_level": 0,
                        "monster_spawn_block_light_limit": 0,
                    },
                }
            ],
        },
        {
            "id": "minecraft:worldgen/biome",
            "entries": [
                {
                    "key": "minecraft:plains",
                    "value": {
                        "has_precipitation": True,
                        "temperature": 0.8,
                        "downfall": 0.4,
                        "effects": {
                            "sky_color": 7907327,
                            "water_fog_color": 329011,
                            "fog_color": 12638463,
                            "water_color": 4159204,
                        },
                    },
                }
            ],
        },
        {
            "id": "minecraft:chat_type",
            "entries": [
                {
                    "key": "minecraft:chat",
                    "value": {
                        "chat": {
                            "translation_key": "chat.type.text",
                            "parameters": ["sender", "content"],
                        },
                        "narration": {
                            "translation_key": "chat.type.text.narrate",
                            "parameters": ["sender", "content"],
                        },
                    },
                },
                {
                    "key": "minecraft:system",
                    "value": {
                        "chat": {
                            "translation_key": "chat.type.text",
                            "parameters": ["sender", "content"],
                        },
                        "narration": {
                            "translation_key": "chat.type.text.narrate",
                            "parameters": ["sender", "content"],
                        },
                    },
                },
            ],
        },
        {
            "id": "minecraft:damage_type",
            "entries": _registry_entries(DAMAGE_TYPE_DATA),
        },
    ]


def empty_tags() -> list[dict[str, object]]:
    return [
        {
            "tagType": "minecraft:block",
            "tags": [{"tagName": "minecraft:infiniburn_overworld", "entries": []}],
        },
        {"tagType": "minecraft:item", "tags": []},
        {"tagType": "minecraft:fluid", "tags": []},
        {"tagType": "minecraft:entity_type", "tags": []},
        {"tagType": "minecraft:game_event", "tags": []},
        {"tagType": "minecraft:banner_pattern", "tags": _banner_pattern_tag_entries()},
        {"tagType": "minecraft:instrument", "tags": _instrument_tag_entries()},
        {"tagType": "minecraft:damage_type", "tags": _damage_type_tag_entries()},
    ]


def encode_empty_chunk_data(section_count: int = 24) -> bytes:
    writer = Writer()
    for _ in range(section_count):
        writer.write_short(0)
        _write_single_value_palette(writer, 0)
        _write_single_value_palette(writer, VOID_BIOME_ID)
    return writer.to_bytes()


def empty_heightmaps() -> list[dict[str, object]]:
    return [
        {"type": 1, "data": [0] * 37},
        {"type": 4, "data": [0] * 37},
    ]


def empty_light_masks() -> dict[str, list[int] | list[bytes]]:
    # 26 sections + 2 edge entries for sky light. Block light is empty.
    sky_sections = [b"\xff" * 2048 for _ in range(26)]
    return {
        "skyLightMask": [(1 << 26) - 1],
        "blockLightMask": [],
        "emptySkyLightMask": [],
        "emptyBlockLightMask": [(1 << 26) - 1],
        "skyLight": sky_sections,
        "blockLight": [],
    }


def _write_single_value_palette(writer: Writer, value: int) -> None:
    writer.write_unsigned_byte(0)
    writer.write_varint(value)
    writer.write_varint(0)


def _required_synchronized_registries() -> list[dict[str, object]]:
    registries: list[dict[str, object]] = []
    for registry in REQUIRED_SYNCHRONIZED_REGISTRIES:
        registry_id = str(registry["id"])
        if registry_id in VANILLA_SYNCHRONIZED_REGISTRY_OVERRIDES:
            registries.append(
                {
                    "id": registry_id,
                    "entries": _registry_entries(
                        VANILLA_SYNCHRONIZED_REGISTRY_OVERRIDES[registry_id]
                    ),
                }
            )
        else:
            registries.append(registry)
    return registries


def _registry_entries(
    values: tuple[tuple[str, dict[str, object]], ...],
) -> list[dict[str, object]]:
    return [{"key": key, "value": value} for key, value in values]


def _banner_pattern_tag_entries() -> list[dict[str, object]]:
    tags: list[dict[str, object]] = []
    for tag_name, values in BANNER_PATTERN_TAG_VALUES.items():
        entries = [BANNER_PATTERN_INDEX_BY_KEY[value] for value in values]
        tags.append({"tagName": tag_name, "entries": entries})
    return tags


def _instrument_tag_entries() -> list[dict[str, object]]:
    tags: list[dict[str, object]] = []
    for tag_name in INSTRUMENT_TAG_VALUES:
        entries = [
            INSTRUMENT_INDEX_BY_KEY[key] for key in _flatten_instrument_tag_values(tag_name)
        ]
        tags.append({"tagName": tag_name, "entries": entries})
    return tags


def _flatten_instrument_tag_values(
    tag_name: str, seen: tuple[str, ...] = ()
) -> tuple[str, ...]:
    if tag_name in seen:
        chain = " -> ".join((*seen, tag_name))
        raise ValueError(f"cyclic instrument tag reference: {chain}")

    values: list[str] = []
    for value in INSTRUMENT_TAG_VALUES[tag_name]:
        if value.startswith("#"):
            values.extend(_flatten_instrument_tag_values(value[1:], (*seen, tag_name)))
        else:
            values.append(value)

    deduped: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value not in INSTRUMENT_INDEX_BY_KEY:
            raise ValueError(f"unknown instrument in tag {tag_name}: {value}")
        if value not in seen_values:
            deduped.append(value)
            seen_values.add(value)
    return tuple(deduped)


def _damage_type_tag_entries() -> list[dict[str, object]]:
    tags: list[dict[str, object]] = []
    for tag_name in DAMAGE_TYPE_TAG_VALUES:
        entries = [
            DAMAGE_TYPE_INDEX_BY_KEY[key]
            for key in _flatten_damage_type_tag_values(tag_name)
        ]
        tags.append({"tagName": tag_name, "entries": entries})
    return tags


def _flatten_damage_type_tag_values(
    tag_name: str, seen: tuple[str, ...] = ()
) -> tuple[str, ...]:
    if tag_name in seen:
        chain = " -> ".join((*seen, tag_name))
        raise ValueError(f"cyclic damage type tag reference: {chain}")

    values: list[str] = []
    for value in DAMAGE_TYPE_TAG_VALUES[tag_name]:
        if value.startswith("#"):
            values.extend(_flatten_damage_type_tag_values(value[1:], (*seen, tag_name)))
        else:
            values.append(value)

    deduped: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if value not in DAMAGE_TYPE_INDEX_BY_KEY:
            raise ValueError(f"unknown damage type in tag {tag_name}: {value}")
        if value not in seen_values:
            deduped.append(value)
            seen_values.add(value)
    return tuple(deduped)
