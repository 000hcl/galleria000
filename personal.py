from db import db
from flask import session, request

def favourites():
    userid = session["user_id"]
    return db.session.execute("""SELECT imgid FROM favourites LEFT JOIN images
     ON images.id=imgid WHERE favourites.userid=:userid 
     AND visible=1 ORDER BY imgid DESC"""
    ,{"userid":userid}).fetchall()

def add_to_favourites(id):
    user_id = session["user_id"]
    fav_result = db.session.execute("SELECT * from favourites where userid=:userid and imgid=:imgid",{"userid":user_id,"imgid":id}).fetchone()
    if fav_result is None:
        db.session.execute("INSERT INTO favourites (userid,imgid) VALUES(:userid,:imgid)",{"userid":user_id,"imgid":id})
    else:
        db.session.execute("DELETE FROM favourites where userid=:userid and imgid=:imgid",{"userid":user_id,"imgid":id})
    db.session.commit()

def delete_image(id):
    user_id = session["user_id"]
    user = db.session.execute("SELECT userid FROM images WHERE id=:id",{"id":id}).fetchone()[0]
    db.session.execute("UPDATE images SET visible=0 where id=:id",{"id":id})
    db.session.commit()

def delete_comment_return_img_id(id):
    imgid = db.session.execute("SELECT imgid FROM comments WHERE id=:id",{"id":id}).fetchone()[0]
    db.session.execute("DELETE FROM comments WHERE id=:id",{"id":id})
    db.session.commit()
    return imgid

def upload():
    message = ""
    error = False
    file = request.files["file"]
    if not (file.filename.lower().endswith(".jpg") or file.filename.lower().endswith(".jpeg")):
        message = "File should be a jpg or jpeg file."
        error = True
    title = request.form["title"]
    if title == "":
        message = "Please add a title."
        error = True
    description = request.form["description"]
    if description == "":
        message = "Please write a description."
        error = True
    data = file.read()
    if len(data)>1000*1024:
        message = "File is too big. Maximum dimensions are 1000x1024 pixels."
        error = True
    mediums = request.form.getlist("medium")
    userid =session["user_id"]
    if not error:
        sql = "INSERT INTO images (title,data,description,userid,visible) VALUES (:title,:data,:description,:userid,1)"
        db.session.execute(sql, {"title":title,"data":data,"description":description,"userid":userid})
        image_id = db.session.execute("SELECT currval(pg_get_serial_sequence('images','id'))").fetchone()[0]
        for m in mediums:
            db.session.execute("INSERT INTO imagecategories (imgid,catid) VALUES (:imgid,:catid)",{"imgid":image_id,"catid":m})
        db.session.commit()
    return message
