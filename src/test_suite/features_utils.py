from ctypes import *
from dataclasses import dataclass


@dataclass
class TargetFeatureSet:
    cleaned_up_features: set[int]
    supported_features: set[int]


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

    # convert to sets
    return TargetFeatureSet(
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


def print_features(f: TargetFeatureSet):
    print("cleaned_up_features_count: ", len(f.cleaned_up_features))
    for i in f.cleaned_up_features:
        print(i)

    print("supported_features_count: ", len(f.supported_features))
    for i in f.supported_features:
        print(i)
