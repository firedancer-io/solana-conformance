"""
Tests for FlatBuffers-native fixture regeneration.

Covers:
1. Feature extraction from FlatBuffers fixtures
2. FlatBuffers context building (build_fb_elf_ctx)
3. FlatBuffers effects parsing (parse_fb_elf_effects)
4. Complete FlatBuffers fixture building (build_fb_elf_fixture)
5. Feature set computation (add/remove/rekey)
6. End-to-end regeneration flow with mocked shared library
"""

import tempfile
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture
def sample_features():
    return [100, 200, 300, 400, 500]


@pytest.fixture
def sample_elf_data():
    return b"\x7fELF" + b"\x00" * 100


@pytest.fixture
def sample_effects():
    return {
        "err_code": 0,
        "rodata_hash": bytes(range(8)),
        "text_cnt": 42,
        "text_off": 16,
        "entry_pc": 8,
        "calldests_hash": bytes(range(8, 16)),
    }


def _require_flatbuffers():
    from test_suite.flatbuffers_utils import FLATBUFFERS_AVAILABLE

    if not FLATBUFFERS_AVAILABLE:
        pytest.skip("FlatBuffers not available")


def _build_fb_fixture_bytes(elf_data, features, deploy_checks=True, effects=None):
    """Helper to build a FlatBuffers fixture for testing."""
    from test_suite.flatbuffers_utils import build_fb_elf_fixture

    if effects is None:
        effects = {
            "err_code": 0,
            "rodata_hash": None,
            "text_cnt": 0,
            "text_off": 0,
            "entry_pc": 0,
            "calldests_hash": None,
        }

    return build_fb_elf_fixture(
        "sol_compat_elf_loader_v2", elf_data, features, deploy_checks, effects
    )


class TestExtractFbElfFeatures:
    """Tests for extracting features from a parsed FlatBuffers fixture."""

    def test_extract_features_basic(self, sample_elf_data, sample_features):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            extract_fb_elf_features,
            parse_fb_elf_fixture,
        )

        fb_bytes = _build_fb_fixture_bytes(sample_elf_data, sample_features)
        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        assert fb_fixture is not None

        extracted = extract_fb_elf_features(fb_fixture)
        assert extracted == sample_features

    def test_extract_features_empty(self, sample_elf_data):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            extract_fb_elf_features,
            parse_fb_elf_fixture,
        )

        fb_bytes = _build_fb_fixture_bytes(sample_elf_data, [])
        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        assert fb_fixture is not None

        extracted = extract_fb_elf_features(fb_fixture)
        assert extracted == []

    def test_extract_features_single(self, sample_elf_data):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            extract_fb_elf_features,
            parse_fb_elf_fixture,
        )

        fb_bytes = _build_fb_fixture_bytes(sample_elf_data, [999])
        fb_fixture = parse_fb_elf_fixture(fb_bytes)

        extracted = extract_fb_elf_features(fb_fixture)
        assert extracted == [999]

    def test_extract_features_large_values(self, sample_elf_data):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            extract_fb_elf_features,
            parse_fb_elf_fixture,
        )

        large_features = [2**63 - 1, 2**62, 2**60 + 7]
        fb_bytes = _build_fb_fixture_bytes(sample_elf_data, large_features)
        fb_fixture = parse_fb_elf_fixture(fb_bytes)

        extracted = extract_fb_elf_features(fb_fixture)
        assert extracted == large_features


class TestExtractFbElfCtxFields:
    """Tests for extracting all context fields from a FlatBuffers fixture."""

    def test_extract_ctx_fields(self, sample_elf_data, sample_features):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            extract_fb_elf_ctx_fields,
            parse_fb_elf_fixture,
        )

        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, sample_features, deploy_checks=True
        )
        fb_fixture = parse_fb_elf_fixture(fb_bytes)

        fields = extract_fb_elf_ctx_fields(fb_fixture)
        assert fields["elf_data"] == sample_elf_data
        assert fields["features"] == sample_features
        assert fields["deploy_checks"] is True

    def test_extract_ctx_fields_deploy_checks_false(self, sample_elf_data):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            extract_fb_elf_ctx_fields,
            parse_fb_elf_fixture,
        )

        fb_bytes = _build_fb_fixture_bytes(sample_elf_data, [1, 2], deploy_checks=False)
        fb_fixture = parse_fb_elf_fixture(fb_bytes)

        fields = extract_fb_elf_ctx_fields(fb_fixture)
        assert fields["deploy_checks"] is False


class TestExtractFbElfEntrypoint:
    """Tests for extracting the entrypoint from a FlatBuffers fixture."""

    def test_extract_entrypoint(self, sample_elf_data):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            extract_fb_elf_entrypoint,
            parse_fb_elf_fixture,
        )

        fb_bytes = _build_fb_fixture_bytes(sample_elf_data, [])
        fb_fixture = parse_fb_elf_fixture(fb_bytes)

        entrypoint = extract_fb_elf_entrypoint(fb_fixture)
        assert entrypoint == "sol_compat_elf_loader_v2"


class TestBuildFbElfCtx:
    """Tests for building a standalone FlatBuffers ELFLoaderCtx."""

    def test_build_and_parse_ctx(self, sample_elf_data, sample_features):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import build_fb_elf_ctx
        from org.solana.sealevel.v2.ELFLoaderCtx import ELFLoaderCtx

        ctx_bytes = build_fb_elf_ctx(sample_elf_data, sample_features, True)
        assert isinstance(ctx_bytes, bytes)
        assert len(ctx_bytes) > 0

        ctx = ELFLoaderCtx.GetRootAs(ctx_bytes, 0)
        assert ctx.DeployChecks() is True

        fb_features = ctx.Features()
        assert fb_features is not None
        assert fb_features.FeaturesLength() == len(sample_features)
        for i, expected in enumerate(sample_features):
            assert fb_features.Features(i) == expected

    def test_build_ctx_empty_features(self, sample_elf_data):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import build_fb_elf_ctx
        from org.solana.sealevel.v2.ELFLoaderCtx import ELFLoaderCtx

        ctx_bytes = build_fb_elf_ctx(sample_elf_data, [], False)
        ctx = ELFLoaderCtx.GetRootAs(ctx_bytes, 0)

        assert ctx.DeployChecks() is False
        assert ctx.Features() is not None
        assert ctx.Features().FeaturesLength() == 0

    def test_build_ctx_no_elf_data(self, sample_features):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import build_fb_elf_ctx
        from org.solana.sealevel.v2.ELFLoaderCtx import ELFLoaderCtx

        ctx_bytes = build_fb_elf_ctx(b"", sample_features, True)
        ctx = ELFLoaderCtx.GetRootAs(ctx_bytes, 0)

        assert ctx.ElfDataLength() == 0
        assert ctx.Features().FeaturesLength() == len(sample_features)


class TestParseFbElfEffects:
    """Tests for parsing FlatBuffers ELFLoaderEffects from raw bytes."""

    def _build_effects_bytes(self, effects_dict):
        """Build FlatBuffers ELFLoaderEffects bytes from a dict."""
        import flatbuffers
        from org.solana.sealevel.v2 import ELFLoaderEffects as FB_Effects_mod
        from org.solana.sealevel.v2 import XXHash as FB_XXHash_mod

        builder = flatbuffers.Builder(256)

        rodata_hash = effects_dict.get("rodata_hash")
        calldests_hash = effects_dict.get("calldests_hash")

        FB_Effects_mod.Start(builder)
        FB_Effects_mod.AddErrCode(builder, effects_dict.get("err_code", 0))
        if rodata_hash and len(rodata_hash) >= 8:
            offset = FB_XXHash_mod.CreateXXHash(builder, list(rodata_hash[:8]))
            FB_Effects_mod.AddRodataHash(builder, offset)
        FB_Effects_mod.AddTextCnt(builder, effects_dict.get("text_cnt", 0))
        FB_Effects_mod.AddTextOff(builder, effects_dict.get("text_off", 0))
        FB_Effects_mod.AddEntryPc(builder, effects_dict.get("entry_pc", 0))
        if calldests_hash and len(calldests_hash) >= 8:
            offset = FB_XXHash_mod.CreateXXHash(builder, list(calldests_hash[:8]))
            FB_Effects_mod.AddCalldestsHash(builder, offset)
        effects_offset = FB_Effects_mod.End(builder)

        builder.Finish(effects_offset)
        return bytes(builder.Output())

    def test_parse_effects_basic(self, sample_effects):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import parse_fb_elf_effects

        effects_bytes = self._build_effects_bytes(sample_effects)
        parsed = parse_fb_elf_effects(effects_bytes)

        assert parsed is not None
        assert parsed["err_code"] == sample_effects["err_code"]
        assert parsed["text_cnt"] == sample_effects["text_cnt"]
        assert parsed["text_off"] == sample_effects["text_off"]
        assert parsed["entry_pc"] == sample_effects["entry_pc"]
        assert parsed["rodata_hash"] == sample_effects["rodata_hash"]
        assert parsed["calldests_hash"] == sample_effects["calldests_hash"]

    def test_parse_effects_no_hashes(self):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import parse_fb_elf_effects

        effects = {
            "err_code": 3,
            "text_cnt": 10,
            "text_off": 20,
            "entry_pc": 30,
        }
        effects_bytes = self._build_effects_bytes(effects)
        parsed = parse_fb_elf_effects(effects_bytes)

        assert parsed is not None
        assert parsed["err_code"] == 3
        assert parsed["rodata_hash"] is None
        assert parsed["calldests_hash"] is None

    def test_parse_effects_invalid_bytes(self):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import parse_fb_elf_effects

        result = parse_fb_elf_effects(b"not valid flatbuffers")
        # Should not crash; may return a dict with defaults or None
        assert result is None or isinstance(result, dict)


class TestBuildFbElfFixture:
    """Tests for building a complete FlatBuffers ELFLoaderFixture."""

    def test_build_fixture_roundtrip(
        self, sample_elf_data, sample_features, sample_effects
    ):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            build_fb_elf_fixture,
            parse_fb_elf_fixture,
            extract_fb_elf_features,
            extract_fb_elf_ctx_fields,
            extract_fb_elf_effects_fields,
            extract_fb_elf_entrypoint,
        )

        fb_bytes = build_fb_elf_fixture(
            "sol_compat_elf_loader_v2",
            sample_elf_data,
            sample_features,
            True,
            sample_effects,
        )
        assert isinstance(fb_bytes, bytes)

        fb_fixture = parse_fb_elf_fixture(fb_bytes)
        assert fb_fixture is not None

        assert extract_fb_elf_entrypoint(fb_fixture) == "sol_compat_elf_loader_v2"
        assert extract_fb_elf_features(fb_fixture) == sample_features

        ctx = extract_fb_elf_ctx_fields(fb_fixture)
        assert ctx["elf_data"] == sample_elf_data
        assert ctx["deploy_checks"] is True

        effects = extract_fb_elf_effects_fields(fb_fixture)
        assert effects is not None
        assert effects["err_code"] == sample_effects["err_code"]
        assert effects["text_cnt"] == sample_effects["text_cnt"]
        assert effects["text_off"] == sample_effects["text_off"]
        assert effects["entry_pc"] == sample_effects["entry_pc"]

    def test_build_fixture_no_effects(self, sample_elf_data, sample_features):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            build_fb_elf_fixture,
            parse_fb_elf_fixture,
            extract_fb_elf_effects_fields,
        )

        fb_bytes = build_fb_elf_fixture(
            "sol_compat_elf_loader_v2",
            sample_elf_data,
            sample_features,
            True,
            None,
        )
        fb_fixture = parse_fb_elf_fixture(fb_bytes)

        effects = extract_fb_elf_effects_fields(fb_fixture)
        assert effects is not None
        assert effects["err_code"] == 0
        assert effects["rodata_hash"] is None
        assert effects["text_cnt"] == 0

    def test_build_fixture_with_modified_features(self, sample_elf_data):
        """Verify that building with different features produces the correct output."""
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            build_fb_elf_fixture,
            parse_fb_elf_fixture,
            extract_fb_elf_features,
        )

        original_features = [100, 200, 300]
        modified_features = [100, 300, 400, 500]

        effects = {
            "err_code": 0,
            "rodata_hash": None,
            "text_cnt": 0,
            "text_off": 0,
            "entry_pc": 0,
            "calldests_hash": None,
        }

        fb_original = build_fb_elf_fixture(
            "sol_compat_elf_loader_v2",
            sample_elf_data,
            original_features,
            True,
            effects,
        )
        fb_modified = build_fb_elf_fixture(
            "sol_compat_elf_loader_v2",
            sample_elf_data,
            modified_features,
            True,
            effects,
        )

        parsed_original = parse_fb_elf_fixture(fb_original)
        parsed_modified = parse_fb_elf_fixture(fb_modified)

        assert extract_fb_elf_features(parsed_original) == original_features
        assert extract_fb_elf_features(parsed_modified) == modified_features


class TestComputeNewFeatureSet:
    """Tests for _compute_new_feature_set with add/remove/rekey operations."""

    def _compute(self, original, add=None, remove=None, rekey=None):
        import test_suite.globals as globals

        saved_add = globals.features_to_add
        saved_remove = globals.features_to_remove
        saved_rekey = globals.rekey_features

        try:
            globals.features_to_add = add or set()
            globals.features_to_remove = remove or set()
            globals.rekey_features = rekey or []

            from test_suite.fixture_utils import _compute_new_feature_set

            return _compute_new_feature_set(original)
        finally:
            globals.features_to_add = saved_add
            globals.features_to_remove = saved_remove
            globals.rekey_features = saved_rekey

    def test_no_changes(self):
        result = self._compute([100, 200, 300])
        assert result == [100, 200, 300]

    def test_add_features(self):
        result = self._compute([100, 200], add={300, 400})
        assert result == [100, 200, 300, 400]

    def test_add_duplicate_feature(self):
        result = self._compute([100, 200], add={200, 300})
        assert result == [100, 200, 300]

    def test_remove_features(self):
        result = self._compute([100, 200, 300], remove={200})
        assert result == [100, 300]

    def test_remove_nonexistent_feature(self):
        result = self._compute([100, 200], remove={999})
        assert result == [100, 200]

    def test_rekey_feature(self):
        result = self._compute([100, 200, 300], rekey=[(200, 999)])
        assert result == [100, 300, 999]

    def test_rekey_nonexistent_feature(self):
        result = self._compute([100, 200], rekey=[(999, 888)])
        assert result == [100, 200]

    def test_add_remove_combined(self):
        result = self._compute([100, 200, 300], add={400}, remove={200})
        assert result == [100, 300, 400]

    def test_add_remove_rekey_combined(self):
        result = self._compute(
            [100, 200, 300],
            add={400},
            remove={100},
            rekey=[(300, 999)],
        )
        assert result == [200, 400, 999]

    def test_empty_original(self):
        result = self._compute([], add={100, 200})
        assert result == [100, 200]

    def test_result_is_sorted(self):
        result = self._compute([500, 100, 300], add={50, 999})
        assert result == sorted(result)


class TestRegenerateFbFixture:
    """Tests for the end-to-end FlatBuffers fixture regeneration flow."""

    def _setup_globals(
        self,
        tmp_dir,
        features_to_add=None,
        features_to_remove=None,
        rekey_features=None,
        dry_run=False,
        verbose=False,
    ):
        import test_suite.globals as globals

        globals.output_dir = Path(tmp_dir)
        globals.features_to_add = features_to_add or set()
        globals.features_to_remove = features_to_remove or set()
        globals.rekey_features = rekey_features or []
        globals.regenerate_dry_run = dry_run
        globals.regenerate_verbose = verbose

    def test_regenerate_adds_feature(self, sample_elf_data, sample_effects):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            parse_fb_elf_fixture,
            extract_fb_elf_features,
        )
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        original_features = [100, 200, 300]
        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, original_features, effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            # Build effects bytes for the mock to return
            effects_bytes = self._build_effects_bytes(sample_effects)

            self._setup_globals(tmp_dir, features_to_add={400, 500})
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=effects_bytes,
            ):
                result = _regenerate_fb_fixture(test_file, fb_bytes)

            assert result == 1

            output_file = Path(tmp_dir) / "test.fix"
            assert output_file.exists()

            fb_fixture = parse_fb_elf_fixture(output_file.read_bytes())
            new_features = extract_fb_elf_features(fb_fixture)
            assert new_features == [100, 200, 300, 400, 500]

    def test_regenerate_removes_feature(self, sample_elf_data, sample_effects):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            parse_fb_elf_fixture,
            extract_fb_elf_features,
        )
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        original_features = [100, 200, 300, 400]
        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, original_features, effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            effects_bytes = self._build_effects_bytes(sample_effects)

            self._setup_globals(tmp_dir, features_to_remove={200, 300})
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=effects_bytes,
            ):
                result = _regenerate_fb_fixture(test_file, fb_bytes)

            assert result == 1

            fb_fixture = parse_fb_elf_fixture((Path(tmp_dir) / "test.fix").read_bytes())
            new_features = extract_fb_elf_features(fb_fixture)
            assert new_features == [100, 400]

    def test_regenerate_rekeys_feature(self, sample_elf_data, sample_effects):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            parse_fb_elf_fixture,
            extract_fb_elf_features,
        )
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        original_features = [100, 200, 300]
        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, original_features, effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            effects_bytes = self._build_effects_bytes(sample_effects)

            self._setup_globals(tmp_dir, rekey_features=[(200, 999)])
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=effects_bytes,
            ):
                result = _regenerate_fb_fixture(test_file, fb_bytes)

            assert result == 1

            fb_fixture = parse_fb_elf_fixture((Path(tmp_dir) / "test.fix").read_bytes())
            new_features = extract_fb_elf_features(fb_fixture)
            assert new_features == [100, 300, 999]

    def test_regenerate_add_remove_rekey_combined(
        self, sample_elf_data, sample_effects
    ):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            parse_fb_elf_fixture,
            extract_fb_elf_features,
        )
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        original_features = [100, 200, 300, 400]
        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, original_features, effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            effects_bytes = self._build_effects_bytes(sample_effects)

            self._setup_globals(
                tmp_dir,
                features_to_add={500},
                features_to_remove={200},
                rekey_features=[(400, 888)],
            )
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=effects_bytes,
            ):
                result = _regenerate_fb_fixture(test_file, fb_bytes)

            assert result == 1

            fb_fixture = parse_fb_elf_fixture((Path(tmp_dir) / "test.fix").read_bytes())
            new_features = extract_fb_elf_features(fb_fixture)
            assert new_features == [100, 300, 500, 888]

    def test_regenerate_dry_run(self, sample_elf_data, sample_effects):
        _require_flatbuffers()
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        original_features = [100, 200, 300]
        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, original_features, effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            self._setup_globals(tmp_dir, features_to_add={400}, dry_run=True)
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            result = _regenerate_fb_fixture(test_file, fb_bytes)

            assert result == 1
            # File should be unchanged (dry run)
            assert test_file.read_bytes() == fb_bytes

    def test_regenerate_preserves_elf_data(self, sample_elf_data, sample_effects):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            parse_fb_elf_fixture,
            extract_fb_elf_ctx_fields,
        )
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, [100, 200], effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            effects_bytes = self._build_effects_bytes(sample_effects)

            self._setup_globals(tmp_dir, features_to_add={300})
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=effects_bytes,
            ):
                _regenerate_fb_fixture(test_file, fb_bytes)

            fb_fixture = parse_fb_elf_fixture((Path(tmp_dir) / "test.fix").read_bytes())
            ctx = extract_fb_elf_ctx_fields(fb_fixture)
            assert ctx["elf_data"] == sample_elf_data

    def test_regenerate_preserves_effects(self, sample_elf_data, sample_effects):
        _require_flatbuffers()
        from test_suite.flatbuffers_utils import (
            parse_fb_elf_fixture,
            extract_fb_elf_effects_fields,
        )
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, [100], effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            effects_bytes = self._build_effects_bytes(sample_effects)

            self._setup_globals(tmp_dir, features_to_add={200})
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=effects_bytes,
            ):
                _regenerate_fb_fixture(test_file, fb_bytes)

            fb_fixture = parse_fb_elf_fixture((Path(tmp_dir) / "test.fix").read_bytes())
            effects = extract_fb_elf_effects_fields(fb_fixture)
            assert effects["err_code"] == sample_effects["err_code"]
            assert effects["text_cnt"] == sample_effects["text_cnt"]
            assert effects["text_off"] == sample_effects["text_off"]
            assert effects["entry_pc"] == sample_effects["entry_pc"]

    def test_regenerate_returns_zero_on_execution_failure(
        self, sample_elf_data, sample_effects
    ):
        _require_flatbuffers()
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, [100], effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            self._setup_globals(tmp_dir)
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=None,
            ):
                result = _regenerate_fb_fixture(test_file, fb_bytes)

            assert result == 0

    def test_regenerate_calls_v2_entrypoint(self, sample_elf_data, sample_effects):
        """Verify that the v2 entrypoint is used when calling the shared library."""
        _require_flatbuffers()
        from test_suite.fixture_utils import _regenerate_fb_fixture
        import test_suite.globals as globals

        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, [100], effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            effects_bytes = self._build_effects_bytes(sample_effects)

            self._setup_globals(tmp_dir)
            globals.reference_shared_library = "mock_lib"
            globals.target_libraries = {"mock_lib": mock.MagicMock()}

            with mock.patch(
                "test_suite.fixture_utils.process_target_raw",
                return_value=effects_bytes,
            ) as mock_process:
                _regenerate_fb_fixture(test_file, fb_bytes)

            call_args = mock_process.call_args
            assert call_args[0][0] == "sol_compat_elf_loader_v2"

    def _build_effects_bytes(self, effects_dict):
        """Build FlatBuffers ELFLoaderEffects bytes from a dict."""
        import flatbuffers
        from org.solana.sealevel.v2 import ELFLoaderEffects as FB_Effects_mod
        from org.solana.sealevel.v2 import XXHash as FB_XXHash_mod

        builder = flatbuffers.Builder(256)

        rodata_hash = effects_dict.get("rodata_hash")
        calldests_hash = effects_dict.get("calldests_hash")

        FB_Effects_mod.Start(builder)
        FB_Effects_mod.AddErrCode(builder, effects_dict.get("err_code", 0))
        if rodata_hash and len(rodata_hash) >= 8:
            offset = FB_XXHash_mod.CreateXXHash(builder, list(rodata_hash[:8]))
            FB_Effects_mod.AddRodataHash(builder, offset)
        FB_Effects_mod.AddTextCnt(builder, effects_dict.get("text_cnt", 0))
        FB_Effects_mod.AddTextOff(builder, effects_dict.get("text_off", 0))
        FB_Effects_mod.AddEntryPc(builder, effects_dict.get("entry_pc", 0))
        if calldests_hash and len(calldests_hash) >= 8:
            offset = FB_XXHash_mod.CreateXXHash(builder, list(calldests_hash[:8]))
            FB_Effects_mod.AddCalldestsHash(builder, offset)
        effects_offset = FB_Effects_mod.End(builder)

        builder.Finish(effects_offset)
        return bytes(builder.Output())


class TestRegenerateFixtureDispatch:
    """Tests for the regenerate_fixture function's format dispatch logic."""

    def test_flatbuffers_dispatches_to_fb_path(self, sample_elf_data, sample_effects):
        _require_flatbuffers()
        from test_suite.fixture_utils import regenerate_fixture

        fb_bytes = _build_fb_fixture_bytes(
            sample_elf_data, [100, 200], effects=sample_effects
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test.fix"
            test_file.write_bytes(fb_bytes)

            with mock.patch(
                "test_suite.fixture_utils._regenerate_fb_fixture",
                return_value=1,
            ) as mock_fb_regen:
                result = regenerate_fixture(test_file)

            assert result == 1
            mock_fb_regen.assert_called_once()
            call_args = mock_fb_regen.call_args
            assert call_args[0][0] == test_file
            assert call_args[0][1] == fb_bytes

    def test_directory_returns_zero(self):
        from test_suite.fixture_utils import regenerate_fixture

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = regenerate_fixture(Path(tmp_dir))
            assert result == 0
