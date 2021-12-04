from cryptography.fernet import Fernet
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, flash, make_response
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import activate_test, login_required, ocr_core, get_pw
import os

# Configure application
app = Flask(__name__)
UPLOAD_FOLDER = "/uploads"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///covid.db")

# https://stackabuse.com/pytesseract-simple-python-optical-character-recognition/
# import our OCR function

# define a folder to store and later serve the images
UPLOAD_FOLDER = "/static/uploads/"

# allow files of a specific type
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "heic"])


def allowed_file(filename):
    # https://stackabuse.com/pytesseract-simple-python-optical-character-recognition/
    # return true if is in file format and extension is a-ok
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.after_request
def after_request(response):
    """Ensure responses aren"t cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# route and function to handle the upload page


@app.route("/", methods=["GET", "POST"])
@ login_required
def ocr():
    if request.method == "POST":
        print("post ocr")
        # print("wot")
        # check if they want manual
        if request.form.get("manual") is not None:
            # switch to
            return render_template("manual.html")
        # check if okie-dokie
        # if request.form.get("normal") is None:
        #     print("normal")
        #     flash("Please use the Color website to activate your test")
        #     return render_template("ocr.html")
        # check if there is a file in the request
        if "file" not in request.files:
            flash("No file selected")
            return render_template("ocr.html")
        file = request.files["file"]
        # if no file is selected
        if file.filename == "":
            flash("No file selected1")
            return render_template("ocr.html")
        if file and allowed_file(file.filename):
            # file is a FileStorage object
            # store FileStorage into uploads folder
            storage_loc = open(f"uploads/{file.filename}", "wb")
            content = file.read()
            storage_loc.write(content)
            pathname = storage_loc.name

            # call the OCR function on it
            extr_text = ocr_core(pathname)

            # tidy up
            storage_loc.close()

            # get barcode and acc_num
            barcode = ""
            D_loc = extr_text.find("D-")
            if D_loc != -1:
                if len(extr_text[D_loc + 2:]) > 9:
                    barcode = extr_text[D_loc+2:D_loc+12]
                else:
                    barcode = extr_text[D_loc + 2:]

            acc_num = ""
            C_loc = extr_text.find("C-")
            if C_loc != -1:
                if len(extr_text[C_loc + 2:]) > 4:
                    acc_num = extr_text[C_loc+2:C_loc+7]
                else:
                    acc_num = extr_text[C_loc+2:]

            if not (barcode or acc_num):
                flash("Barcode or acc_num not found")
                return render_template("manual.html", confirmation=True)
            # Basically user makes sure their input is right
            return render_template("manual.html", barcode=barcode, acc_num=acc_num, confirmation=True)
        flash("Something went wrong...")
        return render_template("ocr.html")
    return render_template("ocr.html")


@ app.route("/manual", methods=["GET", "POST"])
@ login_required
def manual():
    print("manual...")
    if request.method == "POST":
        print("post    ")
        # return "done"
        # if they want to switch input method
        # normal check works
        if request.form.get("ocr") is not None:
            print("switch to auto")
            return render_template("ocr.html")
        # if request.form.get("normal") is None:
        #     print("manual is not normal")
        #     flash("Please use the Color website to activate your test")
        #     return render_template("manual.html")
        print("passed over the normal check")
        print(request.form.get("ocr"))
        print("passed over the normal check")
        # if not normal fill-out
        if not request.form.get("barcode") or not request.form.get("acc_num"):
            flash("One or more fields are blank that shouldn't be!")
            return render_template("manual.html")
        barcode = request.form.get("barcode")
        acc_num = request.form.get("acc_num")
        login_info = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"])
        email = login_info[0]["coloremail"]
        colorpw = login_info[0]["colorpw"]
        decrypted = get_pw(colorpw)
        activate_test(email, decrypted, barcode, acc_num)
        # # return render_template("activated.html", success=True)
        if activate_test(email, decrypted, barcode, acc_num):
            return render_template("activated.html", success=True)
        return render_template("activated.html")
    return render_template("manual.html")


@ app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        error = None

        # Ensure username was submitted
        if not request.form.get("email"):
            error = "Must provide username"

        # Ensure password was submitted
        elif not request.form.get("pw"):
            error = "Must provide password"

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE coloremail = ?",
                          request.form.get("email"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["pw"], request.form.get("pw")):
            error = "Invalid username and/or password"

        # Display error
        if error:
            flash(error)
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@ app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@ app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("coloremail")
        pw = request.form.get("pw")
        confpw = request.form.get("confpw")
        cpw = request.form.get("colorpw")
        cconfpw = request.form.get("confcolorpw")
        error = None
        # CHECKING FOR VALID INPUT
        # check for empty fields
        if not(name and email and pw and confpw and cpw and cconfpw):
            error = "All fields must be filled out"
        # pws match?
        if pw != confpw:
            error = "Password and Confirmation Password must match"
        if cpw != cconfpw:
            error = "Color Password and Color Confirmation Password must match"
        # check has letter and number
        # check for pre-existing username
        same_names = db.execute("SELECT * FROM users WHERE name = ?", name)
        if len(same_names) == 1:
            error = "Username already exists!"
        if error:
            flash(error)
            return render_template("register.html")
        pw_hash = generate_password_hash(pw)
        # encrypt pw
        cpw = cpw.encode()
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        ec_cpw = cipher_suite.encrypt(cpw)
        # add to table
        db.execute(
            "INSERT INTO users (name, coloremail, colorpw, pw) VALUES (?,?,?,?)", name, email, ec_cpw, pw_hash)
        # redirect to login
        return set_key(key)

    # if not post, get
    return render_template("register.html")


@ app.route("/setcookie", methods=["POST", "GET"])
def set_key(key):
    resp = make_response(render_template("login.html"))
    resp.set_cookie("key", key, expires=None,
                    secure=True, samesite="Strict")
    return resp


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
        return render_template(request.path, error=e)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
