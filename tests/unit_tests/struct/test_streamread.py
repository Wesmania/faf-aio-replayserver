import pytest
from replayserver.struct import streamread


def test_generator_data():
    gen = streamread.GeneratorData()
    cor = gen.more()
    cor.send(None)
    with pytest.raises(StopIteration) as v:
        cor.send(b"foobar")
    assert v.value.value == 6

    assert gen.data == b"foobar"
    assert gen.position == 0

    data = gen.take(4)
    assert data == b"foob"
    assert gen.position == 4
    assert gen.data == b"foobar"

    data = gen.take(2)
    assert data == b"ar"
    assert gen.position == 6
    assert gen.data == b"foobar"


def test_generator_maxlen():
    def do_send(gen, data):
        cor = gen.more()
        cor.send(None)
        try:
            cor.send(data)
        except StopIteration:
            pass

    gen = streamread.GeneratorData(maxlen=8)
    do_send(gen, b"12345678")
    with pytest.raises(ValueError):
        do_send(gen, b"12345678")

    gen = streamread.GeneratorData(maxlen=6)
    do_send(gen, b"12345678")
    with pytest.raises(ValueError):
        do_send(gen, b"12345678")

    gen = streamread.GeneratorData(maxlen=6)
    do_send(gen, b"12345678")
    gen.take(6)
    gen.take(0)
    with pytest.raises(ValueError):
        gen.take(2)

    gen = streamread.GeneratorData(maxlen=6)
    do_send(gen, b"12345678")
    gen.take(5)
    with pytest.raises(ValueError):
        gen.take(2)


# From here on we'll assume Generator{Data,Wrapper} work. A tiny violation of
# unit testing rules, but oh well.
def test_read_exactly():
    gen = streamread.GeneratorData()
    gen.data = b"abcdefgh"
    gen.position = 4
    cor = streamread.read_exactly(gen, 3)
    with pytest.raises(StopIteration) as v:
        cor.send(None)
    assert v.value.value == b"efg"

    gen.data = b"1234"
    gen.position = 3
    cor = streamread.read_exactly(gen, 3)
    cor.send(None)
    cor.send(b"5")
    with pytest.raises(StopIteration) as v:
        cor.send(b"678")
    assert v.value.value == b"456"


def test_read_until():
    gen = streamread.GeneratorData()
    gen.data = b"abcdefgh"
    gen.position = 4
    cor = streamread.read_until(gen, b"g")
    with pytest.raises(StopIteration) as v:
        cor.send(None)
    assert v.value.value == b"efg"

    gen.data = b"aaa"
    gen.position = 0
    cor = streamread.read_until(gen, b"b")
    cor.send(None)
    cor.send(b"aaa")
    cor.send(b"ccc")
    with pytest.raises(StopIteration) as v:
        cor.send(b"dbd")
    assert v.value.value == b"aaaaaacccdb"
