from datetime import datetime
from hashlib import md5
import json
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import redis
import rq
from app import db, login


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    dataset = db.relationship('User_dataset', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
  
    def launch_AutoML(self, name, description, columns, table, analysisname, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id, columns, table, analysisname, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()
    def my_datasets(self):
        datasets = User_dataset.query.filter(self.id == User_dataset.user_id)
        return datasets.order_by(User_dataset.timestamp.desc())

    def my_subsets(self):
        subsets = Data_subset.query.join(
            User_dataset, (Data_subset.dataset_name == User_dataset.dataset)).filter(
                User_dataset.user_id == self.id).all()
        return subsets.order_by(User_dataset.id.desc())

    def my_results(self):
        results = Analysis_result.query.join(
            Data_subset, (Data_subset.subset == Analysis_result.subset_name)).join(
                User_dataset, (Data_subset.dataset_name == User_dataset.dataset)).filter(
                    User_dataset.user_id == self.id).all()
        return results.order_by(Analysis_result.id.desc())

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User_dataset(db.Model):
    __tablename__ = 'user_dataset'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dataset = db.Column(db.String(140), unique=True)
    dataset_name = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    subset = db.relationship('Data_subset', backref='user_dataset', lazy='dynamic')
    
    
    def __repr__(self):
        return '{}'.format(self.dataset_name)
    
    def my_columns(self):
        columns = Dataset_columns.query.filter(self.id == Dataset_columns.dataset_id)
    
class Data_subset(db.Model):
    __tablename__ = 'data_subset'
    id = db.Column(db.Integer, primary_key = True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('user_dataset.id'))
    dataset_name = db.Column(db.String(128))
    subset = db.Column(db.String(140))
    subset_name = db.Column(db.String(128))
    columns_subset = db.Column(db.String(256))
    target_column = db.Column(db.String(140))

    def __repr__(self):
        return '{}'.format(self.subset_name)

class Analysis_result(db.Model):
    __tablename__ = 'analysis_result'
    id = db.Column(db.Integer, primary_key = True)
    subset_id = db.Column(db.Integer, db.ForeignKey('data_subset.id'))
    subset_name = db.Column(db.String(128))
    analysis = db.Column(db.String(128))
    analysis_name = db.Column(db.String(128))
    analysis_score = db.Column(db.Float)
    analysis_model = db.Column(db.String())

    def __repr__(self):
        return '{}'.format(self.analysis_score)

class Dataset_columns(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    dataset_name = db.Column(db.String(128))
    column_name = db.Column(db.String(128))

    def __repr__(self):
        return '{}'.format(self.column_name)

class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100
