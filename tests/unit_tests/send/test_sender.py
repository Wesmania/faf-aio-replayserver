import pytest
import asyncio
import asynctest
from asynctest.helpers import exhaust_callbacks
from tests import timeout

from replayserver.send.sender import Sender
from replayserver.errors import MalformedDataError, \
    CannotAcceptConnectionError


@pytest.mark.asyncio
@timeout(0.1)
async def test_sender_doesnt_end_while_connection_runs(
        mock_connections, outside_source_stream, locked_mock_coroutines,
        mock_replay_headers, event_loop):
    mock_header = mock_replay_headers()
    connection = mock_connections()
    outside_source_stream.feed_data(b"aaaaa")
    outside_source_stream.set_header(mock_header)
    end, coro = locked_mock_coroutines()
    connection.write.side_effect = coro

    sender = Sender(outside_source_stream)
    h = asyncio.ensure_future(sender.handle_connection(connection))
    w = asyncio.ensure_future(sender.wait_for_ended())
    await exhaust_callbacks(event_loop)
    outside_source_stream.finish()
    await exhaust_callbacks(event_loop)
    assert not w.done()
    end.set()
    await h
    await w


@pytest.mark.asyncio
@timeout(0.1)
async def test_sender_ends_with_ended_stream_and_no_connections(
        outside_source_stream):
    sender = Sender(outside_source_stream)
    outside_source_stream.finish()
    await sender.wait_for_ended()


@pytest.mark.asyncio
@timeout(0.1)
async def test_sender_refuses_connection_after_stream_ends(
        mock_connections, outside_source_stream, event_loop):
    connection = mock_connections()
    sender = Sender(outside_source_stream)
    outside_source_stream.finish()
    with pytest.raises(CannotAcceptConnectionError):
        await sender.handle_connection(connection)
    await sender.wait_for_ended()


@pytest.mark.asyncio
@timeout(0.1)
async def test_sender_no_header(mock_connections, outside_source_stream,
                                event_loop):
    connection = mock_connections()
    sender = Sender(outside_source_stream)
    f = asyncio.ensure_future(sender.handle_connection(connection))
    await exhaust_callbacks(event_loop)
    outside_source_stream.finish()
    with pytest.raises(MalformedDataError):
        await f

    connection.write.assert_not_called()
    await sender.wait_for_ended()


@pytest.mark.asyncio
@timeout(0.1)
async def test_sender_connection_calls(mock_connections, outside_source_stream,
                                       mock_replay_headers, event_loop):
    mock_header = mock_replay_headers()
    connection = mock_connections()
    mock_header.data = b"Header"
    sender = Sender(outside_source_stream)
    outside_source_stream.set_header(mock_header)
    outside_source_stream.feed_data(b"Data")
    f = asyncio.ensure_future(sender.handle_connection(connection))
    await exhaust_callbacks(event_loop)
    outside_source_stream.finish()
    await f
    connection.write.assert_has_awaits([asynctest.call(b"Header"),
                                        asynctest.call(b"Data")])
    await sender.wait_for_ended()
