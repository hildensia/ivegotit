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

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
db = SQLAlchemy(app)
application = app


class GIList(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(100))
    time = db.Column(db.DateTime)
    comment = db.Column(db.Text)

    def __init__(self):
        self.time = datetime.datetime.now()
        self.id = random.getrandbits(24)


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
        try:
            self.id = GIEntry.query.filter_by(gi_list=gi_list).all()[-1].id + 1
        except IndexError:
            self.id = 0
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


@app.route("/impressum")
def impressum():
    form = OpenForm()
    return flask.render_template("impressum.html", open_form=form)


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


@app.route("/entry/add", methods=[u'POST'])
def new_entry():
    form = GIEntryForm()
    list_id = form.gi_list.data
    gi_list = GIList.query.filter_by(id=list_id).first()
    gi_entry = GIEntry(list_id)
    form.populate_obj(gi_entry)
    db.session.add(gi_entry)
    db.session.commit()
    return flask.jsonify({'html': flask.render_template("list_entry.html",
                                                        entry=gi_entry,
                                                        gi_list=gi_list),
                          'entry_id': gi_entry.id})


@app.route("/entry/gotit", methods=[u'POST'])
def gotit():
    entry = (GIEntry.query
             .filter_by(gi_list=flask.request.form['gi_list'])
             .filter_by(id=flask.request.form['entry_id']).first())
    gi_list = GIList.query.filter_by(id=flask.request.form['gi_list']).first()
    entry.gotit = True
    db.session.commit()

    return flask.jsonify({'html': flask.render_template("list_entry.html",
                                                        entry=entry,
                                                        gi_list=gi_list)})


@app.route("/entry/dontneed", methods=[u'POST'])
def dontneed_entry():
    entry = (GIEntry.query
             .filter_by(gi_list=flask.request.form['gi_list'])
             .filter_by(id=flask.request.form['entry_id']).first())
    gi_list = GIList.query.filter_by(id=flask.request.form['gi_list']).first()
    entry.dontneed = True
    db.session.commit()

    return flask.jsonify({'html': flask.render_template("list_entry.html",
                                                        entry=entry,
                                                        gi_list=gi_list)})


@app.route("/entry/reset", methods=[u'POST'])
def reset_entry():
    entry = (GIEntry.query
             .filter_by(gi_list=flask.request.form['gi_list'])
             .filter_by(id=flask.request.form['entry_id']).first())
    gi_list = GIList.query.filter_by(id=flask.request.form['gi_list']).first()
    entry.dontneed = False
    entry.gotit = False
    db.session.commit()

    return flask.jsonify({'html': flask.render_template("list_entry.html",
                                                        entry=entry,
                                                        gi_list=gi_list)})


@app.route("/entry/rm", methods=[u'POST'])
def remove_entry():
    entry = (GIEntry.query
             .filter_by(gi_list=flask.request.form['gi_list'])
             .filter_by(id=flask.request.form['entry_id']).first())
    db.session.delete(entry)
    db.session.commit()
    return flask.jsonify({'text': 'True'})


def create_database():
    db.create_all()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--createdb", help="Creates the initial database.",
                        action="store_true")
    parser.add_argument("--debug", help="Runs the app in the debugger mode.",
                        action="store_true")
    args = parser.parse_args()

    if args.createdb:
        create_database()
        sys.exit()
    elif args.debug:
        app.run(debug=True)
    else:
        app.run(debug=False)
