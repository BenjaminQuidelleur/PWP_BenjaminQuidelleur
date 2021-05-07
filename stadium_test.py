
import json
import os
import pytest
import tempfile
import time
from datetime import date, time
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

from app import app, db
from app import Track, Choreography, Album, Artist



@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.config["TESTING"] = True

    db.create_all()
    _populate_db()


    yield app.test_client()

    db.session.remove()
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
    
def _get_artist(unique_name="Ramzi"):
    return Artist(
        name="salo",
        unique_name=unique_name
    )

def _populate_db():
    choreography = _get_choreography()
    track = _get_track()
    album = _get_album()
    artist = _get_artist()
    track.choreography = choreography
    track.album = album
    album.artist = artist
    artist.albums.append(album)
    db.session.add(choreography)
    db.session.add(track)
    db.session.add(album)
    db.session.add(artist)
    db.session.commit()
    
def _get_choreography_json():
    """
    Creates a valid sensor JSON object to be used for PUT and POST tests.
    """
    
    return {"name": "nametestchore", "description": "descchore"}

def _get_artist_json():
    return {"name": "nameartist", "unique_name": "Ramzi"}
    
def _check_namespace(client, response):
    """
    Checks that the "senhub" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """
    
    ns_href = response["@namespaces"]["stadium"]["name"]
    resp = client.get(ns_href)
    assert resp.status_code == 200
    
def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """
    
    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200
    
def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """
    
    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204
    
def _check_control_put_method(ctrl, client, obj):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = _get_choreography_json()
    body["name"] = obj["name"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204
    
def _check_control_post_method(ctrl, client, obj):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_choreography_json()
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201

class TestChoreographyCollection(object):
    '''
    This class implements tests for each HTTP method in sensor collection
    resource.'''


    RESOURCE_URL = "/api/choreographies/"

    def test_get(self, client):
        '''
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.'''


        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        #_check_control_post_method("stadium:choreographies-all", client, body)
        assert len(body["items"]) == 1
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)
            assert "name" in item
            assert "description" in item
#
    def test_post(self, client):
        #         '''
        #         Tests the POST method. Checks all of the possible error codes, and
        #         also checks that a valid request receives a 201 response with a
        #         location header that leads into the newly created resource.'''
        #
        #
        valid = _get_choreography_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

    #
    #         # test with valid and see that it exists afterward
    #         resp = client.post(self.RESOURCE_URL, json=valid)
    #         assert resp.status_code == 201
    #         assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
    #         resp = client.get(resp.headers["Location"])
    #         assert resp.status_code == 200
    #         body = json.loads(resp.data)
    #         assert body["name"] == "nametestchore"
    #         assert body["description"] == "descchore"
    #
    #         # send same data again for 409
    #         resp = client.post(self.RESOURCE_URL, json=valid)
    #         assert resp.status_code == 409
    #
    #         # remove model field for 400
    #         valid.pop("description")
    #         resp = client.post(self.RESOURCE_URL, json=valid)
    #         assert resp.status_code == 400


class TestChoreographyItem(object):

    RESOURCE_URL = "/api/choreography/chore/"
    INVALID_URL = "/api/choreography/psg/"
    MODIFIED_URL = "/api/choreography/chore/"

    def test_get(self, client):
#         '''
#         Tests the GET method. Checks that the response status code is 200, and
#         then checks that all of the expected attributes and controls are
#         present, and the controls work. Also checks that all of the items from
#         the DB popluation are present, and their controls.'''
#
#
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == "chore"
        assert body["description"] == "blablabla"
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body)
        #_check_control_delete_method("stadium:delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404




    def test_put(self, client):
    #     '''
    #     Tests the PUT method. Checks all of the possible erroe codes, and also
    #     checks that a valid request receives a 204 response. Also tests that
    #     when name is changed, the sensor can be found from a its new URI. '''
    #
    #
        valid = _get_choreography_json()

        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
    #
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
    #
    #     # test with another choreography's name
    #     valid["name"] = "mc"
    #     resp = client.put(self.RESOURCE_URL, json=valid)
    #     assert resp.status_code == 409
    #
        # test with valid (only change model)
        valid["name"] = "chore"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
    #
        # remove field for 400
        valid.pop("description")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
    #
        valid = _get_choreography_json()
        # resp = client.put(self.RESOURCE_URL, json=valid)
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["description"] == valid["description"]
    #
   # def test_delete(self, client):
    #     Tests the DELETE method. Checks that a valid request reveives 204
    #     response and that trying to GET the sensor afterwards results in 404.
    #     Also checks that trying to delete a sensor that doesn't exist results
    #     in 404.
    #     resp = client.delete(self.MODIFIED_URL)
    #     assert resp.status_code == 204
    #     resp = client.get(self.RESOURCE_URL)
    #     assert resp.status_code == 404
    #     resp = client.delete(self.INVALID_URL)
    #     assert resp.status_code == 404


#class TestArtistCollection(object):
    """
    This class implements tests for each HTTP method in artist collection
    resource.
    """

#    RESOURCE_URL = "/api/artists/"

#    def test_get(self, client):
#         """
#         Tests the GET method. Checks that the response status code is 200, and
#         then checks that all of the expected attributes and controls are
#         present, and the controls work. Also checks that all of the items from
#         the DB popluation are present, and their controls.
#         """

        #resp = client.get(self.RESOURCE_URL)
        #assert resp.status_code == 200
        # body = json.loads(resp.data)
        # _check_namespace(client, body)
        # _check_control_get_method("stadium:artists-all", client, body)
        # assert len(body["items"]) == 1
        # for item in body["items"]:
        #     _check_control_get_method("self", client, item)
        #     _check_control_get_method("profile", client, item)
        #     assert "name" in item
        #     assert "unique_name" in item

    # def test_post(self, client):
    #     """
    #     Tests the POST method. Checks all of the possible error codes, and
    #     also checks that a valid request receives a 201 response with a
    #     location header that leads into the newly created resource.
    #     """
    #
    #     valid = _get_artist_json()
    #
    #     # test with wrong content type
    #     resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
    #     assert resp.status_code == 415
    #
    #     # test with valid and see that it exists afterward
    #     resp = client.post(self.RESOURCE_URL, json=valid)
    #     assert resp.status_code == 201
    #     assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
    #     resp = client.get(resp.headers["Location"])
    #     assert resp.status_code == 200
    #     body = json.loads(resp.data)
    #     assert body["name"] == "nameartist"
    #     assert body["unique_name"] == "nameartist"
    #
    #     # send same data again for 409
    #     resp = client.post(self.RESOURCE_URL, json=valid)
    #     assert resp.status_code == 409
    #
    #     # remove model field for 400
    #     valid.pop("unique_name")
    #     resp = client.post(self.RESOURCE_URL, json=valid)
    #     assert resp.status_code == 400



# class TestArtistItem(object):
#
#      RESOURCE_URL = "/api/artists/Ramzi/"
#      INVALID_URL = "/api/artists/non-name/"
#      MODIFIED_URL = "/api/artists/nameartistmodif/"
#
#      def test_get(self, client):
#
#         """
#         Tests the GET method. Checks that the response status code is 200, and
#         then checks that all of the expected attributes and controls are
#         present, and the controls work. Also checks that all of the items from
#         the DB popluation are present, and their controls.
#         """
#
#         resp = client.get(self.RESOURCE_URL)
#         assert resp.status_code == 200
#         body = json.loads(resp.data)
#         assert body["name"] == "nameartist"
#         assert body["unique_name"] == "nameartist"
#         _check_namespace(client, body)
#         _check_control_get_method("profile", client, body)
#         _check_control_get_method("collection", client, body)
#         _check_control_put_method("edit", client, body)
#         _check_control_delete_method("stadium:delete", client, body)
#         resp = client.get(self.INVALID_URL)
#         assert resp.status_code == 404
#
#     def test_put(self, client):
#         """
#         Tests the PUT method. Checks all of the possible erroe codes, and also
#         checks that a valid request receives a 204 response. Also tests that
#         when name is changed, the sensor can be found from a its new URI.
#         """
#
#         valid = _get_artist_json()
#
#         # test with wrong content type
#         resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
#         assert resp.status_code == 415
#
#         resp = client.put(self.INVALID_URL, json=valid)
#         assert resp.status_code == 404
#
#
#
#         # test with valid (only change model)
#         valid["name"] = "artistname"
#         resp = client.put(self.RESOURCE_URL, json=valid)
#         assert resp.status_code == 204
#
#         # remove field for 400
#         valid.pop("unique_name")
#         resp = client.put(self.RESOURCE_URL, json=valid)
#         assert resp.status_code == 400
#
#         valid = _get_artist_json()
#         resp = client.put(self.RESOURCE_URL, json=valid)
#         resp = client.get(self.MODIFIED_URL)
#         assert resp.status_code == 200
#         body = json.loads(resp.data)
#         assert body["unique_name"] == valid["unique_name"]
#
#     def test_delete(self, client):
#         """
#         Tests the DELETE method. Checks that a valid request reveives 204
#         response and that trying to GET the sensor afterwards results in 404.
#         Also checks that trying to delete a sensor that doesn't exist results
#         in 404.
#         """
#
#         resp = client.delete(self.RESOURCE_URL)
#         assert resp.status_code == 204
#         resp = client.get(self.RESOURCE_URL)
#         assert resp.status_code == 404
#         resp = client.delete(self.INVALID_URL)
#         assert resp.status_code == 404
        
        
        
class TestAlbumCollection(object):
#
     RESOURCE_URL = "/api/albums/"

#
     def test_get(self, client):

     #    """
     #    Tests the GET method. Checks that the response status code is 200, and
     #    then checks that all of the expected attributes and controls are
     #    present, and the controls work. Also checks that all of the items from
     #    the DB popluation are present, and their controls.
     #    """
     #
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        
        
        
        
        
    
    

    

        
            
    