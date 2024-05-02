# Global variables that can be accessed from processes.

# Target libraries (for run-tests)
target_libraries = {}

# Ground truth library (for run-tests)
solana_shared_library = None

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
