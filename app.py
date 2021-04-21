from flask import Flask
from flask import render_template, request, make_response, session, redirect
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
#.replace("://","ql://",1)

app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)


@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        pwcheck = db.session.execute("SELECT password FROM users WHERE username=:username",{"username":username}).fetchone()
        if pwcheck == None:
            return "Password or username invalid."
        if check_password_hash(pwcheck[0],password):
            session["username"] = username
            user_id = db.session.execute("SELECT id FROM users WHERE username=:username",{"username":username}).fetchone()[0]
            session["user_id"] = user_id
            return redirect("/home")
        return "Password or username invalid."


@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/upload")
def upload():
    return render_template("upload.html")


@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "GET":
       return render_template("register.html")
    if request.method == "POST":
        un = request.form["username"]
        if len(un)>12 or len(un)<2:
            return "Username must be between 2 and 12 characters long."
        pw = request.form["password"]
        if len(pw)>24 or len(pw)<8:
            return "Password must be between 8 and 24 characters long."
        pw2 = request.form["password2"]
        if pw != pw2:
            return "Passwords don't match."
        userexists = db.session.execute("SELECT username FROM users WHERE username=:un",{"un":un}).fetchone()
        if userexists != None:
            return "Username already exists."
        hash_value = generate_password_hash(pw)
        db.session.execute("INSERT INTO users (username,password) VALUES (:un,:pw)", {"un":un,"pw":hash_value})
        db.session.commit()
        return redirect("/")

@app.route("/home",methods=["POST", "GET"])
def home():
    id = db.session.execute("SELECT id FROM images").fetchall()
    count = db.session.execute("SELECT COUNT(*) FROM images").fetchone()[0]
    return render_template("home.html", id=id, count=count)

@app.route("/send",methods=["POST"])
def send():
    file = request.files["file"]
    title = request.form["title"]
    description = request.form["description"]
    data = file.read()
    mediums = request.form.getlist("medium")

    userid =session["user_id"]
    sql = "INSERT INTO images (title,data,description,userid) VALUES (:title,:data,:description,:userid)"
    db.session.execute(sql, {"title":title,"data":data,"description":description,"userid":userid})
    image_id = db.session.execute("SELECT currval(pg_get_serial_sequence('images','id'))").fetchone()[0]
    for m in mediums:
        db.session.execute("INSERT INTO imagecategories (imgid,catid) VALUES (:imgid,:catid)",{"imgid":image_id,"catid":m})
    db.session.commit()
    return redirect("/home")
@app.route("/show/<int:id>")

def show(id):
    result = db.session.execute("SELECT data FROM images WHERE id=:id",{"id":id})
    data = result.fetchone()[0]

    response = make_response(bytes(data))
    response.headers.set("Content-Type","image/jpeg")
    return response


@app.route("/view/<int:id>",methods=["POST","GET"])

def view(id):
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


@app.route("/deletecomment/<int:id>",methods=["GET"])
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
        db.session.execute("DELETE FROM images where userid=:id",{"id":id})
        db.session.commit()
        return redirect("/home")




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
