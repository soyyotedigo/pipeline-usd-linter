from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from usd_linter.parser import ParseError, _parse_stage_from_text, parse_stage


class _FakeLayer:
    def ExportToString(self) -> str:
        return '#usda 1.0\ndef Xform "Root" {\n}\n'


class _FakeStage:
    def GetRootLayer(self) -> _FakeLayer:
        return _FakeLayer()


class ParserTests(unittest.TestCase):
    def test_parse_stage_uses_pxr_exported_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset.usdc"
            path.write_bytes(b"binary-content")

            with patch("usd_linter.parser._open_stage_with_pxr", return_value=_FakeStage()):
                stage = parse_stage(path)

        self.assertEqual(stage.path, path.resolve())
        self.assertEqual(len(stage.prims), 1)
        self.assertEqual(stage.prims[0].path, "/Root")

    def test_parse_stage_reads_real_usdc_file_via_pxr(self) -> None:
        from pxr import Usd

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset.usdc"
            stage = Usd.Stage.CreateNew(str(path))
            stage.DefinePrim("/Asset", "Xform")
            stage.GetRootLayer().Save()

            parsed_stage = parse_stage(path)

        self.assertEqual(parsed_stage.path, path.resolve())
        self.assertEqual([prim.path for prim in parsed_stage.prims], ["/Asset"])

    def test_parse_stage_uses_pxr_for_usdz(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset.usdz"
            path.write_bytes(b"PK\x03\x04binary-zip-content")

            with patch("usd_linter.parser._open_stage_with_pxr", return_value=_FakeStage()):
                stage = parse_stage(path)

        self.assertEqual(stage.path, path.resolve())
        self.assertEqual(len(stage.prims), 1)
        self.assertEqual(stage.prims[0].path, "/Root")

    def test_parse_stage_reads_real_usdz_file_via_pxr(self) -> None:
        from pxr import Usd, UsdUtils

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "asset.usda"
            package_path = temp_path / "asset.usdz"

            stage = Usd.Stage.CreateNew(str(source_path))
            stage.DefinePrim("/Asset", "Xform")
            stage.GetRootLayer().Save()
            UsdUtils.CreateNewUsdzPackage(str(source_path), str(package_path))

            parsed_stage = parse_stage(package_path)

        self.assertEqual(parsed_stage.path, package_path.resolve())
        self.assertEqual([prim.path for prim in parsed_stage.prims], ["/Asset"])

    def test_parse_stage_raises_parse_error_when_pxr_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "asset.usda"
            path.write_text('#usda 1.0\ndef Xform "Root" {}\n', encoding="utf-8")

            with patch(
                "usd_linter.parser._open_stage_with_pxr",
                side_effect=ParseError("usd-core is required."),
            ):
                with self.assertRaises(ParseError):
                    parse_stage(path)

    def test_parse_stage_separates_references_payloads_and_sublayers(self) -> None:
        text = (
            '#usda 1.0\n(\n'
            '    subLayers = [@./layers/look.usda@]\n)\n\n'
            'def Xform "Asset" (\n'
            '    prepend payload = @./payloads/asset_payload.usda@\n)\n'
            '{\n'
            '    def Mesh "Body" (\n'
            '        prepend references = @./refs/materials.usda@\n'
            '    )\n    {\n    }\n}\n'
        )

        stage = _parse_stage_from_text(Path("C:/tmp/asset.usda"), text)

        self.assertEqual([ref.raw_path for ref in stage.sublayers], ["./layers/look.usda"])
        self.assertEqual([ref.raw_path for ref in stage.asset_payloads], ["./payloads/asset_payload.usda"])
        self.assertEqual([ref.raw_path for ref in stage.asset_references], ["./refs/materials.usda"])
