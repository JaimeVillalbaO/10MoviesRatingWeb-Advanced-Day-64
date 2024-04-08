from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY_FLASK')
Bootstrap5(app)

##CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

# # After adding the new_movie the code needs to be commented out/deleted.
# ## So you are not trying to add the same movie twice. The db will reject non-unique movie titles.
# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()

# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()

class EditMovie(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review')
    submit = SubmitField('Done')
    
    
class AddMovie(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired()])
    # review = StringField('Your Review')
    submit = SubmitField('Add Movie')


API_KEYS = '554084035051ebd422421eec71f76b49'
TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1NTQwODQwMzUwNTFlYmQ0MjI0MjFlZWM3MWY3NmI0OSIsInN1YiI6IjY1ZTY2MDQxN2YxZDgzMDBjYTIyOGIwOCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.hpi00Ji2C8qeZHy8o7bwp0VD-6H3SPB-LZyUfEanMkI'
END_POINT = 'https://api.themoviedb.org/3/search/movie'
IMG_URL = 'https://image.tmdb.org/t/p/w500'
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


@app.route("/")
def home():
    n=10
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all() #lo convierte en una lista .all()
    for movie in all_movies: 
        movie.ranking = n
        print(movie.ranking)
        db.session.commit()
        n-=1
    # result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    # all_movies = result.scalars()
    return render_template("index.html", all_movies= all_movies)


@app.route('/edit',  methods=["GET", "POST"])
def update():
    form = EditMovie()
    movie_id = request.args.get('id')
    movie_selected = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    if form.validate_on_submit():
        movie_selected.rating = float(form.rating.data)
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie = movie_selected, form = form)

@app.route('/delete',  methods=["GET", "POST"])
def delete():
    movie_id = request.args.get('id')
    movie_selected = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods=["GET", "POST"])
def add_movie():
    form = AddMovie()
    if form.validate_on_submit():
        new_movie = form.movie_title.data
        response = requests.get(url=END_POINT, headers=headers, params={'query' : new_movie,'language' : 'en'})
        data = response.json()['results']
        movies = []
        for movie in data:
            if movie['original_language'] == 'en':
                # print(f"{movie['original_title']} - {movie['release_date'].split('-')[0]}")
                # movies_list.append(movie['original_title'])
                # years_list.append(movie['release_date'].split('-')[0])             
                movies.append(movie)   
        return render_template('select.html', movies = movies)
    return render_template('add.html', form = form)

@app.route('/find', methods=["GET", "POST"] )
def find_movie():
    movie_api_id = request.args.get("id")
    END_POINT_FIND = 'https://api.themoviedb.org/3/movie'
    NEW_END_POINT = f'{END_POINT_FIND}/{movie_api_id}'
    print(NEW_END_POINT)
    response = requests.get(url=NEW_END_POINT, headers=headers)
    data = response.json()
    print(data)
    new_movie = Movie(
        title = data['title'],
        year=data["release_date"].split("-")[0],
        description = data['overview'],
        img_url = f"{IMG_URL}{data['poster_path']}",
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('home'))
    

if __name__ == '__main__':
    app.run(debug=True, ) #use_reloader=False se coloca cuando voy a agregarle un row a la tabla.
    