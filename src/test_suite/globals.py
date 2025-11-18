from test_suite.features_utils import TargetFeaturePool
from test_suite.fuzz_interface import HarnessCtx

# Global variables that can be accessed from processes.

# Target libraries (for run-tests)
target_libraries = {}

# Ground truth library (for run-tests)
reference_shared_library = None

# Number of iterations (for check-consistency)
n_iterations = 0

# Output directory
output_dir = None

# Fill output buffer with random bytes
output_buffer_pointer = None

# A FeaturePool object describing the hardcoded and supported features
# of the target
feature_pool = None

# (For fixtures) Whether to output in human-readable format
readable = False

# (For fixtures) Whether to organize fixtures by program type
organize_fixture_dir = False

# (For fixtures) Whether to only keep passing tests
only_keep_passing = False

# Default harness context
default_harness_ctx: HarnessCtx = None

# Whether to run in consensus mode
consensus_mode: bool = False

# Whether to run in core bpf mode
core_bpf_mode: bool = False

# Whether to run in "ignore compute units" mode
ignore_compute_units_mode: bool = False

# For regenerating fixtures
features_to_add: set[int] = set()
features_to_remove: set[int] = set()
rekey_features: list[tuple[int, ...]] = []
target_features: TargetFeaturePool = None
regenerate_all: bool = False
regenerate_dry_run: bool = False
regenerate_verbose: bool = False

# For download progress tracking (shared across threads)
download_progress_bar = None

# For downloads: whether to download all artifacts or only the latest
download_all_artifacts: bool = False
