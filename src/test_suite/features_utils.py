from ctypes import *
from dataclasses import dataclass, field


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


def get_sol_compat_features_t(lib: CDLL) -> sol_compat_features_t:
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


"""
Compatibility criteria:
- All cleaned up features must be in features
- All features must be in the union of cleaned up features and supported features
"""


def is_featureset_compatible(target: TargetFeaturePool, features: set[int]) -> bool:
    return target.cleaned_up_features.issubset(features) and features.issubset(
        target.union_features
    )


"""
- Adds all cleaned up features to the features set and
- Drops any features that are not in the union of cleaned up and supported features
"""


def min_compatible_featureset(
    target: TargetFeaturePool, features: set[int]
) -> set[int]:
    return target.cleaned_up_features.union(features).intersection(
        target.union_features
    )


def print_featureset_compatibility_report(
    target: TargetFeaturePool, features: set[int]
):
    print("Featureset compatibility report:")
    if target.cleaned_up_features.issubset(features):
        print("All cleaned up features are present")
    else:
        print("Missing cleaned up features:")
        print(target.cleaned_up_features.difference(features))

    if features.issubset(target.union_features):
        print("All features are supported by the target")

    else:
        print("Unsupported features:")
        print(features.difference(target.union_features))
