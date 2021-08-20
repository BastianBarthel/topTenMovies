from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os
import requests

FLASK_SECRET_KEY = os.environ.get("SECRET_KEY")
TMDB_API_KEY = os.environ.get("API_KEY")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_INFO_URL = "https://api.themoviedb.org/3/movie"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# CREATE APPLICATION
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
Bootstrap(app)

# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CREATE MOVIE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


# FORMS
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating", validators=[DataRequired()])
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    name = StringField("Movie Name", validators=[DataRequired()])
    submit = SubmitField("Done")


# ROUTES
@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_name = form.name.data
        data = requests.get(TMDB_SEARCH_URL, params={"api_key": TMDB_API_KEY, "query": movie_name}).json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route('/delete/<int:movie_id>')
def delete(movie_id):
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/find")
def find():
    movie_id = request.args.get("id")
    if movie_id:
        movie_url = f"{TMDB_INFO_URL}/{movie_id}"
        data = requests.get(movie_url, params={"api_key": TMDB_API_KEY}).json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{TMDB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


# RUN APPLICATION
if __name__ == '__main__':
    app.run(debug=True)
