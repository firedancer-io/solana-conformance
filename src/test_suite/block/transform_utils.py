import fd58
import test_suite.block_pb2 as block_pb


def transform_fixture(fixture: block_pb.BlockFixture):
    """
    Example:
    fixture.input.slot_ctx.fee_rate_governor.target_lamports_per_signature = 10000
    fixture.input.slot_ctx.fee_rate_governor.target_signatures_per_slot = 20000
    fixture.input.slot_ctx.fee_rate_governor.min_lamports_per_signature = 5000
    fixture.input.slot_ctx.fee_rate_governor.max_lamports_per_signature = 100000
    fixture.input.slot_ctx.fee_rate_governor.burn_percent = 50
    fixture.input.slot_ctx.parent_signature_count = 0
    """
    pass
