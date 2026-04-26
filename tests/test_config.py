from pathlib import Path
import unittest

from usd_linter.config import ConfigError, load_config


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class LoadConfigTests(unittest.TestCase):
    def test_loads_default_settings_without_config_file(self) -> None:
        config = load_config(FIXTURE_DIR / "valid_asset.usda")

        self.assertEqual(config.output_format, "text")
        self.assertEqual(config.fail_on, "error")
        self.assertTrue(config.enable_references_rule)
        self.assertTrue(config.enable_suspicious_over_rule)
        self.assertTrue(config.enable_name_rule)
        self.assertEqual(config.allowed_root_prims, ("Asset", "Root", "World"))

    def test_cli_arguments_override_config_file_values(self) -> None:
        config = load_config(
            FIXTURE_DIR / "valid_asset.usda",
            config_path=FIXTURE_DIR / "custom_rules.toml",
            output_format="json",
            fail_on="error",
        )

        self.assertEqual(config.output_format, "json")
        self.assertEqual(config.fail_on, "error")
        self.assertEqual(config.allowed_root_prims, ("BadRoot",))
        self.assertEqual(config.required_stage_metadata, ("upAxis",))

    def test_config_only_enables_declared_rules(self) -> None:
        config = load_config(
            FIXTURE_DIR / "valid_asset.usda",
            config_path=FIXTURE_DIR / "selective_rules.toml",
        )

        self.assertFalse(config.enable_name_rule)
        self.assertFalse(config.enable_root_prim_rule)
        self.assertFalse(config.enable_required_metadata_rule)
        self.assertTrue(config.enable_references_rule)
        self.assertFalse(config.enable_suspicious_over_rule)

    def test_legacy_rule_switches_are_rejected_with_clear_error(self) -> None:
        with self.assertRaises(ConfigError):
            load_config(
                FIXTURE_DIR / "valid_asset.usda",
                config_path=FIXTURE_DIR / "legacy_enabled_rules.toml",
            )

    def test_invalid_boolean_rule_flag_raises_config_error(self) -> None:
        with self.assertRaises(ConfigError):
            load_config(
                FIXTURE_DIR / "valid_asset.usda",
                config_path=FIXTURE_DIR / "invalid_boolean_rules.toml",
            )

    def test_invalid_toml_raises_config_error(self) -> None:
        invalid_path = FIXTURE_DIR / "invalid_rules.toml"
        invalid_path.write_text("[rules\nname_pattern = 'oops'", encoding="utf-8")

        try:
            with self.assertRaises(ConfigError):
                load_config(FIXTURE_DIR / "valid_asset.usda", config_path=invalid_path)
        finally:
            invalid_path.unlink(missing_ok=True)

    def test_max_hierarchy_depth_is_loaded_from_config(self) -> None:
        config = load_config(
            FIXTURE_DIR / "deep_hierarchy.usda",
            config_path=FIXTURE_DIR / "max_depth_rules.toml",
        )

        self.assertEqual(config.max_hierarchy_depth, 3)

    def test_performance_budgets_are_loaded_from_config(self) -> None:
        config = load_config(
            FIXTURE_DIR / "valid_composition.usda",
            config_path=FIXTURE_DIR / "performance_rules.toml",
        )

        self.assertEqual(config.max_stage_file_size_bytes, 0)
        self.assertEqual(config.max_prim_count, 0)
        self.assertEqual(config.max_payload_count, 0)
