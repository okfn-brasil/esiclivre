#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals  # unicode by default

from extensions import db


class Entidades(db.Model):
    __tablename__ = 'entidades'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)


class Pedidos(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    entidade = db.Column(db.String(200), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'),
                          nullable=False)
    text = db.Column(db.Text, nullable=False)
    received = db.Column(db.DateTime, nullable=False)
    sent = db.Column(db.DateTime, nullable=True, default=None)
    protocolo = db.Column(db.Integer, nullable=True)


class Author(db.Model):
    __tablename__ = 'author'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    comments = db.relationship("Pedidos", backref="author")
