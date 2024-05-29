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

# Harness context
harness_ctx: HarnessCtx = None
