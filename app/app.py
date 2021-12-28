# Copyright (c) 2021 Lucia Pisarenco, Berlin, Germany
from contextlib import contextmanager
from typing import Optional, Tuple
from flask import Flask, request
import sqlite3
import uuid
import datetime
from pathlib import Path

app = Flask(__name__)

DB_LOCATION = "data/bookmarks.db"


@contextmanager
def db_connect():
    try:
        db_file = Path(DB_LOCATION)
        db_file.parent.mkdir(exist_ok=True, parents=True)
        connection = sqlite3.connect(DB_LOCATION)
        cursor = connection.cursor()
        yield connection, cursor

    except:
        connection.rollback()
        raise

    finally:
        connection.commit()
        cursor.close()
        connection.close()


def setup():
    with db_connect() as (conn, curs):
        curs.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (  
                sync_id TEXT PRIMARY KEY, 
                bookmarks TEXT,
                version TEXT,
                last_updated TEXT
            );
        """)


setup()


def get_now() -> str:
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return now


def validate(sync_id: str) -> Optional[Tuple[dict, int]]:
    if sync_id == "":
        return {
            "code": "NotImplementedException",
            "message": "The requested route has not been implemented"
        }, 404
    try:
        int("0x" + sync_id, 16)
    except ValueError:
        return {
            "code": "InvalidSyncIdException",
            "message": "Argument is not a valid UUID string"
        }, 401


@app.route("/bookmarks", methods=["POST"])
def bookmarks_create():
    bookmarks_id = uuid.uuid4().hex
    body = request.json
    if not body.get("version"):
        return {
            "code": "RequiredDataNotFoundException",
            "message": "Unable to find required data"
        }, 400
    version = request.json["version"]
    last_updated = get_now()
    with db_connect() as (conn, curs):
        curs.execute("""
            INSERT INTO bookmarks(sync_id, version, last_updated)
            VALUES(?, ?, ?)
        """, (bookmarks_id, version, last_updated))
    bookmarks = {
        "id": bookmarks_id,
        "lastUpdated": last_updated,
        "version": version
    }
    return bookmarks


@app.route("/bookmarks/<string:sync_id>", methods=["GET"])
def bookmarks_get(sync_id: str):
    validation_error = validate(sync_id)
    if validation_error:
        return validation_error

    with db_connect() as (conn, curs):
        curs.execute("""
            SELECT
                bookmarks,
                version,
                last_updated
            FROM bookmarks
            WHERE sync_id=?;
        """, [sync_id])
        bookmarks_row = curs.fetchone()

    if bookmarks_row is None:
        return {
            "code": "InvalidSyncIdException",
            "message": "Invalid sync ID"
        }, 401

    bookmarks = {
        "bookmarks": bookmarks_row[0],
        "version": bookmarks_row[1],
        "lastUpdated": bookmarks_row[2]
    }

    return bookmarks


@app.route("/bookmarks/<string:sync_id>", methods=["PUT"])
def bookmarks_update(sync_id: str):
    validation_error = validate(sync_id)
    if validation_error:
        return validation_error

    bookmarks = request.json["bookmarks"]
    if bookmarks == "":
        return {
            "code": "RequiredDataNotFoundException",
            "message": "Unable to find required data"
        }, 400
    user_time = request.json["lastUpdated"]

    with db_connect() as (conn, curs):
        curs.execute("""
            SELECT last_updated
            FROM bookmarks
            WHERE sync_id=?;
        """, [sync_id])
        last_updated_row = curs.fetchone()

        if last_updated_row is None:
            return {"error": f"Bookmarks id {sync_id} not found"}, 404

        last_updated = last_updated_row[0]

        if last_updated == user_time:
            now = get_now()
            curs.execute("""
                UPDATE bookmarks 
                SET bookmarks=?, last_updated=?
                WHERE sync_id=?
            """, (bookmarks, now, sync_id))

            return {"lastUpdated": now}
        return {
            "code": "SyncConflictException",
            "message": "A sync conflict was detected"
        }, 409


@app.route("/bookmarks/<string:sync_id>/lastUpdated", methods=["GET"])
def last_updated_get(sync_id: str):
    validation_error = validate(sync_id)
    if validation_error:
        return validation_error

    with db_connect() as (conn, curs):
        curs.execute("""
            SELECT last_updated
            FROM bookmarks
            WHERE sync_id=?;
        """,[sync_id])
        bookmarks_row = curs.fetchone()

    if bookmarks_row is None:
        return {"error": f"Bookmarks id {sync_id} not found"}, 404

    last_updated = {"lastUpdated": bookmarks_row[0]}

    return last_updated


@app.route("/bookmarks/<string:sync_id>/version", methods=["GET"])
def version_get(sync_id: str):
    validation_error = validate(sync_id)
    if validation_error:
        return validation_error
    
    with db_connect() as (conn, curs):
        curs.execute("""
            SELECT version
            FROM bookmarks
            WHERE sync_id=?;
        """,[sync_id])
        bookmarks_row = curs.fetchone()

    if bookmarks_row is None:
        return {"error": f"Bookmarks id {sync_id} not found"}, 404

    version = {"version": bookmarks_row[0]}

    return version


@app.route("/info", methods=["GET"])
def info():
    info = {
        "location": "DE",
        "maxSyncSize": 1048576,
        "message": "Hello World",
        "status": 1,
        "version": "1.1.12"
    }
    return info
