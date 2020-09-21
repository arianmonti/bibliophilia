from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app, abort
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, EmptyForm, BookForm, SearchForm, MessageForm, CommentForm
from app.models import User, Book, Rating, Message, Notification, Comment
from app.translate import translate
from app.main import bp
from werkzeug.utils import secure_filename
import os


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    books = current_user.followed_books().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=books.next_num) if books.has_next else None
    prev_url = url_for('main.index', page=books.prev_num) if books.has_prev else None
    return render_template('index.html', title=_('Home'), books=books.items, next_url=next_url, prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    books = Book.query.order_by(Book.time.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=books.next_num) if books.has_next else None
    prev_url = url_for('main.explore', page=books.prev_num) if books.has_prev else None
    return render_template('index.html', title=_('Explore'), books=books.items, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    books = user.books.order_by(Book.time.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=books.next_num) if books.has_next else None
    prev_url = url_for('main.user', username=user.username, page=books.prev_num) if books.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, books=books.items, next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about = form.about.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about.data = current_user.about
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({
        'text': translate(
            request.form['text'],
            request.form['source_language'],
            request.form['dest_language']
        )
    })

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    books, total = Book.search(g.search_form.q.data, page,
                                current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), books=books,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(message)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'), form=form, recipient=recipient)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(Message.time.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.messages', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) if messages.has_prev else None
    return render_template('messages.html', messages=messages.items, next_url=next_url, prev_url=prev_url)

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


@bp.route('/new_book/', methods=['GET', 'POST'])
@login_required
def new_book():
    form = BookForm()
    if form.validate_on_submit():
        language = guess_language(form.description.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        book = Book(description=form.description.data, isbn=form.isbn.data, title=form.title.data, author=form.author.data, poster=current_user, language=language)
        db.session.add(book)
        db.session.commit()
        f = form.photo.data
        # filename = secure_filename(f.filename)
        f.save(os.path.join(current_app.static_folder, 'book_covers', str(book.id))) if f else None
        flash(_('Your book is now live!'))
        return redirect(url_for('main.index'))
    return render_template('new_book.html', title=_('New Book'), form=form)

@bp.route('/edit_book/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    form = BookForm()
    book = Book.query.filter_by(id=id).first_or_404()
    if current_user != book.poster:
        abort(404)
    if form.validate_on_submit():
        language = guess_language(form.title.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        book.isbn = form.isbn.data
        book.title = form.title.data
        book.author = form.author.data
        book.description = form.description.data
        book.language = language
        if form.photo.data:
            f = form.photo.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(current_app.static_folder, 'book_covers', str(book.id)))
        db.session.commit()
        flash(_('Your book edited'))
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.isbn.data = book.isbn
        form.title.data = book.title
        form.author.data = book.author
        form.description.data = book.description
    return render_template('edit_book.html', title=_('Edit Book'), form=form)


@bp.route('/book/<int:id>', methods=['GET', 'POST'])
def book(id):
    book = Book.query.get_or_404(id)
    current_rating = Rating.query.filter_by(author=current_user, book=book).first()
    form = CommentForm()
    if form.validate_on_submit():
        language = guess_language(form.body.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        comment = Comment(body=form.body.data, book=book, author=current_user._get_current_object(), language=language)
        comment.save()
        flash('Your comment has been published.')
        return redirect(url_for('main.book', id=book.id, page=1))
    page = request.args.get('page', 1, type=int)
    comments = book.comments.order_by(Comment.time.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    comments_count = book.comments.count()
    next_url = url_for('main.book', id=book.id, page=comments.next_num) if comments.has_next else None
    prev_url = url_for('main.book', id=book.id, page=comments.prev_num) if comments.has_prev else None
    return render_template('book.html', title=_('book'), comments_count=comments_count, books=[book], form=form, comments=comments.items, prev_url=prev_url, next_url=next_url)


@bp.route('/edit_comment/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_comment(id):
    form = CommentForm()
    comment = Comment.query.filter_by(id=id).first_or_404()
    if current_user != comment.author:
        abort(404)
    if form.validate_on_submit():
        language = guess_language(form.body.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        comment.body = form.body.data
        comment.language = language
        db.session.commit()
        flash(_('Your comment edited'))
        return redirect(url_for('main.book', id=comment.book_id))
    elif request.method == 'GET':
        form.body.data = comment.body
    return render_template('edit_comment.html', title=_('Edit Comment'), form=form)


@bp.route('/comment/<int:id>', methods=['GET', 'POST'])
def comment(id):
    comment = Comment.query.get_or_404(id)
    parents = comment.get_parents(comment)
    parent_book = Book.query.filter_by(id=parents[0].book_id)
    form = CommentForm()
    if form.validate_on_submit():
        language = guess_language(form.body.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        comment_reply = Comment(body=form.body.data, parent=comment, author=current_user._get_current_object(), language=language)
        comment_reply.save()
        flash('Your comment has been published.')
        return redirect(url_for('main.comment', id=comment.id, page=1))
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(id=comment.id).first().replies.paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    comments_count = Comment.query.filter_by(id=comment.id).first().replies.count()
    next_url = url_for('main.comment', id=comment.id, page=comments.next_num) if comments.has_next else None
    prev_url = url_for('main.comment', id=comment.id, page=comments.prev_num) if comments.has_prev else None
    return render_template('comment.html', title=_('comment'), parent_book=parent_book, parents=parents, comments_count=comments_count, comment=[comment], form=form, comments=comments.items, prev_url=prev_url, next_url=next_url)


@bp.route('/echo', methods=['POST'])
def hello():
    rate_updating = request.json['rating']
    book = Book.query.filter_by(id=request.json['book']).first()
    rating = Rating.query.filter_by(author=current_user, book=book).first()
    if rating:
        rating.score = rate_updating
    else:
        new_rating = Rating(author=current_user._get_current_object(), book=book, score=rate_updating)
        db.session.add(new_rating)
        db.session.commit()
    db.session.commit()
    return redirect(url_for('main.book', id=book.id))
