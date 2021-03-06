import pytest
from tests import docker_faf_db_config
import datetime
import random

from replayserver.bookkeeping.database import Database, ReplayDatabaseQueries
from replayserver.errors import BookkeepingError


docker_db_config = {
    "config_db_host": docker_faf_db_config["host"],
    "config_db_port": docker_faf_db_config["port"],
    "config_db_user": docker_faf_db_config["user"],
    "config_db_password": docker_faf_db_config["password"],
    "config_db_name": docker_faf_db_config["db"]
}


# TODO - no tests modifying the db just yet until we set up a db reset fixture
@pytest.mark.asyncio
async def test_database_ok_query():
    db = Database.build(**docker_db_config)

    await db.start()
    result = await db.execute('SELECT * FROM login')
    assert 1 in [r['id'] for r in result]
    await db.stop()


@pytest.mark.asyncio
async def test_database_bad_query():
    db = Database.build(**docker_db_config)

    await db.start()
    with pytest.raises(BookkeepingError):
        await db.execute('SELECT * glablagradargh')
    await db.stop()


@pytest.mark.asyncio
async def test_database_query_at_bad_time():
    db = Database.build(**docker_db_config)

    with pytest.raises(BookkeepingError):
        await db.execute('SELECT * FROM login')
    await db.start()
    await db.stop()
    with pytest.raises(BookkeepingError):
        await db.execute('SELECT * FROM login')


# FIXME - this test pollutes our default db setup. As long as we insert
# out-of-way data and prepare tests for existing data, we should be fine.
@pytest.mark.asyncio
async def test_database_commits_results():
    db = Database.build(**docker_db_config)
    await db.start()
    random.seed()
    randnum = random.randint(1, 100000)
    await db.execute(f"""
        INSERT INTO login (id, login, password, email) VALUES
        (1200, 'commit_test_{randnum}', 'commit_test', 'commit_test')
        ON DUPLICATE KEY UPDATE `login` = 'commit_test_{randnum}'
    """)
    data = await db.execute("SELECT * FROM login WHERE id = 1200")
    assert data
    assert data[0]['login'] == f"commit_test_{randnum}"
    await db.stop()


@pytest.mark.asyncio
async def test_queries_get_teams(mock_database):
    queries = ReplayDatabaseQueries(mock_database)
    await mock_database.add_mock_game((1, 1, 1),
                                      [(1, 1), (2, 2)])
    teams = await queries.get_teams_in_game(1)
    assert teams == {1: ["user1"], 2: ["user2"]}


@pytest.mark.asyncio
async def test_queries_missing_teams(mock_database):
    queries = ReplayDatabaseQueries(mock_database)
    with pytest.raises(BookkeepingError):
        await queries.get_teams_in_game(1)


@pytest.mark.asyncio
async def test_queries_ignore_ai_players(mock_database):
    queries = ReplayDatabaseQueries(mock_database)
    await mock_database.add_mock_game((1, 1, 1),
                                      [(1, 1), (2, 2), (3, 3, 1)])
    teams = await queries.get_teams_in_game(1)
    assert teams == {1: ["user1"], 2: ["user2"]}


@pytest.mark.asyncio
async def test_queries_get_game_stats(mock_database):
    queries = ReplayDatabaseQueries(mock_database)
    await mock_database.add_mock_game((1, 1, 1),
                                      [(1, 1), (2, 2)])
    stats = await queries.get_game_stats(1)
    assert stats == {
        'featured_mod': 'faf',
        'game_type': '0',
        'recorder': 'user1',
        'host': 'user1',
        'launched_at': datetime.datetime(2001, 1, 1, 0, 0).timestamp(),
        'game_end': datetime.datetime(2001, 1, 2, 0, 0).timestamp(),
        'title': 'Name of the game',
        'mapname': 'scmp_1',
        'map_file_path': 'maps/scmp_1.zip',
        'num_players': 2
    }


@pytest.mark.asyncio
async def test_queries_missing_game_stats(mock_database):
    queries = ReplayDatabaseQueries(mock_database)
    with pytest.raises(BookkeepingError):
        await queries.get_game_stats(1)


@pytest.mark.asyncio
async def test_queries_null_game_end(mock_database):
    queries = ReplayDatabaseQueries(mock_database)
    stats = await queries.get_game_stats(101)   # Game with no end time
    assert type(stats['game_end']) is float


@pytest.mark.asyncio
async def test_queries_get_mod_versions(mock_database):
    queries = ReplayDatabaseQueries(mock_database)
    mod = await queries.get_mod_versions("faf")
    assert mod == {
        '1': 1,
        '2': 1,
        '3': 1,
        '4': 1,
        '5': 1,
        '6': 1,
        '7': 1,
        '8': 1,
        '9': 1,
        '10': 1,
    }
