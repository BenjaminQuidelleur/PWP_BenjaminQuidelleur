import os
import pytest
import tempfile
import time
from datetime import date, time
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

import app
from app import Choreography, Track, Artist, Album

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def db_handle():
    db_fd, db_fname = tempfile.mkstemp()
    app.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.app.config["TESTING"] = True
    
    with app.app.app_context():
        app.db.create_all()
        
    yield app.db
    
    app.db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

def _get_choreography(name="chore"):
    return Choreography(
        name=name,
        description="blablabla",
    )

def _get_track(title="track1"):
    return Track(
        title = title,
        disc_number = 1,
        track_number = 8,
        length = time(0,3,40),
        lyrics = "tttttttttttttttttttt"
    )
    
def _get_album(title="album1"):
    return Album(
        title = title,
        release = date(2021, 11, 12),
        genre = "Rap",
        discs = 1
    )
    
def _get_artist(name="testartist"):
    return Artist(
        name=name,
        unique_name="unique name artist test"
    )
    
def test_create_instances(db_handle):
    """
    Tests that we can create one instance of each model and save them to the
    database using valid values for all columns. After creation, test that 
    everything can be found from database, and that all relationships have been
    saved correctly.
    """

    # Create everything
    choreography = _get_choreography()
    track = _get_track()
    album = _get_album()
    artist = _get_artist()
    track.choreography = choreography
    track.album = album
    album.artist = artist
    artist.albums.append(album)
    db_handle.session.add(choreography)
    db_handle.session.add(track)
    db_handle.session.add(album)
    db_handle.session.add(artist)
    db_handle.session.commit()
    
    # Check that everything exists
    assert Choreography.query.count() == 1
    assert Track.query.count() == 1
    assert Album.query.count() == 1
    assert Artist.query.count() == 1
    db_track = Track.query.first()
    db_album = Album.query.first()
    db_choreography = Choreography.query.first()
    db_artist = Artist.query.first()
    
    # Check all relationships (both sides)

    assert db_track.choreography == db_choreography
    #assert db_choreography.in_track == db_track

    assert db_track.album == db_album
    #assert db_album.tracks == db_track

    #assert db_track.artist == db_artist
    #assert db_artist.tracks == db_track

    assert db_album.artist == db_artist
    #assert db_artist.albums == db_album

    
    
    assert db_track in db_album.tracks
    assert db_track in db_choreography.in_track

    assert db_album in db_artist.albums
    #assert db_album in db_track.album    


def test_updated_choreography(db_handle):
    """
    tests that the choreography name is updated
    """
    choreography = _get_choreography()
    choreography.name = "new name"
    db_handle.session.add(choreography)
    db_handle.session.commit()
    db_choreography = Choreography.query.first()
    assert db_choreography.name == "new name"
    db_handle.session.rollback()


def test_updated_track(db_handle):
    """
    tests that the track title is updated
    """
    choreography = _get_choreography()
    track = _get_track()
    album = _get_album()
    track.album = album
    track.choreography = choreography
    track.title = "updated title"
    db_handle.session.add(track)

    #choreography.name = "new name"
    #db.session.add(choreography)
    db_handle.session.commit()
    db_track = Track.query.first()
    assert db_track.title == "updated title"
    db_handle.session.rollback()

def test_updated_album(db_handle):
    """
    tests that the album title is updated
    """
    
    artist = _get_artist()
    album = _get_album()
    album.artist = artist
    
    album.title = "updated title"
    db_handle.session.add(album)

    #choreography.name = "new name"
    #db.session.add(choreography)
    db_handle.session.commit()
    db_album = Album.query.first()
    assert db_album.title == "updated title"
    db_handle.session.rollback()


def test_updated_artist(db_handle):
    """
    tests that the artist name is updated
    """
    artist = _get_artist()
    artist.name = "new name"
    db_handle.session.add(artist)
    db_handle.session.commit()
    db_artist = Artist.query.first()
    assert db_artist.name == "new name"
    db_handle.session.rollback()


def test_delete_choreography(db_handle):
    """
    tests that the choreography is deleted
    """
    choreography = _get_choreography()
    db_handle.session.add(choreography)
    db_handle.session.commit()
    db_handle.session.delete(choreography)
    assert Choreography.query.count() == 0
    db_handle.session.rollback()


def test_delete_artist(db_handle):
    """
    tests that the choreography is deleted
    """
    artist = _get_artist()
    db_handle.session.add(artist)
    db_handle.session.commit()
    db_handle.session.delete(artist)
    assert Artist.query.count() == 0
    db_handle.session.rollback()


def test_delete_track(db_handle):
    """
    tests that the choreography is deleted
    """
    
    choreography = _get_choreography()
    track = _get_track()
    album = _get_album()
    track.album = album
    track.choreography = choreography
    db_handle.session.add(track)
    db_handle.session.commit()
    db_handle.session.delete(track)
    assert Artist.query.count() == 0
    db_handle.session.rollback()

def test_delete_album(db_handle):
    """
    tests that the album is deleted
    """
    
    artist = _get_artist()
    album = _get_album()
    album.artist = artist
    
    db_handle.session.add(album)
    db_handle.session.commit()
    db_handle.session.delete(album)
    assert Album.query.count() == 0
    db_handle.session.rollback()


def test_album_ondelete_track(db_handle):
    choreography = _get_choreography()
    track = _get_track()
    album = _get_album()
    track.album = album
    track.choreography = choreography
    db_handle.session.add(track)
    db_handle.session.add(album)
    db_handle.session.commit()
    db_handle.session.delete(album)
    db_handle.session.commit()
    assert Track.query.count() == 0
    db_handle.session.rollback()


def test_album_ondelete_artist(db_handle):
    """
    tests if album is delete if the artist is deleted
    """
    album = _get_album()
    artist = _get_artist()
    album.artist = artist
    db_handle.session.add(album)
    db_handle.session.add(artist)
    db_handle.session.commit()
    db_handle.session.delete(artist)
    db_handle.session.commit()
    assert Album.query.count() == 0
    db_handle.session.rollback()






    
""" def test_choreography_track_one_to_one(db_handle):
    
    Tests that the relationship between track and choreography is one-to-one.
    i.e. that we cannot assign the same choreography for two tracks.

    
    choreography = _get_choreography()
    track_1 = _get_track(1)
    track_2 = _get_track(2)
    track_1.choreography = choreography
    track_2.choreography = choreography
    db_handle.session.add(choreography)
    db_handle.session.add(track_1)
    db_handle.session.add(track_2)    
    with pytest.raises(IntegrityError):
        db_handle.session.commit() """
        
""" def test_album_ondelete_track(db_handle):
    
    Tests that album's track foreign key is set to null when the track
    is deleted.
    
    
    album = _get_album()
    track = _get_track()
    album.track = track
    db_handle.session.add(album)
    db_handle.session.commit()
    db_handle.session.delete(track)
    db_handle.session.commit()
    assert album.track is None """


        
""" def test_choreography_columns(db_handle):
    """
""" Tests the types and restrictions of choreography columns. Checks that numerical
    values only accepts numbers, and that all of the columns are optional.  """
"""
    
    choreography = _get_choreography()
    choreography.latitude = str(choreography.latitude) + "°"
    db_handle.session.add(choreography)
    with pytest.raises(StatementError):
        db_handle.session.commit()
        
    db_handle.session.rollback()
        
    choreography = _get_choreography()
    choreography.longitude = str(choreography.longitude) + "°"
    db_handle.session.add(choreography)
    with pytest.raises(StatementError):
        db_handle.session.commit()
    
    db_handle.session.rollback()

    choreography = _get_choreography()
    choreography.altitude = str(choreography.altitude) + "m"
    db_handle.session.add(choreography)
    with pytest.raises(StatementError):
        db_handle.session.commit()
    
    db_handle.session.rollback()
    
    choreography = choreography()
    db_handle.session.add(choreography)
    db_handle.session.commit()     """
    
def test_track_columns(db_handle):
    """
    Tests track columns' restrictions. Name must be unique, and name and model
    must be mandatory.
    """

    track_1 = _get_track()
    track_2 = _get_track()
    db_handle.session.add(track_1)
    db_handle.session.add(track_2)    
    with pytest.raises(IntegrityError):
        db_handle.session.commit()

    db_handle.session.rollback()
    
    track = _get_track()
    track.title = None
    db_handle.session.add(track)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()
    
  
    
def test_album_columns(db_handle):
    """
    Tests that a album release only accepts date values 
    """

    
    album = _get_album()
    album.release = "20:12:11"
    db_handle.session.add(album)
    with pytest.raises(StatementError):
        db_handle.session.commit()
    
""" def test_artist_columns(db_handle):
    
    Tests that all columns in the artist table are mandatory. Also tests
    that start and end only accept datetime values.
    
    
    # Tests for nullable
    artist = _get_artist()
    artist.start = None
    db_handle.session.add(artist)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()

    artist = _get_artist()
    artist.end = None
    db_handle.session.add(artist)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()

    artist = _get_artist()
    artist.name = None
    db_handle.session.add(artist)
    with pytest.raises(IntegrityError):
        db_handle.session.commit()
    
    db_handle.session.rollback()
        
    # Tests for column type
    artist = _get_artist()
    artist.start = time.time()
    db_handle.session.add(artist)
    with pytest.raises(StatementError):
        db_handle.session.commit()
    
    db_handle.session.rollback()
    
    artist = _get_artist()
    artist.end = time.time()
    db_handle.session.add(artist)
    with pytest.raises(StatementError):
        db_handle.session.commit()
     """
