from datetime import datetime
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import BewertForm, LoginForm, RegistrationForm, EditProfileForm, \
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Rezepteintrag, Bewertung
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        titel = request.form['titel']
        rezeptbeschreibung = request.form['rezeptbeschreibung']
        zutat = request.form['zutat']
        user_id = current_user.id
        eintrag = Rezepteintrag(titel, rezeptbeschreibung, zutat, user_id)
        db.session.add(eintrag)
        db.session.commit()
        flash('Dein Rezept ist nun online!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    rezeptposts = Rezepteintrag.query.order_by(Rezepteintrag.titel.desc()).paginate(
      page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=rezeptposts.next_num) \
        if rezeptposts.has_next else None
    prev_url = url_for('index', page=rezeptposts.prev_num) \
        if rezeptposts.has_prev else None
    return render_template('index.html', title='Home', form=form, rezeptposts=rezeptposts.items, next_url=next_url, prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    formbew = EmptyForm()
    page = request.args.get('page', 1, type=int)
    rezeptposts = Rezepteintrag.query.order_by(Rezepteintrag.titel.desc()).paginate(
       page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=rezeptposts.next_num) \
        if rezeptposts.has_next else None
    prev_url = url_for('explore', page=rezeptposts.prev_num) \
    if rezeptposts.has_prev else None

    
    return render_template('index.html', title='Explore', rezeptposts=rezeptposts.items, formbew=formbew,
                           next_url=next_url, prev_url=prev_url)
     

@app.route('/bewertung/<id>', methods=['GET','POST'])
@login_required
def bewertung(id):
    rezeptid = Rezepteintrag.query.filter_by(id=id).first()
    
    form = BewertForm()
    if form.validate_on_submit():
         bewertung = request.form['bewertung']
         user_id = current_user.id
         rezepteintrag_id = rezeptid.id
         bewertungeintrag = Bewertung(bewertung, user_id, rezepteintrag_id)
         db.session.add(bewertungeintrag)
         db.session.commit()
         flash('Bewertung durchgeführt {}!'.format(rezeptid))
         return redirect(url_for('bewertung', id=rezepteintrag_id))
    return render_template('bewertung.html', title='Bewertung', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    rezeptposts = user.rezepte.order_by(Rezepteintrag.titel.desc()).paginate(
         page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=rezeptposts.next_num) \
         if rezeptposts.has_next else None
    prev_url = url_for('user', username=user.username, page=rezeptposts.prev_num) \
         if rezeptposts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, form=form, rezeptposts=rezeptposts.items,
                           next_url=next_url, prev_url=prev_url )


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


