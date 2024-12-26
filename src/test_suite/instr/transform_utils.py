import fd58
import test_suite.invoke_pb2 as invoke_pb


def transform_fixture(fixture: invoke_pb.InstrFixture):
    """
    Allows for applying custom transformations to each fixture (mainly the context) before
    rerunning through the harness. For now, this is only used for fixture regeneration.
    As the user, you may modify `fixture` in-place before the fixture context gets run against
    a target and regenerated. To keep this function customizable, the implementation is left
    to the user to decide what they want to do with the data.
    """
    pass
