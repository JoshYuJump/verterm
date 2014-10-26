#! /venv/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from flask import Flask, render_template, request, session, \
                  redirect, url_for, flash
from flask.ext.script import Server, Manager, Shell
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
from flask.ext.migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, LoginManager, login_required, login_user


app = Flask(__name__)
app.debug = True
app.config['SERVER_NAME'] = 'verterm.com'
app.config['SECRET_KEY'] = \
    '\xba[\xdb9\xeb\xc8\xf6C\x11\xf5\r\xcb\x96\r/\x9cxf>\xc8|\x82$\xb5'
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql://root:123@127.0.0.1/verterm'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True


login_manager = LoginManager()
login_manager.setup_app(app)

manager = Manager(app)
server = Server(host='0.0.0.0', port=80)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', server)

sys_user_id = 1
page_row = 15
active_channel = u''

# --- data models ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(128))
    topics = db.relationship('Topic', backref='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter 
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(64))
    topic_keywords = db.Column(db.String(256))
    topic_desc = db.Column(db.Text)
    topic_alias = db.Column(db.String(64), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    Contents = db.relationship('Content', backref='content_topic', lazy='dynamic')
    Taokes = db.relationship('Taoke', backref='taoke_topic', lazy='dynamic')

    def __repr__(self):
        return '<Topic %r>' % self.topic_name

class Content(db.Model):
    __tablename__ = 'contents'
    id = db.Column(db.Integer, primary_key=True)
    content_name = db.Column(db.String(64))
    content_keywords = db.Column(db.String(256))
    content_description = db.Column(db.String(512))
    content_content = db.Column(db.Text)
    content_datetime = db.Column(db.DateTime, default=datetime.now)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'))

    def __repr__(self):
        return '<Content %r>' % self.content_name  

class Taoke(db.Model):
    __tablename__ = 'taokes'
    id = db.Column(db.Integer, primary_key=True)
    taoke_title = db.Column(db.String(256))
    taoke_image = db.Column(db.String(512))
    taoke_discount = db.Column(db.String(512))
    taoke_price = db.Column(db.Float)
    taoke_link = db.Column(db.String(4000))
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'))

    def __repr__(self):
        return '<Taoke %r>' % self.taoke_title             


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- main site views ---
@app.route('/', subdomain="<var>", methods=['GET'])
def index(var):
    if var != 'www':
        return topic(var)
    taokes = Taoke.query.order_by('id desc').limit(50)
    topics = Topic.query.order_by('id desc').limit(20)
    contents = Content.query.order_by('id desc').limit(20)
    return render_template('main/index.html', taokes=taokes, topics=topics, contents=contents)

@app.route('/content/<int:content_id>', subdomain="<var>", methods=['GET'])
def sub(content_id, var):
    return content(content_id)

# --- topic views views ---
@app.route('/topic/<topic_alias>')
@app.route('/topic/<topic_alias>/')
def topic(topic_alias):
    topic = Topic.query.filter_by(topic_alias=topic_alias).first()
    if topic is None:
        return redirect(url_for('index'))
    keywords = topic.topic_keywords.split(',')
    taokes = Taoke.query.filter_by(topic_id=topic.id)
    contents = Content.query.filter_by(topic_id=topic.id).limit(10)
    return render_template('skins/default/index.html', topic=topic, taokes=taokes, contents=contents, keywords=keywords)

@app.route('/content/<int:contend_id>')
def content(contend_id):
    content = Content.query.filter_by(id=contend_id).first()
    if content is None:
        return redirect(url_for('index'))
    topic = Topic.query.filter_by(id=content.topic_id).first()
    if topic is None:
        return redirect(url_for('index'))
    taokes = Taoke.query.filter_by(topic_id=topic.id)
    random_topics = Topic.query.order_by(func.rand()).limit(8)
    return render_template('skins/default/content.html', content=content, topic=topic, taokes=taokes, random_topics=random_topics)    

# --- dashboard views ---

@app.route('/user-panel/login', methods=['GET', 'POST'])
def user_panel_login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print password
        if username == '':
            flash(u'用户名不能为空！')
            return render_template('user-panel/login.html')

        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(u'用户名不存在！')
            return render_template('user-panel/login.html')

        # verify password
        if user.verify_password(password):
            login_user(user)
            flash(u'登录成功！')
            return redirect(url_for('user_panel'))
        else:
            flash(u'用户名和密码不匹配！')
            return render_template('user-panel/login.html')
            
    else:       
        return render_template('user-panel/login.html')


@app.route('/user-panel/')
@app.route('/user-panel/main')
@login_required
def user_panel():
    active_channel = u'概况'
    return render_template('user-panel/dashboard.html', active_channel=active_channel)

@app.route('/user-panel/topic-list')
@login_required
def user_panel_topic_list():
    active_channel = u'主题'
    page = int(request.args.get('page', '1'))
    paginate = Topic.query.paginate(page, page_row, False)
    topics = paginate.items
    return render_template('user-panel/topic-list.html', pagination=paginate, topics=topics, active_channel=active_channel)

@app.route('/user-panel/topic-edit', methods=['GET', 'POST'])
@login_required
def user_panel_topic_edit():
    active_channel = u'主题'
    if request.method == 'POST':
        topic_id = int(request.form['id'])
        if topic_id <= 0:
            topic = Topic(topic_name=request.form['topic-name'], \
                          topic_alias=request.form['topic-alias'], \
                          topic_keywords=request.form['topic-keywords'], \
                          topic_desc=request.form['topic-desc'], \
                          user_id=sys_user_id)
        else:
            topic = Topic.query.filter_by(id=topic_id).first()
            topic.topic_name = request.form['topic-name']
            topic.topic_alias = request.form['topic-alias']
            topic.topic_keywords = request.form['topic-keywords']
            topic.topic_desc=request.form['topic-desc']
        db.session.add(topic)
        db.session.commit()
        flash(u'添加成功')
        return redirect(url_for('user_panel_topic_edit'))
    else:
        topic_id = int(request.args.get('id', '0'))
        topic = Topic.query.filter_by(id=topic_id).first()
        return render_template('user-panel/topic-edit.html', topic=topic, active_channel=active_channel)

@app.route('/user-panel/topic-delete', methods=['GET', 'POST'])
@login_required
def user_panel_topic_delete():
    active_channel = u'主题'
    topic_id = int(request.args.get('id', '0'))
    topic = Topic.query.filter_by(id=topic_id).first()
    db.session.delete(topic)
    db.session.commit()
    flash(u'删除成功')
    return redirect(url_for('user_panel_topic_list'))       
    
@app.route('/user-panel/content-list')
@login_required
def user_panel_content_list():
    active_channel = u'内容'
    page = int(request.args.get('page', '1'))
    paginate = Content.query.paginate(page, page_row, False)
    contents = paginate.items
    return render_template('user-panel/content-list.html', pagination=paginate, contents=contents, active_channel=active_channel) 

@app.route('/user-panel/content-edit', methods=['GET', 'POST'])
@login_required
def user_panel_content_edit():
    active_channel = u'内容'
    topics = Topic.query.all()
    if request.method == 'POST':
        content_id = int(request.form['id'])
        if content_id <= 0:
            op_name = u"添加"
            content = Content(content_name=request.form['content-name'], \
                          content_keywords=request.form['content-keywords'], \
                          content_description=request.form['content-description'], \
                          content_content=request.form['content-content'], \
                          topic_id=request.form['topic-id'])
        else:
            op_name = u"编辑"
            content = Content.query.filter_by(id=content_id).first()
            content.content_name = request.form['content-name']
            content.content_keywords = request.form['content-keywords']
            content.content_description = request.form['content-description']
            content.content_content = request.form['content-content']
            content.topic_id = request.form['topic-id']
        db.session.add(content)
        db.session.commit()
        flash(op_name + u'成功')
        return redirect(url_for('user_panel_content_edit'))
    else:
        content_id = int(request.args.get('id', '0'))
        content = Content.query.filter_by(id=content_id).first()
        return render_template('user-panel/content-edit.html', content=content, topics=topics, active_channel=active_channel)

@app.route('/user-panel/content-delete', methods=['GET', 'POST'])
@login_required
def user_panel_content_delete():
    active_channel = u'内容'
    content_id = int(request.args.get('id', '0'))
    content = Content.query.filter_by(id=content_id).first()
    db.session.delete(content)
    db.session.commit()
    flash(u'删除成功')
    return redirect(url_for('user_panel_content_list'))                    


@app.route('/user-panel/taoke-list')
@login_required
def user_panel_taoke_list():
    active_channel = u'淘宝客'
    page = int(request.args.get('page', '1'))
    paginate = Taoke.query.paginate(page, page_row, False)
    taokes = paginate.items
    return render_template('user-panel/taoke-list.html', pagination=paginate, taokes=taokes, active_channel=active_channel)

@app.route('/user-panel/taoke-edit', methods=['GET', 'POST'])
@login_required
def user_panel_taoke_edit():
    active_channel = u'淘宝客'
    topics = Topic.query.all()
    if request.method == 'POST':
        taoke_id = int(request.form['id'])
        if taoke_id <= 0:
            taoke = Taoke(taoke_title=request.form['taoke-title'], \
                          taoke_image=request.form['taoke-image'], \
                          taoke_discount=request.form['taoke-discount'], \
                          taoke_price=request.form['taoke-price'], \
                          taoke_link=request.form['taoke-link'], \
                          topic_id=request.form['topic-id'])
        else:
            op_name = u"编辑"
            taoke = Taoke.query.filter_by(id=taoke_id).first()
            taoke.taoke_title = request.form['taoke-title']
            taoke.taoke_image = request.form['taoke-image']
            taoke.taoke_discount = request.form['taoke-discount']
            taoke.taoke_price = request.form['taoke-price']
            taoke.taoke_link = request.form['taoke-link']
            taoke.topic_id = request.form['topic-id']
        db.session.add(taoke)
        db.session.commit()
        flash(u'添加成功')
        return redirect(url_for('user_panel_taoke_edit'))
    else:
        taoke_id = int(request.args.get('id', '0'))
        taoke = Taoke.query.filter_by(id=taoke_id).first()
        return render_template('user-panel/taoke-edit.html', taoke=taoke, topics=topics, active_channel=active_channel)

@app.route('/user-panel/taoke-delete', methods=['GET', 'POST'])
@login_required
def user_panel_taoke_delete():
    active_channel = u'淘宝客'
    taoke_id = int(request.args.get('id', '0'))
    taoke = Taoke.query.filter_by(id=taoke_id).first()
    db.session.delete(taoke)
    db.session.commit()
    flash(u'删除成功')
    return redirect(url_for('user_panel_taoke_list'))       



if __name__ == '__main__':
    manager.run()
