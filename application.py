import os, requests

from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from markupsafe import escape
from datetime import date, datetime
from json import dumps

app = Flask(__name__)
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = os.urandom(16)
app.debug = True
socketio = SocketIO(app)

# Data memory storage
users = []
channel = "CVzap"
messages = []


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


@app.route("/")
def index():
    """ If no user, display login screen (username only, no password required). Otherwise, goes to channel selection """
    if "username" in session:
        return render_template(
            "index.html", messages=messages, user=session["username"], channel=channel,
        )
    return redirect("login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = escape(request.form["username"])
        if username == "" or len(username) < 3:
            return """
                <form method="post">
                    <p>Your username must be at least 3 characters!</p>
                    <p><input type=text name=username> You need a valid name!
                    <p><input type=submit value=Login>
                </form>
            """
        session["username"] = username
        users.append(username)
        return redirect(url_for("index"))
    return """
        <form method="post">
            <p>Your username must be at least 3 characters!</p>
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    """


@app.route("/logout")
def logout():
    # remove the username from the session if it's there
    session.pop("username", None)
    return redirect(url_for("index"))


@app.route("/channel")
def create_channel():
    """ Here the user can create a channel. """
    pass


@socketio.on("connect")
def connect_handler():
    if "username" in session:
        emit(
            "my response",
            {"message": "{0} has joined".format(session["username"])},
            broadcast=True,
        )
    else:
        return False  # not allowed here


@socketio.on("message sent")
def new_message(message):
    """ Handles users sending messages, if more than 100, the channel should drop older messages to create space """
    print(message)
    new_message = message["message"]
    user = session["username"]
    now = dumps(datetime.now(), default=json_serial)
    print(new_message, now)
    messages.append([user, new_message, now])
    emit("new message", messages, broadcast=True)


# Adapted from https://flask-socketio.readthedocs.io/en/latest/
# Handles the default namespace
@socketio.on_error()
def error_handler(e):
    print(e)


# handles the '/chat' namespace
@socketio.on_error("/chat")
def error_handler_chat(e):
    print(e)


# handles all namespaces without an explicit error handler
@socketio.on_error_default
def default_error_handler(e):
    print(request.event["message"])  # "my error event"
    print(request.event["args"])  # (data,)


if __name__ == "__main__":
    socketio.run(app)
