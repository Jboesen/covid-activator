from cryptography.fernet import Fernet
from cs50 import SQL
from datetime import datetime, timedelta
from flask import Flask, redirect, render_template, request, session, flash, make_response
from flask_session import Session
import smtplib
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import activate_test, login_required, ocr_core, get_pw, message, read_text

# Configure application
app = Flask(__name__)
UPLOAD_FOLDER = "/uploads"

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SECURITY_EMAIL_SENDER"] = "colorautomator@gmail.com"
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
        # check if they want manual
        if request.form.get("manual") is not None:
            # switch to
            return render_template("manual.html")
        # check if okie-dokie
        # like I said in the html, this is finnicky so I am holding off on putting it in there
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
            flash("No file selected")
            return render_template("ocr.html")
        if file and allowed_file(file.filename):
            # file is a FileStorage object
            # store FileStorage into uploads folder
            storage_loc = open(f"uploads/{file.filename}", "wb")
            content = file.read()
            storage_loc.write(content)
            # call the OCR function on it
            pass_filename = ocr_core(storage_loc.name)
            print(pass_filename)
            storage_loc.close()
            flash("Loading...")
            print("ab to render manual")
            return redirect(f"/manual?pass_filename={pass_filename}")
            return render_template("ocr.html")
        flash("Something went wrong...")
        return render_template("ocr.html")
    return render_template("ocr.html")


@ app.route("/manual", methods=["GET", "POST"])
@ login_required
def manual():
    print("manual...")
    if request.args.get("pass_filename"):
        pass_filename = str(request.args.get("pass_filename"))
    else:
        pass_filename = ""
        print("No pass_filename")
    print(pass_filename)
    if request.method == "POST":
        print("manual post")
        # if they want to switch input method
        if request.form.get("ocr") is not None:
            return render_template("ocr.html")
        # if request.form.get("normal") is None:
        #     print("manual is not normal")
        #     flash("Please use the Color website to activate your test")
        #     return render_template("manual.html")
        # if not normal fill-out
        # if missing field
        if not request.form.get("barcode") or not request.form.get("acc_num"):
            flash("One or more fields are blank that shouldn't be!")
            return render_template("manual.html")
        barcode = request.form.get("barcode")
        acc_num = request.form.get("acc_num")
        # gather color login info
        login_info = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"])
        email = login_info[0]["coloremail"]
        colorpw = login_info[0]["colorpw"]
        decrypted = get_pw(colorpw)
        # pass to Color and check that it worked
        if activate_test(email, decrypted, barcode, acc_num):
            return render_template("activated.html", success=True)
        # otherwise it did not work
        return render_template("activated.html")

    if len(pass_filename) != 0:
        print("Finish ocr called")
        extr_text = read_text(pass_filename)
        print("extr texted")
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

        print("after finding")
        print(acc_num)
        print(barcode)
        if not (barcode or acc_num):
            flash("Barcode or acc_num not found")
            return render_template("manual.html", confirmation=True)
        print("after if")
        # Basically user makes sure their input is right
        flash("Done!")
        return render_template("manual.html", barcode=barcode, acc_num=acc_num, confirmation=True)
    return render_template("manual.html")


@ app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        error = None

        if request.form.get("del") is not None:
            return redirect("/delete")

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
        # error checks are done, tell user what we found
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


@ app.route("/delete", methods=["GET", "POST"])
def delete():
    """Log user in"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        error = None
        em = request.form.get("coloremail")

        # Ensure username was submitted
        if not request.form.get("name"):
            error = "Must provide name"

        # Ensure password was submitted
        elif not em:
            error = "Must provide email"

        # Query database for username
        print("Email: " + str(request.form.get("coloremail")))
        print("name: " + str(
            request.form.get("name")))
        rows = db.execute("SELECT * FROM users WHERE coloremail = ? AND name = ?",
                          em, request.form.get("name"))

        # Display error
        if error:
            flash(error)
            return render_template("delete.html")
        if len(rows) != 0:
            hash = db.execute(
                "SELECT pw FROM users WHERE coloremail = ?", em)[0]["pw"]
            smtp = smtplib.SMTP('smtp.gmail.com', 587)
            smtp.starttls()

            # Login with email and password
            smtp.login("colorautomator@gmail.com", "gCixxinECi4xZpF")
            smtp.send
            # send confirmation
            message(smtp, "Account Deletion",
                    f"Click this link to delete your Color Automator Account: https://color-automator.herokuapp.com/delete_confirmed?id={hash}&em={em}", em)
            flash("Click the link we sent to you to complete deletion.")
            return render_template("delete.html")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("delete.html")


@ app.route("/delete_confirmed", methods=["GET"])
def delete_confirm():
    db.execute("DELETE FROM users WHERE pw = ?", request.args.get("id"))
    # check that acct is no longer in table
    test_query = db.execute(
        "SELECT * FROM users WHERE pw = ? and coloremail = ?", request.args.get("id"), request.args.get("em"))
    if not test_query:
        flash("Successfully deleted account")
        return render_template("login.html")
    else:
        flash("Something went wrong")
        return render_template("delete.html")


@ app.route("/setcookie", methods=["POST", "GET"])
def set_key(key):
    # https://stackoverflow.com/questions/26613435/python-flask-not-creating-cookie-when-setting-expiration
    resp = make_response(render_template("login.html"))
    now = datetime.now()
    # set cookie to expire four years from now (just a far-future date so it doesn't expire w session)
    expire_date = now + timedelta(days=365*4)
    resp.set_cookie("key", key, expires=expire_date,
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
