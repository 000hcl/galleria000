from flask import Flask
from flask import render_template, request, make_response, session, redirect
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL").replace("://","ql://",1)

app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)


@app.route("/", methods=["GET","POST"])
def index():
    message = " "
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        pwcheck = db.session.execute("SELECT password FROM users WHERE username=:username",{"username":username}).fetchone()
        if pwcheck == None:
            message = "Password or username invalid."
        
        elif check_password_hash(pwcheck[0],password):
            session["username"] = username
            user_id = db.session.execute("SELECT id FROM users WHERE username=:username",{"username":username}).fetchone()[0]
            session["user_id"] = user_id
            return redirect("/home")
        message = "Password or username invalid."
    return render_template("index.html",message=message)
        


@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/upload",methods=["GET","POST"])
def upload():
    if request.method == "POST":
        error = False
        file = request.files["file"]
        if not (file.filename.lower().endswith(".jpg") or file.filename.lower().endswith(".jpeg")):
            message = "File should be a jpg or jpeg file."
            error = True
        title = request.form["title"]
        if title is None:
            message = Please add a title.
            error = True
        description = request.form["description"]
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
            return redirect("/home")
    else:
        message = " "
    return render_template("upload.html",message=message)


@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        error = False
        un = request.form["username"]
        if len(un)>12 or len(un)<2:
            message = "Username must be between 2 and 12 characters long."
            error= True
        pw = request.form["password"]
        if len(pw)>24 or len(pw)<8:
            message = "Password must be between 8 and 24 characters long."
            error = True
        pw2 = request.form["password2"]
        if pw != pw2:
            message = "Passwords don't match."
            error = True
        userexists = db.session.execute("SELECT username FROM users WHERE username=:un",{"un":un}).fetchone()
        if userexists != None:
            message = "Username already exists."
            error = True
        if not error:
            hash_value = generate_password_hash(pw)
            db.session.execute("INSERT INTO users (username,password) VALUES (:un,:pw)", {"un":un,"pw":hash_value})
            db.session.commit()
            return redirect("/")
    else:
        message = " "
    return render_template("register.html",message=message)

@app.route("/home",methods=["POST", "GET"])
def home():
    id = db.session.execute("SELECT id FROM images WHERE visible=1 ORDER BY id DESC").fetchall()
    return render_template("home.html", id=id)

@app.route("/show/<int:id>")
def show(id):
    result = db.session.execute("SELECT data FROM images WHERE id=:id AND visible=1",{"id":id})
    data = result.fetchone()[0]

    response = make_response(bytes(data))
    response.headers.set("Content-Type","image/jpeg")
    return response


@app.route("/view/<int:id>",methods=["POST","GET"])

def view(id):
    visible = db.session.execute("SELECT visible FROM images WHERE id=:id",{"id":id}).fetchone()[0]
    if visible == 0:
        return redirect("/home")
    user_id = session["user_id"]
    description = db.session.execute("SELECT description FROM images WHERE id=:id",{"id":id}).fetchone()[0]
    mediums = db.session.execute("select distinct name from categories left join imagecategories on categories.id=imagecategories.catid where imagecategories.imgid=:id",{"id":id}).fetchall()
    artist = db.session.execute("select username from images left join users on users.id=images.userid where images.id=:id",{"id":id}).fetchone()[0]
    artist_id = db.session.execute("SELECT userid FROM images WHERE id=:id",{"id":id}).fetchone()[0]
    title = db.session.execute("SELECT title FROM images WHERE id=:id",{"id":id}).fetchone()[0]
    favourite = db.session.execute("SELECT * FROM favourites WHERE userid=:userid and imgid=:imgid",{"userid":user_id,"imgid":id}).fetchone()
    message = ""
    if favourite is None:
        favourite="None"
    else:
        favourite="X"
    if request.method == "POST":
        comment = request.form["comment"]
        if len(comment)<1 or len(comment)>1000:
            message = "Comment must be 1-1000 characters long."
        else:
            db.session.execute("INSERT INTO comments (userid,imgid,comment) VALUES (:userid,:imgid,:comment)",{"userid":user_id,"imgid":id,"comment":comment})
            db.session.commit()
    sql = "FROM comments left join users on comments.userid=users.id WHERE imgid=:id ORDER BY comments.id DESC"
    comments_un = db.session.execute("SELECT username "+sql,{"id":id}).fetchall()
    comments_c = db.session.execute("SELECT comment "+sql,{"id":id}).fetchall()
    comments_id = db.session.execute("SELECT comments.id "+sql,{"id":id}).fetchall()
    count = db.session.execute("SELECT COUNT(*) FROM comments WHERE imgid=:imgid",{"imgid":id}).fetchone()[0]
    return render_template("view.html",id=id,description=description,mediums=mediums,artist=artist,artist_id=artist_id,title=title,favourite=favourite,message=message,comments_un=comments_un,comments_c=comments_c,comments_id=comments_id,count=count)


@app.route("/deletecomment/<int:id>",methods=["POST"])
def deletecomment(id):
    imgid = db.session.execute("SELECT imgid FROM comments WHERE id=:id",{"id":id}).fetchone()[0]
    userid = db.session.execute("SELECT userid FROM comments WHERE id=:id",{"id":id}).fetchone()[0]
    if userid != session["user_id"]:
        return "Access denied."
    db.session.execute("DELETE FROM comments WHERE id=:id",{"id":id})
    db.session.commit()
    return redirect("/view/"+str(imgid))

@app.route("/deleteimage/<int:id>",methods=["POST"])
def deleteimage(id):
    user_id = session["user_id"]
    user = db.session.execute("SELECT userid FROM images WHERE id=:id",{"id":id}).fetchone()[0]
    if user_id != user:
        return "Access denied."
    else:
        db.session.execute("UPDATE images SET visible=0 where id=:id",{"id":id})
        db.session.commit()
        return redirect("/home")

@app.route("/searchmedium",methods=["POST","GET"])
def searchmedium():
    message=""
    if request.method == "POST":
        medium = int(request.form["medium"])
        order = request.form["sortby"]
        sql = "SELECT DISTINCT images.id FROM imagecategories LEFT JOIN images ON imagecategories.imgid=images.id WHERE visible=1 "
        sql += "AND catid=:medium "
        sql += "ORDER BY id "+order
        imgs = db.session.execute(sql,{"medium":medium}).fetchall()
        if len(imgs)==0:
            message="No matching results found."

    else:
        imgs = db.session.execute("SELECT id FROM images WHERE visible=1 ORDER BY id DESC").fetchall()
    return render_template("search.html",imgs=imgs,message=message)

@app.route("/searchtitle",methods=["POST","GET"])
def searchtitle():
    message=""
    if request.method == "POST":
        title = request.form["title"]
        title = "%"+title+"%".lower()
        order = request.form["sortby"]
        sql = "SELECT DISTINCT id FROM images WHERE visible=1 "
        sql += "AND title LIKE LOWER(:title) "
        sql += "ORDER BY id "+order
        imgs = db.session.execute(sql,{"title":title}).fetchall()
        if len(imgs)==0:
            message="No matching results found."

    else:
        imgs = db.session.execute("SELECT id FROM images WHERE visible=1 ORDER BY id DESC").fetchall()
    return render_template("searchbytitle.html",imgs=imgs,message=message)

@app.route("/favourites")
def favourites():
    message=""
    userid = session["user_id"]
    faves = db.session.execute("SELECT imgid FROM favourites LEFT JOIN images ON images.id=imgid WHERE favourites.userid=:userid AND visible=1 ORDER BY imgid DESC",{"userid":userid}).fetchall()
    if len(faves)==0:
        message="You have no favourites yet."
    return render_template("favourites.html",id=faves,message=message)

@app.route("/favourite/<int:id>",methods=["POST"])
def favourite(id):
    user_id = session["user_id"]
    fav_result = db.session.execute("SELECT * from favourites where userid=:userid and imgid=:imgid",{"userid":user_id,"imgid":id}).fetchone()
    if fav_result is None:
        db.session.execute("INSERT INTO favourites (userid,imgid) VALUES(:userid,:imgid)",{"userid":user_id,"imgid":id})
    else:
        db.session.execute("DELETE FROM favourites where userid=:userid and imgid=:imgid",{"userid":user_id,"imgid":id})
    db.session.commit()
    return redirect("/view/"+str(id))
