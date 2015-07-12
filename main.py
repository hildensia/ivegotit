import flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.wtf import Form
from wtforms import (StringField, TextAreaField, SubmitField, HiddenField,
                     validators)

import random
import datetime
import argparse
import sys

import os
import traceback
import config

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_url
app.config['SECRET_KEY'] = config.secret_key
db = SQLAlchemy(app)
application = app


class GIList(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(100))
    time = db.Column(db.DateTime)
    comment = db.Column(db.Text)

    def __init__(self):
        self.time = datetime.datetime.now()
        self.id = random.getrandbits(32)


class GIListForm(Form):
    name = StringField(u'List\'s name')
    comment = TextAreaField(u'A comment to this list')
    submit = SubmitField(u'Create List')


class GIEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gi_list = db.Column(db.BigInteger, db.ForeignKey('gi_list.id'),
                        primary_key=True)
    entry = db.Column(db.String(100))
    gotit = db.Column(db.Boolean)
    dontneed = db.Column(db.Boolean)

    def __init__(self, gi_list):
        # get all list entries, count them, make id = number + 1
        self.id = len(GIEntry.query.filter_by(gi_list=gi_list).all())
        self.gotit = False
        self.dontneed = False


class GIEntryForm(Form):
    entry = StringField(u'Bring it', [validators.required(),
                                      validators.length(max=100)])
    submit = SubmitField(u'Add')
    gi_list = HiddenField()


class OpenForm(Form):
    gi_list = StringField(u'List ID')
    submit = SubmitField(u'Open')


@app.route("/")
def index():
    form = OpenForm()
    return flask.render_template("index.html", form=form, open_form=form)


@app.route("/list/create")
def create_list():
    form = GIListForm()
    open_form = OpenForm()
    return flask.render_template('create_list.html', form=form, open_form=open_form)


@app.route("/list/new", methods=[u'POST'])
def new_list():
    print('create a new list')
    form = GIListForm()
    if form.validate_on_submit():
        print('form is validate')
        gi_list = GIList()
        form.populate_obj(gi_list)
        print('object populated')
        db.session.add(gi_list)
        print('database add')
        db.session.commit()
        print('database commit')
        return flask.redirect('/list/{}'.format(gi_list.id))

    return flask.redirect('/list/create')


@app.route("/entry/reset/<list_id>/<entry_id>")
def reset_entry(list_id, entry_id):
    entry = (GIEntry.query
             .filter_by(gi_list=list_id)
             .filter_by(id=entry_id).first())
    entry.gotit = False
    entry.dontneed = False
    db.session.commit()

    return flask.redirect('/list/{}'.format(list_id))


@app.route("/list/open", methods=[u'POST'])
def open_list():
    form = OpenForm()
    if form.validate_on_submit():
        gi_list = form.gi_list.data
        return flask.redirect('/list/{}'.format(gi_list))


@app.route("/list/<list_id>")
def shopping_list(list_id):
    gi_list = GIList.query.filter_by(id=list_id).first_or_404()

    gi_entries = GIEntry.query.filter_by(gi_list=list_id).all()
    new_entry_form = GIEntryForm(gi_list=list_id)

    open_form = OpenForm()
    return flask.render_template('list.html', new_entry_form=new_entry_form,
                                 gi_list=gi_list, gi_entries=gi_entries,
                                 open_form=open_form)


@app.route("/entry/new", methods=[u'POST'])
def new_entry():
    form = GIEntryForm()
    list_id = form.gi_list.data
    if form.validate_on_submit():
        gi_entry = GIEntry(list_id)
        form.populate_obj(gi_entry)
        db.session.add(gi_entry)
        db.session.commit()
    return flask.redirect('/list/{}'.format(list_id))


@app.route("/entry/gotit/<list_id>/<entry_id>")
def gotit_get(list_id, entry_id):
    entry = (GIEntry.query
             .filter_by(gi_list=list_id)
             .filter_by(id=entry_id).first())
    entry.gotit = True
    db.session.commit()

    return flask.redirect('/list/{}'.format(list_id))


@app.route("/entry/dontneed/<list_id>/<entry_id>")
def dontneed_get(list_id, entry_id):
    entry = (GIEntry.query
             .filter_by(gi_list=list_id)
             .filter_by(id=entry_id).first())
    entry.dontneed = True
    db.session.commit()

    return flask.redirect('/list/{}'.format(list_id))


@app.route("/entry/rm/<list_id>/<entry_id>")
def remove_entry(list_id, entry_id):
    entry = (GIEntry.query
             .filter_by(gi_list=list_id)
             .filter_by(id=entry_id).first())
    db.session.delete(entry)
    db.session.commit()

    return flask.redirect('/list/{}'.format(list_id))


def create_database():
    db.create_all()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--createdb", help="Creates the initial database.",
                        action="store_true")
    args = parser.parse_args()

    if args.createdb:
        create_database()
        sys.exit()

    else:
        app.run(debug=True)
