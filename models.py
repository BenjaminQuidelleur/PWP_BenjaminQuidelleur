import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import binascii, hashlib, os
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

class Choreography(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(64), nullable=False)
    track = db.relationship('Track', back_populates='choreography')

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["name", "description"],
            "additionalProperties": False
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
    __table_args__ = (db.UniqueConstraint("disc_number", "track_number", "album_id", name="_track_index_uc"),)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    disc_number = db.Column(db.Integer, default=1)
    track_number = db.Column(db.Integer, nullable=False)
    length = db.Column(db.Time, nullable=False)
    lyrics = db.Column(db.String, nullable=False)
    album_id = db.Column(db.ForeignKey("album.id", ondelete="CASCADE"), nullable=False)
    choreography_id = db.Column(db.ForeignKey("choreography.id", ondelete="CASCADE"), nullable=False)
    # artist_id = db.Column(db.ForeignKey("artist.id", ondelete="SET NULL"), nullable=False)
    choreography = db.relationship("Choreography", back_populates="track")
    album = db.relationship("Album", back_populates="track")

    # artist = db.relationship("Artist", back_populates="artist_track")

    def __repr__(self):
        return "{} <{}> on {}".format(self.title, self.id, self.album.title)

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["disc_number", "track_number", "album_id", "choreography_id"]
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
    __table_args__ = (db.UniqueConstraint("title", "artist_id", name="_artist_title_uc"),{'extend_existing': True})

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    release = db.Column(db.Date, nullable=False)
    artist_id = db.Column(db.ForeignKey("artist.id", ondelete="CASCADE"), nullable=True)
    genre = db.Column(db.String, nullable=True)
    discs = db.Column(db.Integer, default=1)

    artist = db.relationship("Artist", back_populates="albums")
    # va_artists = db.relationship("Artist", secondary=va_artist_table)
    track = db.relationship("Track",
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
    __table_args__ = {'extend_existing': True}
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