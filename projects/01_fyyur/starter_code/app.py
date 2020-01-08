#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ARRAY, ForeignKey
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
my_migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    genres = Column(ARRAY(String))
    address = Column(String(120))
    city = Column(String(120))
    state = Column(String(120))
    phone = Column(String(120))
    website = Column(String(120))
    facebook_link = Column(String(120))
    seeking_talent = Column(Boolean)
    seeking_description = Column(String(500))
    image_link = Column(String(500))

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'

'''
Show = db.Table('Show',
    Column('venue_id', Integer, ForeignKey('Venue.id'), primary_key=True),
    Column('artist_id', Integer, ForeignKey('Artist.id'), primary_key=True),
    Column('start_time', DateTime, nullable=False, default=datetime.utcnow)
)
'''


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    genres = Column(ARRAY(String))
    city = Column(String(120))
    state = Column(String(120))
    phone = Column(String(120))
    website = Column(String(120))
    facebook_link = Column(String(120))
    seeking_venue = Column(Boolean)
    seeking_description = Column(String(500))
    image_link = Column(String(500))

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'Show'

    venue_id = Column(Integer, ForeignKey('Venue.id'), primary_key=True)
    artist_id = Column(Integer, ForeignKey('Artist.id'), primary_key=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    Artist = db.relationship('Artist', backref=db.backref("shows", cascade="all, delete-orphan"), lazy='select')
    Venue = db.relationship('Venue', backref=db.backref("shows", cascade="all, delete-orphan"), lazy='select')

    def __repr__(self):
        return f'<Show {self.id} {self.venue_id} {self.artist_id} {self.start_time}>'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='full'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    current_time = datetime.now()
    venue_data = db.session.query(Venue).order_by(Venue.city).all()
    data = []
    for venue_item in venue_data:
        upcoming_shows = 0
        for show in venue_item.shows:
            if show.start_time > current_time:
                upcoming_shows += 1
        if not data or data[-1]['city']+data[-1]['state'] != venue_item.city+venue_item.state:
            # New venue location
            data += [{
                'city': venue_item.city,
                'state': venue_item.state,
                'venues': [{
                    'id': venue_item.id,
                    'name': venue_item.name,
                    'num_upcoming_shows': upcoming_shows
                }]
            }]
        else:
            # same venue location as previous one
            data[-1]['venues'] += [{
                'id': venue_item.id,
                'name': venue_item.name,
                'num_upcoming_shows': upcoming_shows
            }]
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    venue_data = db.session.query(Venue).filter(Venue.name.ilike('%' + request.form['search_term'] + '%')).order_by(
      Venue.id)
    data = []
    for venue_item in venue_data:
        data += [{'id': venue_item.id, 'name': venue_item.name}]
    results = {'count': len(data), 'data': data}
    return render_template('pages/search_venues.html', results=results, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # replace with real venue data from the venues table, using venue_id
    venue_data = db.session.query(Venue).get(venue_id)
    if not venue_data:
        return render_template('errors/404.html')
    venue_to_display = {
        'id': venue_data.id,
        'name': venue_data.name,
        'genres': venue_data.genres,
        'address': venue_data.address,
        'city': venue_data.city,
        'state': venue_data.state,
        'phone': venue_data.phone,
        'website': venue_data.website,
        'facebook_link': venue_data.facebook_link,
        'seeking_talent': venue_data.seeking_talent,
        'seeking_description': venue_data.seeking_description,
        'image_link': venue_data.image_link,
    }
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    upcoming_shows = db.session.query(Show).filter(Show.venue_id == venue_id, Show.start_time > current_time).all()
    upcoming_shows_list = []
    for show_item in upcoming_shows:
        upcoming_shows_list += [{
            'artist_id': show_item.artist_id,
            'artist_name': show_item.Artist.name,
            'artist_image_link': show_item.Artist.image_link,
            'start_time': str(show_item.start_time)
            }]
    venue_to_display['upcoming_shows'] = upcoming_shows_list
    venue_to_display['upcoming_shows_count'] = len(upcoming_shows_list)
    past_shows = db.session.query(Show).filter(Show.venue_id == venue_id, Show.start_time <= current_time).all()
    past_shows_list = []
    for show_item in past_shows:
        past_shows_list += [{
            'artist_id': show_item.artist_id,
            'artist_name': show_item.Artist.name,
            'artist_image_link': show_item.Artist.image_link,
            'start_time': str(show_item.start_time)
            }]
    venue_to_display['past_shows'] = past_shows_list
    venue_to_display['past_shows_count'] = len(past_shows_list)
    return render_template('pages/show_venue.html', venue=venue_to_display)


#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    if not form.validate():
        flash('An error occurred. Venue ' + request.form['name'] + ' is invalid.')
        return render_template('pages/home.html')
    try:
        if request.form.get('seeking_talent', 'n') == 'y':
            seeking_talent = True
        else:
            seeking_talent = False
        seeking_description = request.form.get('seeking_description', '')
        new_venue = Venue(
            name=request.form['name'],
            genres=request.form.getlist('genres'),
            address=request.form['address'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            website=request.form['website'],
            facebook_link=request.form['facebook_link'],
            image_link=request.form['image_link'],
            seeking_talent=seeking_talent,
            seeking_description=seeking_description
        )
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except SQLAlchemyError:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        # always close the session
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        to_delete = db.session.query(Venue).get(venue_id)
        to_delete_name = to_delete.name
        db.session.delete(to_delete)
        db.session.commit()
        flash('Venue ' + to_delete_name + ' was successfully deleted!')
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred. Venue could not be listed.')
    finally:
        # always close the session
        db.session.close()
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # replace with real data returned from querying the database
    artist_data = db.session.query(Artist).order_by(Artist.id).all()
    if not artist_data:
        return render_template('errors/404.html')
    artists_to_display = []
    for artist_item in artist_data:
        artists_to_display += [{
            'id': artist_item.id,
            'name': artist_item.name
        }]
    return render_template('pages/artists.html', artists=artists_to_display)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    artist_data = db.session.query(Artist).filter(Artist.name.ilike('%'+request.form['search_term']+'%')).order_by(Artist.id)
    data = []
    for artist_item in artist_data:
        data += [{'id': artist_item.id, 'name': artist_item.name}]
    results = {'count': len(data), 'data': data}
    return render_template('pages/search_artists.html', results=results, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_data = db.session.query(Artist).get(artist_id)
    if not artist_data:
        return render_template('errors/404.html')
    artist_to_display = {
        'id': artist_data.id,
        'name': artist_data.name,
        'genres': artist_data.genres,
        'city': artist_data.city,
        'state': artist_data.state,
        'phone': artist_data.phone,
        'website': artist_data.website,
        'facebook_link': artist_data.facebook_link,
        'seeking_venue': artist_data.seeking_venue,
        'seeking_description': artist_data.seeking_description,
        'image_link': artist_data.image_link,
    }
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    upcoming_shows = db.session.query(Show).filter(Show.artist_id == artist_id, Show.start_time > current_time).all()
    upcoming_shows_list = []
    for show_item in upcoming_shows:
        upcoming_shows_list += [{
            'venue_id': show_item.artist_id,
            'venue_name': show_item.Artist.name,
            'venue_image_link': show_item.Artist.image_link,
            'start_time': str(show_item.start_time)
            }]
    artist_to_display['upcoming_shows'] = upcoming_shows_list
    artist_to_display['upcoming_shows_count'] = len(upcoming_shows_list)
    past_shows = db.session.query(Show).filter(Show.artist_id == artist_id, Show.start_time <= current_time).all()
    past_shows_list = []
    for show_item in past_shows:
        past_shows_list += [{
            'venue_id': show_item.artist_id,
            'venue_name': show_item.Artist.name,
            'venue_image_link': show_item.Artist.image_link,
            'start_time': str(show_item.start_time)
            }]
    artist_to_display['past_shows'] = past_shows_list
    artist_to_display['past_shows_count'] = len(past_shows_list)
    return render_template('pages/show_artist.html', artist=artist_to_display)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_data = db.session.query(Artist).get(artist_id)
    if not artist_data:
        return render_template('errors/404.html')
    form.name.data = artist_data.name
    form.genres.data = artist_data.genres
    form.city.data = artist_data.city
    form.state.data = artist_data.state
    form.phone.data = artist_data.phone
    form.website.data = artist_data.website
    form.facebook_link.data = artist_data.facebook_link
    form.seeking_venue.data = artist_data.seeking_venue
    form.seeking_description.data = artist_data.seeking_description
    form.image_link.data = artist_data.image_link
    artist = {
        "id": artist_data.id,
        "name": artist_data.name,
        "genres": artist_data.genres,
        "city": artist_data.city,
        "state": artist_data.state,
        "phone": artist_data.phone,
        "website": artist_data.website,
        "facebook_link": artist_data.facebook_link,
        "seeking_venue": artist_data.seeking_venue,
        "seeking_description": artist_data.seeking_description,
        "image_link": artist_data.image_link
    }
    # populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm(request.form)
    if not form.validate():
        flash('An error occurred. Artist ' + request.form['name'] + ' is invalid.')
        return render_template('pages/home.html')
    try:
        if request.form.get('seeking_venue', 'n') == 'y':
            seeking_venue = True
        else:
            seeking_venue = False
        artist_data = db.session.query(Artist).get(artist_id)
        seeking_description = request.form.get('seeking_description ', '')
        artist_data.name = request.form['name']
        artist_data.genres = request.form.getlist('genres')
        artist_data.city = request.form['city']
        artist_data.state = request.form['state']
        artist_data.phone = request.form['phone']
        artist_data.website = request.form['website']
        artist_data.facebook_link = request.form['facebook_link']
        artist_data.image_link = request.form['image_link']
        artist_data.seeking_description = seeking_description
        artist_data.seeking_venue = seeking_venue
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred. Artist could not be edited.')
    finally:
        # always close the session
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue_data = db.session.query(Venue).get(venue_id)
    if not venue_data:
        return render_template('errors/404.html')
    form.name.data = venue_data.name
    form.genres.data = venue_data.genres
    form.address.data = venue_data.address
    form.city.data = venue_data.city
    form.state.data = venue_data.state
    form.phone.data = venue_data.phone
    form.website.data = venue_data.website
    form.facebook_link.data = venue_data.facebook_link
    form.seeking_talent.data = venue_data.seeking_talent
    form.seeking_description.data = venue_data.seeking_description
    form.image_link.data = venue_data.image_link
    venue = {
        "id": venue_data.id,
        "name": venue_data.name,
        "genres": venue_data.genres,
        "address": venue_data.address,
        "city": venue_data.city,
        "state": venue_data.state,
        "phone": venue_data.phone,
        "website": venue_data.website,
        "facebook_link": venue_data.facebook_link,
        "seeking_talent": venue_data.seeking_talent,
        "seeking_description": venue_data.seeking_description,
        "image_link": venue_data.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    form = VenueForm(request.form)
    if not form.validate():
        flash('An error occurred. venue ' + request.form['name'] + ' is invalid.')
        return render_template('pages/home.html')
    try:
        if request.form.get('seeking_talent', 'n') == 'y':
            seeking_talent = True
        else:
            seeking_talent = False
        venue_data = db.session.query(Venue).get(venue_id)
        seeking_description = request.form.get('seeking_description ', '')
        venue_data.name = request.form['name']
        venue_data.genres = request.form.getlist('genres')
        venue_data.address = request.form['address']
        venue_data.city = request.form['city']
        venue_data.state = request.form['state']
        venue_data.phone = request.form['phone']
        venue_data.website = request.form['website']
        venue_data.facebook_link = request.form['facebook_link']
        venue_data.image_link = request.form['image_link']
        venue_data.seeking_description = seeking_description
        venue_data.seeking_talent = seeking_talent
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred. venue could not be edited.')
    finally:
        # always close the session
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # insert form data as a new Venue record in the db, instead
    # modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    form = ArtistForm(request.form)
    if not form.validate():
        flash('An error occurred. Artist ' + request.form['name'] + ' is invalid.')
        return render_template('pages/home.html')
    try:
        if request.form.get('seeking_venue', 'n') == 'y':
            seeking_venue = True
        else:
            seeking_venue = False
        seeking_description = request.form.get('seeking_description', '')
        new_artist = Artist(
            name=request.form['name'],
            genres=request.form.getlist('genres'),
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            website=request.form['website'],
            facebook_link=request.form['facebook_link'],
            image_link=request.form['image_link'],
            seeking_venue=seeking_venue,
            seeking_description=seeking_description,
        )
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except SQLAlchemyError:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
        # always close the session
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # replace with real venues data.
    # num_shows should be aggregated based on number of upcoming shows per venue.
    # show_data = db.session.query(Show, Artist, Venue).filter(Show.venue_id == Venue.id, Show.artist_id == Artist.id).order_by(Show.start_time)
    # show_data = Show.query.options(db.joinedload(Show.Venue), db.joinedload(Show.Artist)).all()
    show_data = db.session.query(Show).order_by(Show.start_time)
    if not show_data:
        return render_template('errors/404.html')
    show_to_display = []
    for show_item in show_data:
        show_to_display += [{
            'venue_id': show_item.Venue.id,
            'venue_name': show_item.Venue.name,
            'artist_id': show_item.Artist.id,
            'artist_name': show_item.Artist.name,
            'artist_image_link': show_item.Artist.image_link,
            'start_time': str(show_item.start_time)
        }]
    return render_template('pages/shows.html', shows=show_to_display)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # insert form data as a new Show record in the db, instead
    # on successful db insert, flash success
    # on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    form = ShowForm(request.form)
    #if not form.validate():
    #    flash('An error occurred. Input is invalid.')
    #    return render_template('pages/home.html')
    try:
        new_show = Show(
            venue_id=request.form['venue_id'],
            artist_id=request.form['artist_id'],
            start_time=request.form['start_time']
        )
        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully listed!')
    except SQLAlchemyError:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
    finally:
        # always close the session
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
