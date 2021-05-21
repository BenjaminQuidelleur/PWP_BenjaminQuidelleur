from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, OperationalError
import json
from jsonschema import validate, ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy import event

from flask import Flask, Response, url_for
from flask_restful import Api, Resource
import os
import tempfile
from datetime import date, time
from flask_cors import CORS




#sys.path.insert(0, '/home/kali/Documents/web/')
#from masonbuilder import MasonBuilder
app = Flask(__name__, static_folder="static")
CORS(app)
api = Api(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['CORS_HEADERS'] = 'Content-Type'
db = SQLAlchemy(app)


MASON = "application/vnd.mason+json"
CHOREOGRAPHY_PROFILE = "/profiles/choreography/"
TRACK_PROFILE = "/profiles/track/"
ALBUM_PROFILE = "/profiles/album/"
ARTIST_PROFILE = "/profiles/artist/"
ERROR_PROFILE = "/profiles/error/"
LINK_RELATIONS_URL = "/instadium/link-relations/"


class Choreography(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(64), nullable=False)
    in_track = db.relationship('Track', back_populates='choreography')

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["name", "description"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Choreography name",
            "type": "string"
        }
        props["description"] = {
            "description": "Choreography's description",
            "type": "string"
        }
        return schema

 
class Track(db.Model):
    
    __table_args__ = (db.UniqueConstraint("disc_number", "track_number", "album_id", name="_track_index_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    disc_number = db.Column(db.Integer, default=1)
    track_number = db.Column(db.Integer, nullable=False)
    length = db.Column(db.Time, nullable=False)
    lyrics = db.Column(db.String, nullable=False)
    album_id = db.Column(db.ForeignKey("album.id", ondelete="CASCADE"), nullable=False)
    choreography_id = db.Column(db.ForeignKey("choreography.id", ondelete="CASCADE"), nullable=True)
    #artist_id = db.Column(db.ForeignKey("artist.id", ondelete="SET NULL"), nullable=False)
    choreography = db.relationship("Choreography", back_populates="in_track")
    album = db.relationship("Album", back_populates="tracks")
    #artist = db.relationship("Artist", back_populates="artist_track")

    def __repr__(self):
        return "{} <{}> on {}".format(self.title, self.id, self.album.title)
    
    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["disc_number", "track_number", "album_id"]
        }
        props = schema["properties"] = {}
        props["disc_number"] = {
            "description": "disc number",
            "type": "number"
        }
        props["track_number"] = {
            "description": "track's number on the disc",
            "type": "number"
        }
        return schema
    
class Album(db.Model):
    
    __table_args__ = (db.UniqueConstraint("title", "artist_id", name="_artist_title_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    release = db.Column(db.Date, nullable=False)
    artist_id = db.Column(db.ForeignKey("artist.id", ondelete="CASCADE"), nullable=True)
    genre = db.Column(db.String, nullable=True)
    discs = db.Column(db.Integer, default=1)
    
    artist = db.relationship("Artist", back_populates="albums")
    #va_artists = db.relationship("Artist", secondary=va_artist_table)
    tracks = db.relationship("Track",
        cascade="all,delete",
        back_populates="album",
        order_by=(Track.disc_number, Track.track_number)
    )
    
    sortfields = ["artist", "release", "title"]
    
    def __repr__(self):
        return "{} <{}>".format(self.title, self.id)

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["title"]
        }
        props = schema["properties"] = {}
        props["title"] = {
            "description": "album title",
            "type": "string"
        }
        return schema

class Artist(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    unique_name = db.Column(db.String, nullable=False, unique=True)
 
    
    albums = db.relationship("Album", cascade="all,delete", back_populates="artist")

    def __repr__(self):
        return "{} <{}>".format(self.name, self.id)

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["name", "unique_name"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "Artist name",
            "type": "string"
        }
        props["unique_name"] = {
            "description": "Artist unique name",
            "type": "string"
        }
        return schema


def _get_choreography(name="chore", description='une purée de choreo'):
    return Choreography(
        name=name,
        description=description,
    )

def _get_track(title="track1"):
    return Track(
        title=title,
        disc_number=1,
        track_number=8,
        length=time(0, 3, 40),
        lyrics="tttttttttttttttttttt"
    )

def _get_album(title="album1"):
    return Album(
        title=title,
        release=date(2021, 11, 12),
        genre="Rap",
        discs=1
    )

def _get_artist(name="ben10", unique_name="nasmus"):
    return Artist(
        name=name,
        unique_name=unique_name
    )

def _populate_db():
    choreography = _get_choreography('chore', 'une purée de choreo')
    choreography1 = _get_choreography("un truc", 'pain au chocolat')
    choreography2 = _get_choreography("namemodified", 'ce cours est null')
    track = _get_track()
    album = _get_album()
    artist = _get_artist()
    artist0 = _get_artist('desChamps', 'zizou')
    artist1 = _get_artist('hamoud', 'boualam')
    artist2 = _get_artist('john', 'snow')
    track.choreography = choreography
    track.album = album
    album.artist = artist

    db.session.add(choreography)
    db.session.add(choreography1)
    db.session.add(choreography2)
    db.session.add(track)
    db.session.add(album)
    db.session.add(artist)
    db.session.add(artist0)
    db.session.add(artist1)
    db.session.add(artist2)
    artist.albums.append(album)
    db.session.commit()

meta = db.metadata
for table in reversed(meta.sorted_tables):
    print('Clear table')
    db.session.execute(table.delete())
db.session.commit()



db.create_all()
_populate_db()

db_fd, db_fname = tempfile.mkstemp()
db.session.remove()
os.close(db_fd)
os.unlink(db_fname)


class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href




class InStadiumBuilder(MasonBuilder):


    def add_control_all_albums(self):
        self.add_control(
            "stadium:albums-all",
            api.url_for(AlbumCollection),
            method="GET",
            encoding="json",
            title="Get all albums"
        )

    def add_control_all_artists(self):
        self.add_control(
            "stadium:artists-all",
            api.url_for(ArtistCollection),
            method="GET",
            encoding="json",
            title="Get all artists"
        )

    def add_control_all_choreographies(self):
        self.add_control(
            "stadium:choreographies-all",
            api.url_for(ChoreographyCollection),
            method="GET",
            encoding="json",
            title="Get all choreographies"
        )




    def add_control_delete_album(self,title):
            self.add_control(
                "stadium:delete",
                api.url_for(AlbumItem, title=title),
                method="DELETE",
                title="delete this album"
            )

    def add_control_delete_artist(self,unique_name):
            self.add_control(
                "stadium:delete",
                api.url_for(ArtistItem, unique_name=unique_name),
                method="DELETE",
                title="delete this artist"
            )

    def add_control_delete_choreography(self,name):
            self.add_control(
                "stadium:delete",
                api.url_for(ChoreographyItem, name=name),
                method="DELETE",
                title="delete this choreography"
            )



    def add_control_add_album(self):
            self.add_control(
                "stadium:add-album",
                api.url_for(AlbumCollection),
                method="POST",
                encoding="json",
                title="Add new album",
                schema=Album.get_schema()
            )

    def add_control_add_choreography(self):
            self.add_control(
                "stadium:add-choreography",
                api.url_for(ChoreographyCollection),
                method="POST",
                encoding="json",
                title="Add new choreography",
                schema=Choreography.get_schema()
            )


    def add_control_add_artist(self):
            self.add_control(
                "stadium:add-artist",
                api.url_for(ArtistCollection),
                method="POST",
                encoding="json",
                title="Add new artist",
                schema=Artist.get_schema()
            )        

    def add_control_add_track(self):
            self.add_control(
                "stadium:add-track",
                api.url_for(AlbumItem),
                method="POST",
                encoding="json",
                title="Add new track",
                schema=Track.get_schema()
            ) 


    
    def add_control_edit_album(self, title):
                self.add_control(
                    "edit",
                    api.url_for(AlbumItem, title=title),
                    method="PUT",
                    encoding="json",
                    title="edit album",
                    schema=Album.get_schema()
                )

    def add_control_edit_artist(self, unique_name):
                self.add_control(
                    "edit",
                    api.url_for(ArtistItem, unique_name=unique_name),
                    method="PUT",
                    encoding="json",
                    title="edit artist",
                    schema=Artist.get_schema()
                )



    def add_control_edit_choreography(self, name):
                self.add_control(
                    "edit",
                    api.url_for(ChoreographyItem, name=name),
                    method="PUT",
                    encoding="json",
                    title="edit choreography",
                    schema=Choreography.get_schema()
                )

def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)

class AlbumCollection(Resource):

    def get(self):
        body = InStadiumBuilder()
        
        body.add_namespace("stadium", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(AlbumCollection))
        body.add_control_add_album()
        body["items"] = []

        for db_album in Album.query.all():
            item = InStadiumBuilder(
                title=db_album.title,
                release=db_album.release,
                genre=db_album.genre,
                disc= db_album.disc
            )
            item.add_control("self", api.url_for(AlbumItem, title=db_album.title))
            item.add_control("profile", ALBUM_PROFILE)
            body["items"].append(item)
            
        return Response(json.dumps(body), 200, mimetype=MASON)

    

class AlbumItem(Resource):
    
    def get(self, title):
        db_album = Album.query.filter_by(title=title).first()
        if db_album is None:
            return create_error_response(404, "Not found", 
                "No product was found with the name {}".format(title)
            )
        
        body = InStadiumBuilder(
            title=db_album.title,
            release=db_album.release,
            genre=db_album.genre,
            disc= db_album.disc
        )
        body.add_namespace("stadium", "/api/")
        body.add_control("self", api.url_for(AlbumItem, title=title))
        body.add_control("profile", ALBUM_PROFILE)
        body.add_control("collection", api.url_for(AlbumCollection))
        body.add_control_delete_album(title)
        body.add_control_edit_album(title)
        body.add_control_add_album()
      

        
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    def put(self, title):
        db_album = Album.query.filter_by(title=title).first()
        if db_album is None:
            return create_error_response(404, "Not found", 
                "No product was found with the name {}".format(title)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Album.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_album.title = request.json["title"]
        db_album.release = request.json["release"]
        db_album.genre = request.json["genre"]
        db_album.disc = request.json["disc"]
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Album with name '{}' already exists.".format(request.json["title"])
            )
        
        return Response(status=204)

    def delete(self, title):
        db_album = Album.query.filter_by(title=title).first()
        if db_album is None:
            return create_error_response(404, "Not found", 
                "No product was found with the name {}".format(handle)
            )
        
        db.session.delete(db_album)
        db.session.commit()
        
        return Response(status=204)

class ArtistCollection(Resource):

    def get(self):
        body = InStadiumBuilder()
        
        body.add_namespace("stadium", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ArtistCollection))
        body.add_control_add_artist()
        body["items"] = []

        for db_artist in Artist.query.all():
            item = InStadiumBuilder(
                name=db_artist.name,
                unique_name=db_artist.unique_name
            )
            item.add_control("self", api.url_for(ArtistItem, unique_name=db_artist.unique_name))
            item.add_control("profile", ARTIST_PROFILE)
            body["items"].append(item)
            
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Artist.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        artist = Artist(
            name=request.json["name"],
            unique_name=request.json["unique_name"]
        )

        try:
            db.session.add(artist)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Artist with name '{}' already exists.".format(request.json["unique_name"])
            )
        
        return Response(status=201, headers={
            "Location": api.url_for(ArtistItem, unique_name=request.json["unique_name"])
        })


class ArtistItem(Resource):
    
    def get(self, unique_name):
        db_artist = Artist.query.filter_by(unique_name=unique_name).first()
        if db_artist is None:
            return create_error_response(404, "Not found", 
                "No artist was found with the name {}".format(unique_name)
            )
        
        body = InStadiumBuilder(
                name=db_artist.name,
                unique_name=db_artist.unique_name
            )
        body.add_namespace("stadium", "/api/")
        body.add_control("self", api.url_for(ArtistItem, unique_name=unique_name))
        body.add_control("profile", ARTIST_PROFILE)
        body.add_control("collection", api.url_for(ArtistCollection))
        body.add_control_delete_artist(unique_name)
        body.add_control_edit_artist(unique_name)
        body.add_control_add_artist()
      

        
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    def put(self, unique_name):
        db_artist = Artist.query.filter_by(unique_name=unique_name).first()
        if db_artist is None:
            return create_error_response(404, "Not found", 
                "No artist was found with the name {}".format(unique_name)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Artist.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_artist.name = request.json["name"]
        db_artist.unique_name = request.json["unique_name"]
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Artist with name '{}' already exists.".format(request.json["unique_name"])
            )
        
        return Response(status=204)

    def delete(self, unique_name):
        db_artist = Artist.query.filter_by(unique_name=unique_name).first()
        if db_artist is None:
            return create_error_response(404, "Not found", 
                "No artist was found with the name {}".format(unique_name)
            )
        
        db.session.delete(db_artist)
        db.session.commit()
        
        return Response(status=204)




class ChoreographyCollection(Resource):

    def get(self):
        body = InStadiumBuilder()
        
        body.add_namespace("stadium", LINK_RELATIONS_URL)
        body.add_control("self", api.url_for(ChoreographyCollection))
        body.add_control_add_choreography()
        body["items"] = []

        for db_chore in Choreography.query.all():
            item = InStadiumBuilder(
                name=db_chore.name,
                description=db_chore.description
            )
            item.add_control("self", api.url_for(ChoreographyItem, name=db_chore.name))
            item.add_control("profile", CHOREOGRAPHY_PROFILE)
            body["items"].append(item)
            
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Choreography.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        choreography = Choreography(
            name=request.json["name"],
            description=request.json["description"]
        )

        try:
            db.session.add(choreography)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Choreography with name '{}' already exists.".format(request.json["name"])
            )
        
        return Response(status=201, headers={
            "Location": api.url_for(ChoreographyItem, name=request.json["name"])
        })

class ChoreographyItem(Resource):
    
    def get(self, name):
        db_chore = Choreography.query.filter_by(name=name).first()
        if db_chore is None:
            return create_error_response(404, "Not found", 
                "No choreography was found with the name {}".format(name)
            )
        
        body = InStadiumBuilder(
                name=db_chore.name,
                description=db_chore.description
            )
        body.add_namespace("stadium", "/api/")
        body.add_control("self", api.url_for(ChoreographyItem, name=name))
        body.add_control("profile", CHOREOGRAPHY_PROFILE)
        body.add_control("collection", api.url_for(ChoreographyCollection))
        body.add_control_delete_choreography(name)
        body.add_control_edit_choreography(name)
        body.add_control_add_choreography()
      

        
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    def put(self, name):
        db_chore = Choreography.query.filter_by(name=name).first()
        if db_chore is None:
            return create_error_response(404, "Not found", 
                "No choreography was found with the name {}".format(name)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Choreography.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_chore.name = request.json["name"]
        db_chore.description = request.json["description"]
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Choreography with name '{}' already exists.".format(request.json["name"])
            )
        
        return Response(status=204)

    def delete(self, name):
        db_chore = Choreography.query.filter_by(name=name).first()
        if db_chore is None:
            return create_error_response(404, "Not found", 
                "No choreography was found with the name {}".format(name)
            )
        
        db.session.delete(db_chore)
        db.session.commit()
        
        return Response(status=204)


class TrackItem(Resource):
    
    def get(self, title):
        db_track = Track.query.filter_by(title=title).first()
        if db_track is None:
            return create_error_response(404, "Not found", 
                "No track was found with the name {}".format(title)
            )
        
        body = InStadiumBuilder(
                title = db_track.title,
                disc_number = db_track.disc_number,
                track_number = db_track.track_number
            )
        body.add_namespace("stadium", "/api/")
        body.add_control("self", api.url_for(TrackItem, title=title))
        body.add_control("profile", TRACK_PROFILE)
        body.add_control("collection", api.url_for(AlbumItem))
        body.add_control_delete_track(title)
        body.add_control_edit_track(title)
        body.add_control_add_track()
      

        
        return Response(json.dumps(body), 200, mimetype=MASON)
    
    def put(self, title):
        db_track = Track.query.filter_by(title=title).first()
        if db_track is None:
            return create_error_response(404, "Not found", 
                "No track was found with the name {}".format(title)
            )
        
        if not request.json:
            return create_error_response(415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Track.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
    
        db_chore.name = request.json["name"]
        db_chore.description = request.json["description"]
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, "Already exists", 
                "Track with name '{}' already exists.".format(request.json["title"])
            )
        
        return Response(status=204)

    def delete(self, title):
        db_track = Track.query.filter_by(title=title).first()
        if db_track is None:
            return create_error_response(404, "Not found", 
                "No track was found with the name {}".format(title)
            )
        
        db.session.delete(db_track)
        db.session.commit()
        
        return Response(status=204)

api.add_resource(ArtistCollection, "/api/artists/")
api.add_resource(ArtistItem, "/api/artists/<unique_name>/")

api.add_resource(AlbumCollection, "/api/albums/")
api.add_resource(AlbumItem, "/api/artists/<artist>/albums/<title>")

api.add_resource(ChoreographyCollection, "/api/choreographies/")
api.add_resource(ChoreographyItem, "/api/choreographies/<name>/")
#collection_uri = api.url_for(ProductCollection)
#product_uri = api.url_for(ProductItem)
#api.add_resource(Product, "/api/products/add")
api.add_resource(TrackItem, "/api/artists/<artist>/albums/<album>/<disc>/<track>/")

@app.route("/api/")
def entrypoint():
    body = InStadiumBuilder()
        
    body.add_namespace("stadium", LINK_RELATIONS_URL)
    #body.add_control_all_albums()
    return Response(json.dumps(body), 200, mimetype=MASON)


@app.route(LINK_RELATIONS_URL)
def send_link_relations():
    return "link relations"

@app.route("/profiles/<profile>/")
def send_profile(profile):
    return "you requests {} profile".format(profile)

if __name__ == '__main__':
    app.run()