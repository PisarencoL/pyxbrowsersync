# Copyright (c) 2021 Lucia Pisarenco, Berlin, Germany
from app import app
from types import SimpleNamespace

app.DB_LOCATION = "data/test.db"

def test_bookmarks_create_ok(db):
    # Replace HTTP request data, with hardcoded data
    app.request = SimpleNamespace(json = {
        "version": "1.1.12"
    })
    # call actual function we want to test
    result = app.bookmarks_create()
    # Check if we got a valid response
    assert isinstance(result, dict), "Response should be a dict"
    assert "id" in result, "Response is lacking key 'id'"
    assert "lastUpdated" in result, "Response is lacking key 'lastUpdated"
    assert "version" in result, "Response is lacking key 'version'"

    # Check if we also have the data in the DB
    with app.db_connect() as (conn, curs):
        curs.execute("""
            SELECT sync_id FROM bookmarks WHERE sync_id=?
        """, [result["id"]])
        all_rows_from_query = curs.fetchall()
        assert len(all_rows_from_query) == 1, "Should be exactly 1 matching row"


def test_bookmarks_create_failure(db):
    # Let's try an invalid request
    app.request = SimpleNamespace(json = {
        "version1": "1.1.12"
    })
    # Call the function
    result = app.bookmarks_create()
    # Result should be a Tuple this time (failure, with error message as dict, and HTTP code)
    assert isinstance(result, tuple), "Expecting failure result, as a tuple of dict and HTTP error code"
    assert result[1] == 400, "HTTP error code should be 400"
