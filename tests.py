#!/usr/bin/env python
from datetime import datetime, timedelta
import unittest
from app import create_app, db
from app.models import User, Book 
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    ELASTICSEARCH_URL = None

class UserTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_check(self):
        u = User(username='susan')
        u.set_password('axolotl')
        self.assertFalse(u.check_password('axolotol'))
        self.assertTrue(u.check_password('axolotl'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128'))
    
    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        
        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)
    
    def test_follow_posts(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        now = datetime.utcnow()
        b1 = Book(title="the first book", author="the first author", poster=u1, time=now + timedelta(seconds=1))
        b2 = Book(title="the second book", author="the first author", poster=u2, time=now + timedelta(seconds=4))
        b3 = Book(title="the third book", author="the first author", poster=u3, time=now + timedelta(seconds=3))
        b4 = Book(title="the fourth book", author="the first author", poster=u4, time=now + timedelta(seconds=2))
        db.session.add_all([b1, b2, b3, b4])
        db.session.commit()

        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u3)
        u3.follow(u4)
        db.session.commit()

        f1 = u1.followed_books().all()
        f2 = u2.followed_books().all()
        f3 = u3.followed_books().all()
        f4 = u4.followed_books().all()
        self.assertEqual(f1, [b2, b4, b1])
        self.assertEqual(f2, [b2, b3])
        self.assertEqual(f3, [b3, b4])
        self.assertEqual(f4, [b4])

if __name__ == "__main__":
    unittest.main(verbosity=2)
    
