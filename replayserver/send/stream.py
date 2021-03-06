import asyncio
from replayserver.stream import ReplayStream, DataEventMixin, EndedEventMixin
from replayserver.send.timestamp import Timestamp


class DelayedReplayStream(DataEventMixin, EndedEventMixin, ReplayStream):
    def __init__(self, stream, timestamp):
        DataEventMixin.__init__(self)
        EndedEventMixin.__init__(self)
        ReplayStream.__init__(self)
        self._stream = stream
        self._timestamp = timestamp
        self._current_position = 0
        asyncio.ensure_future(self._track_current_position())

    @classmethod
    def build(cls, stream, *, config_sent_replay_position_update_interval,
              config_sent_replay_delay, **kwargs):
        timestamp = Timestamp(stream,
                              config_sent_replay_position_update_interval,
                              config_sent_replay_delay)
        return cls(stream, timestamp)

    @property
    def header(self):
        return self._stream.header

    async def wait_for_header(self):
        h = await self._stream.wait_for_header()
        if h is None:
            # Stream ended without setting the header. Respect the 'wait until
            # header is set or stream ends' rule and wait for our own end.
            await self.wait_for_ended()
        return h

    def _data_length(self):
        return min(len(self._stream.data), self._current_position)

    def _data_slice(self, s):
        if s.stop is None:
            new_stop = self._current_position
        else:
            new_stop = min(s.stop, self._current_position)
        return self._stream.data[slice(s.start, new_stop, s.step)]

    def _data_bytes(self):
        return self._stream.data[:self._current_position]

    async def _track_current_position(self):
        async for position in self._timestamp.timestamps():
            if position <= self._current_position:
                continue
            self._current_position = position
            self._signal_new_data_or_ended()
        self._end()
        self._signal_new_data_or_ended()
