from requests import get
from json import loads
from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask("LeetBoard")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    bio = db.Column(db.Text)
    username = db.Column(db.String, unique=True)
    dp = db.Column(db.String)
    rank = db.Column(db.Integer, default=5000000)
    change = db.Column(db.Integer, default=0)
    country = db.Column(db.String(16), nullable=True)
    solutions = db.Column(db.Text, nullable=True)
    update = db.Column(db.DateTime, default=datetime.utcnow)
    
    def rank_formated(user):
        r_rank = str(user.rank)[::-1]
        f_rank = ""
        for i in range(len(r_rank)):
            if i and not i % 3:
                f_rank = "," + f_rank
            f_rank = r_rank[i] + f_rank
        return f_rank
     
    def __lt__(user, other):
        return not user.rank < other.rank
    
    def __gt__(user, other):
        return not user.rank > other.rank

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    rank = db.Column(db.Integer)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    
    @classmethod
    def _for(history, username):
        return history.query.filter_by(username=username).order_by(history.date).all()

def leetcode_profile(username):
    if username in lcrr:
        return None
    url = "https://leetcode.com/" + username
    page = get(url)
    if not page.ok:
        return None
    page = page.text
    user = page[page.find("\"profile\":")+10:page.find("\"profile\":") + page[page.find("\"profile\":"):].find("}")+1]
    page = page[page.find(user)-1000:page.find(user)+1000]
    #solutions = page[page.find("{\"matchedUser\":")+15:page.find("{\"matchedUser\":") + page[page.find("{\"matchedUser\":"):].find("}")+2]
    #solutions of the user will be added in soon
    user = loads(user)
    return user

lcrr = {
    'acounts', 'assessment', 'bugbounty',
    'business', 'contest', 'discuss',
    'explore', 'jobs', 'playground',
    'privacy', 'problems', 'problemset',
    'region', 'store', 'student',
    'submissions', 'subscribe', 'subscription',
    'support', 'terms',
}


@app.route("/")
def _home():
    users = User.query.order_by(User.rank).all()
    msg = request.args.get("msg")
    return render_template("home.html", users=users, History=History, msg=msg)

@app.route("/update")
def _update():
    id = request.args.get("id")
    try:
        id = int(id)
    except:
        return redirect("/?msg=invalid user id")
    user = User.query.filter_by(id=id).first()
    if not user:
        return redirect("/")
    if user.update > datetime.utcnow() - timedelta(days=1):
        return redirect("/?msg=Profile Already Updated within a day")
    fetched = leetcode_profile(user.username)
    user.change = user.rank - fetched["ranking"]
    user.rank = fetched["ranking"]
    user.dp = fetched["userAvatar"]
    user.name = fetched["realName"]
    user.bio = fetched["aboutMe"]
    user.country = fetched["countryName"]
    user.update = datetime.utcnow()
    
    db.session.add(History(username=user.username, rank=user.rank))
    
    db.session.commit()
    return redirect("/?msg=Profile updated succesfuly#" + user.username)

@app.route("/-add", methods=["POST"])
def _add():
    username = request.form.get("username")
    if not username:
        return redirect("/")
    username = username.strip().replace("@", "").replace("/", "").lower()
    if user := User.query.filter_by(username=username).first():
        return redirect("/update?id=" + str(user.id))
    fetched = leetcode_profile(username)
    if not fetched:
        return redirect("/?msg=User not found")
    user = User(
        username = username,
        rank = fetched["ranking"],
        dp = fetched["userAvatar"],
        name = fetched["realName"],
        bio = fetched["aboutMe"],
        country = fetched["countryName"],
    )
    db.session.add(History(username=user.username, rank=user.rank))
    db.session.add(user)
    db.session.commit()
    return redirect("/?msg= " + username + "'s Profile added!!#" + username)

if __name__ == "__main__":
    app.run(debug=True)