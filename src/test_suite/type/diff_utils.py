import test_suite.protos.type_pb2 as type_pb


def diff_type_effects(a: type_pb.TypeEffects, b: type_pb.TypeEffects):
    a_san = type_pb.TypeEffects()
    a_san.CopyFrom(a)
    b_san = type_pb.TypeEffects()
    b_san.CopyFrom(b)

    # We want to ignore the yaml field for the types harness
    a_san.ClearField("yaml")
    b_san.ClearField("yaml")

    return a_san == b_san
