from flask import render_template, url_for, redirect, flash
from app import app
from app.forms import LoginForm

@app.route('/')
def index():
    user = {'username' : 'Arian'}
    return render_template('index.html', title="Home", user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user %s, remember_me=%s' %(form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title=" Sign In", form=form)











