from ctypes import *
from dataclasses import dataclass, field
import struct
import fd58


@dataclass
class TargetFeaturePool:
    cleaned_up_features: set[int]
    supported_features: set[int]
    union_features: set[int] = field(init=False)

    def __post_init__(self):
        self.union_features = self.cleaned_up_features.union(self.supported_features)


class sol_compat_features_t(Structure):
    _fields_ = [
        ("struct_size", c_uint64),
        ("cleaned_up_features", POINTER(c_uint64)),
        ("cleaned_up_features_count", c_uint64),
        ("supported_features", POINTER(c_uint64)),
        ("supported_features_count", c_uint64),
    ]


def get_sol_compat_features_t(lib: CDLL) -> TargetFeaturePool:
    lib.sol_compat_get_features_v1.argtypes = []
    lib.sol_compat_get_features_v1.restype = POINTER(sol_compat_features_t)

    features_C = lib.sol_compat_get_features_v1().contents
    if features_C.struct_size < 40:
        raise ValueError("sol_compat_get_features_v1 not supported")

    # convert to sets
    return TargetFeaturePool(
        cleaned_up_features=set(
            [
                features_C.cleaned_up_features[i]
                for i in range(features_C.cleaned_up_features_count)
            ]
        ),
        supported_features=set(
            [
                features_C.supported_features[i]
                for i in range(features_C.supported_features_count)
            ]
        ),
    )


def is_featureset_compatible(
    target: TargetFeaturePool, context_features: set[int]
) -> bool:
    """
    Checks the following compatibility criteria:
    - All cleaned up features in target must be in fixture/context's features list
    - All features in fixture/context's list must be in the union of target's cleaned up features and supported features

    Args:
        target: TargetFeaturePool
        context_features: set[int] - features in the fixture/context's FeatureSet
    """
    return target.cleaned_up_features.issubset(
        context_features
    ) and context_features.issubset(target.union_features)


def min_compatible_featureset(
    target: TargetFeaturePool, context_features: set[int]
) -> set[int]:
    """
    Returns the minimum compatible featureset between the target and the fixture/context.
    - Adds all cleaned up features in target to the fixture/context's features set and
    - Drops any features in fixture/context that are not in the union of target's cleaned up and supported features

    Args:
        target: TargetFeaturePool
        context_features: set[int] - features in the fixture/context's FeatureSet

    Returns:
        set[int]: Minimum compatible featureset
    """
    return target.cleaned_up_features.union(context_features).intersection(
        target.union_features
    )


def print_featureset_compatibility_report(
    target: TargetFeaturePool, context_features: set[int]
):
    print("Featureset compatibility report:")
    if target.cleaned_up_features.issubset(context_features):
        print("All cleaned up features are present")
    else:
        print("Missing cleaned up features:")
        print(target.cleaned_up_features.difference(context_features))

    if context_features.issubset(target.union_features):
        print("All features are supported by the target")

    else:
        print("Unsupported features:")
        print(context_features.difference(target.union_features))


def feature_bytes_to_ulong(feature_pubkey: str) -> int:
    return struct.unpack("<Q", fd58.dec32(feature_pubkey.encode())[:8])[0]
