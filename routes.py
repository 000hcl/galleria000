from app import app

from flask import render_template, request, redirect

import users, gallery, personal


@app.route("/", methods=["GET","POST"])
def index():
    message = ""
    if request.method == "POST":
        login = users.login()
        if not login:
            message = "Password or username invalid."
        else:
            return redirect("/home")
    return render_template("index.html",message=message)

@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")

@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        message = users.attempt_register()
        if message == "":
            return redirect("/")
    else:
        message = ""
    return render_template("register.html",message=message)

@app.route("/home",methods=["POST", "GET"])
def home():
    id = gallery.get_default()
    return render_template("home.html", id=id)

@app.route("/show/<int:id>")
def show(id):
    return gallery.show_image(id)

@app.route("/searchmedium",methods=["POST","GET"])
def searchmedium():
    message=""
    if request.method == "POST":
        imgs = gallery.search_medium()
        if len(imgs)==0:
            message="No matching results found."
    else:
        imgs = gallery.get_default()
    return render_template("search.html",imgs=imgs,message=message)

@app.route("/searchtitle",methods=["POST","GET"])
def searchtitle():
    message=""
    if request.method == "POST":
        imgs = gallery.search_title()
        if len(imgs)==0:
            message="No matching results found."
    else:
        imgs = gallery.get_default()
    return render_template("searchbytitle.html",imgs=imgs,message=message)

@app.route("/favourites")
def favourites():
    message=""
    faves = personal.favourites()
    if len(faves)==0:
        message="You have no favourites yet."
    return render_template("favourites.html",id=faves,message=message)

@app.route("/favourite/<int:id>",methods=["POST"])
def favourite(id):
    personal.add_to_favourites(id)
    return redirect("/view/"+str(id))

@app.route("/deleteimage/<int:id>",methods=["POST"])
def deleteimage(id):
    personal.delete_image(id)
    return redirect("/home")

@app.route("/deletecomment/<int:id>",methods=["POST"])
def deletecomment(id):
    imgid = personal.delete_comment_return_img_id(id)
    return redirect("/view/"+str(imgid))

@app.route("/upload",methods=["GET","POST"])
def upload():
    message = ""
    if request.method == "POST":
        message = personal.upload()
        if message == "":
            return redirect("/home")
    return render_template("upload.html",message=message)

@app.route("/view/<int:id>",methods=["POST","GET"])
def view(id):
    view = gallery.view(id)
    visible = view[0]
    description = view[4]
    user = view[1]
    poster_id = view[2]
    title = view[3]
    if visible == 0:
        return redirect("/home")
    mediums = gallery.get_mediums(id)
    favourite = gallery.find_favourite(id)
    if favourite is None:
        favourite="None"
    else:
        favourite="X"
    message = ""
    if request.method == "POST":
        message = gallery.attempt_comment_return_message(id)
    comments = gallery.get_comments(id)
    comments_un = comments[0]
    comments_c = comments[1]
    comments_id = comments[2]
    count = comments[3]
    return render_template("view.html",id=id,description=description
    ,mediums=mediums,user=user,user_id=poster_id,title=title,favourite=favourite,
    message=message,comments_un=comments_un,comments_c=comments_c,comments_id=comments_id,count=count)
