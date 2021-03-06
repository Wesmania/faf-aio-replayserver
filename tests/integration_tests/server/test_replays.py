from replayserver.server.replays import Replays
from replayserver.receive.mergestrategy import MergeStrategies


config = {
    "config_merger_grace_period_time": 30,
    "config_replay_merge_strategy": MergeStrategies.FOLLOW_STREAM,
    "config_mergestrategy_stall_check_period": 60,
    "config_sent_replay_delay": 5 * 60,
    "config_sent_replay_position_update_interval": 1,
    "config_replay_forced_end_time": 5 * 60 * 60,
}


def test_replays_init(mock_bookkeeper):
    Replays.build(mock_bookkeeper, **config)
