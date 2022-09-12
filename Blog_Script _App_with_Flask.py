from flask import Flask, url_for, render_template, request, redirect, session
import sqlite3 as sql3
from datetime import datetime
import timeago
from slugify import slugify
import hashlib


app = Flask(__name__)
app.secret_key = b'b\xf9\xd5\xee\xc2\xb2\xf2^`\x1fBM\xbd%`0'

def md5(strVal):
    return hashlib.md5(strVal.encode()).hexdigest()


def categories():
    sql = 'SELECT * FROM categories ORDER BY category_name ASC'
    db = sql3.connect('blog.db')
    dbCursor = db.cursor()
    dbCursor.execute(sql)
    cats = dbCursor.fetchall()

    return cats


def hasPost(url):
    sql = 'SELECT post_id FROM posts WHERE post_url = ?'
    db = sql3.connect('blog.db')
    dbCursor = db.cursor()
    dbCursor.execute(sql, (url,))
    post = dbCursor.fetchone()

    return post


def timeAgo(date):
    return timeago.format(date, datetime.now(), 'en')


app.jinja_env.globals.update(categories = categories)
app.jinja_env.filters['timeAgo'] = timeAgo


@app.route('/', methods = ['GET','POST'])
def home():
    db = sql3.connect('blog.db')
    dbCursor = db.cursor()
    #sql = 'SELECT * FROM posts ORDER BY post_id DESC' # sorts from largest to smallest DESC, ASC from smallest to largest
    sql = 'SELECT * FROM posts \
        INNER JOIN users ON users.user_id = posts.post_user_id \
        INNER JOIN categories ON categories.category_id = posts.post_category_id \
        ORDER BY post_id DESC'
    dbCursor.execute(sql)
    posts = dbCursor.fetchall()
    return render_template('index.html', posts = posts)


@app.route('/category/<string:url>')
def category(url):
    db = sql3.connect('blog.db')
    dbCursor = db.cursor()
    sql = 'SELECT * FROM categories WHERE category_url = ?'
    dbCursor.execute(sql, (url,))
    category_ = dbCursor.fetchone()
    
    if category_:
        sql_ = 'SELECT * FROM posts \
        INNER JOIN users ON users.user_id = posts.post_user_id \
        INNER JOIN categories ON categories.category_id = posts.post_category_id \
        WHERE post_category_id = ? \
        ORDER BY post_id DESC'
        dbCursor.execute(sql_, (category_[0], ))
        posts = dbCursor.fetchall()
        return render_template('category.html', category_ = category_, posts = posts)

    else:
        return redirect(url_for('home'))


@app.route('/login', methods = ['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    error = ''
    if request.method == 'POST':
        if request.form['email'] == '':
            error = 'Specify Your Email Address.'
        elif request.form['password'] == '':
            error = 'Specify Your Password.'
        else:
            db = sql3.connect('blog.db')
            dbCursor = db.cursor() 
            sql = 'SELECT * FROM users WHERE user_email = ? and user_password = ?'
            dbCursor.execute(sql, (request.form['email'],md5(request.form['password']), ))

            user = dbCursor.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('home'))
            else:
                error = 'The user for the information you entered could not be found.'


    return render_template('login.html', error = error)
 

@app.route('/register', methods = ['GET','POST'])
def register():
    error = ''
    if request.method == 'POST':
        if request.form['username'] == '':
            error = 'Specify your Name and Surname.'
        elif request.form['email'] == '':
            error = 'Specify your E-mail Address.'
        elif request.form['password'] == '' or request.form['re_password'] == '':
            error = 'Specify your Password.'
        elif request.form['password'] != request.form['re_password']:
            error = 'The passwords you entered do not match.'
        else:
            db = sql3.connect('blog.db')
            dbCursor = db.cursor()
            dbCursor.execute('''INSERT INTO users(user_name,user_email,user_password) VALUES(?,?,?)''', [request.form['username'],request.form['email'],md5(request.form['password'])])

            db.commit()

            if dbCursor.rowcount:
                session['user_id'] = dbCursor.lastrowid
                return redirect(url_for('home'))
            else:
                error = 'Your registration could not be created due to a technical problem.'

    return render_template('register.html', error = error)
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/post/<string:url>')
def post(url):
    if 'user_id' in session:
        sql = 'SELECT * FROM posts \
            INNER JOIN users ON users.user_id = posts.post_user_id \
            INNER JOIN categories ON categories.category_id = posts.post_category_id \
            WHERE post_url = ?'

        db = sql3.connect('blog.db')
        dbCursor = db.cursor()
        dbCursor.execute(sql, (url,))
        post = dbCursor.fetchone()
        if post:
            return render_template('post.html', post = post)
        else:
            return redirect(url_for('home'))
    else:
        return 'In order to see the content, if you have an account, do not log in. If you do not, please register.'


@app.route('/new-post', methods = ['GET','POST'])
def newPost():
    error = ''
    if request.method == 'POST':
        if request.form['title'] == '':
            error = 'Specify the Article Title.'
        elif request.form['category_id'] == '':
            error = 'Specify the Article Category.'
        elif request.form['content_'] == '':
            error = 'Write Article Content'
        elif hasPost(slugify(request.form['title'])):
            error = 'The article is already attached, try another article.'
        else:
            db = sql3.connect('blog.db')
            dbCursor = db.cursor()
            dbCursor.execute('''INSERT INTO posts(post_title,post_url,post_content,post_user_id,post_category_id) VALUES(?,?,?,?,?)''', [request.form['title'],slugify(request.form['title']),request.form['content_'],session['user_id'],request.form['category_id']])

            db.commit()

            if dbCursor.rowcount:
                return redirect(url_for('post', url = slugify(request.form['title'])))
            else:
                error = 'Your article could not be added due to a technical problem.'


    return render_template('new-post.html', error = error)


@app.route('/post/update/<string:id>')
def update(id):
    global id_ 
    id_ = id
    if 'user_id' in session:
        return render_template('update-post.html')
    else:
        return 'To Update, If You Have an Account, Login, If Not, Register.'


@app.route('/post/update/result', methods = ['GET','POST'])
def updateResult():
    month = ''
    if request.method == 'POST':
        if request.form['title'] == '':
            error = 'Specify the Article Title.'
        elif request.form['category_id'] == '':
            error = 'Specify the Article Category.'
        elif request.form['content_'] == '':
            error = 'Write Article Content'
        #elif hasPost(slugify(request.form['title'])):
        #    error = 'The article is already attached, try another article.'
        else:
            db = sql3.connect('blog.db')
            dbCursor = db.cursor()
            sql = 'UPDATE posts SET post_title = ? , post_url = ? , post_content = ?, post_user_id = ?, post_category_id = ?, post_date = ? WHERE post_id = ?'
            if int(datetime.now().month) < 10:
                month = '0' + str(datetime.now().month)
            else:
                month = str(datetime.now().month)
            dateYearMonthDay = [str(datetime.now().year),month,str(datetime.now().day)]
            dateHourMinuteSecond = [str(datetime.now().hour),str(datetime.now().minute),str(datetime.now().second)]

            dateYearMonthDayRes = '-'.join(dateYearMonthDay)
            dateHourMinuteSecondRes = ':'.join(dateHourMinuteSecond)

            allResult = dateYearMonthDayRes + ' ' + dateHourMinuteSecondRes

            dbCursor.execute(sql, [request.form['title'],slugify(request.form['title']),request.form['content_'],session['user_id'],request.form['category_id'],str(allResult.strip()) ,id_])
            db.commit()

            if dbCursor.rowcount:
                return redirect(url_for('post', url = slugify(request.form['title'])))
            else:
                error = 'Your article could not be added due to a technical problem.'
                return error
        if error:
            return error
                
        return redirect(url_for('home'))
     

@app.route('/post/delete/<string:id_>')
def postDelete(id_):
    if 'user_id' in session:
        db = sql3.connect('blog.db')
        dbCursor = db.cursor()
        sqlDeleteQuery = 'DELETE from posts where post_id = ?'
        dbCursor.execute(sqlDeleteQuery, (id_,))
        db.commit()
        return redirect(url_for('home'))
    
    else:
        return 'To delete, if you have an account, log in, if not, register.'


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('not-found.html'), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)

