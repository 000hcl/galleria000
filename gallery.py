from db import db
from flask import make_response, request, session

def get_default():
    return db.session.execute("SELECT id FROM images WHERE visible=1 ORDER BY id DESC").fetchall()

def show_image(id):
    result = db.session.execute("SELECT data FROM images WHERE id=:id AND visible=1",{"id":id})
    data = result.fetchone()[0]

    response = make_response(bytes(data))
    response.headers.set("Content-Type","image/jpeg")
    return response

def search_medium():
    medium = int(request.form["medium"])
    order = request.form["sortby"]
    sql = "SELECT DISTINCT images.id FROM imagecategories LEFT JOIN images ON imagecategories.imgid=images.id WHERE visible=1 AND catid=:medium "
    sql += "ORDER BY id "+order
    return db.session.execute(sql,{"medium":medium}).fetchall()

def search_title():
    title = request.form["title"]
    title = "%"+title+"%".lower()
    order = request.form["sortby"]
    sql = "SELECT DISTINCT id FROM images WHERE visible=1 AND title LIKE LOWER(:title) ORDER BY id "+order
    return db.session.execute(sql,{"title":title}).fetchall()

def get_comments(id):
    sql = "FROM comments left join users on comments.userid=users.id WHERE imgid=:id ORDER BY comments.id DESC"
    comments_un = db.session.execute("SELECT username "+sql,{"id":id}).fetchall()
    comments_c = db.session.execute("SELECT comment "+sql,{"id":id}).fetchall()
    comments_id = db.session.execute("SELECT comments.id "+sql,{"id":id}).fetchall()
    count = db.session.execute("SELECT COUNT(*) FROM comments WHERE imgid=:imgid",{"imgid":id}).fetchone()[0]
    return (comments_un, comments_c, comments_id, count)

def find_favourite(id):
    user_id = session["user_id"]
    return db.session.execute("SELECT * FROM favourites WHERE userid=:userid and imgid=:imgid",{"userid":user_id,"imgid":id}).fetchone()

def get_mediums(id):
    return db.session.execute("""select distinct name from categories left 
    join imagecategories on categories.id=imagecategories.catid 
    where imagecategories.imgid=:id""",{"id":id}).fetchall()

def attempt_comment_return_message(id):
    comment = request.form["comment"]
    user_id = session["user_id"]
    if len(comment)<1 or len(comment)>1000:
        return "Comment must be 1-1000 characters long."
    else:
        db.session.execute("INSERT INTO comments (userid,imgid,comment) VALUES (:userid,:imgid,:comment)",{"userid":user_id,"imgid":id,"comment":comment})
        db.session.commit()
        return ""

def view(id):
    return db.session.execute("""select visible, username, 
    userid, title, description from images left join users 
    on users.id=images.userid where images.id=:id""",{"id":id}).fetchone()
