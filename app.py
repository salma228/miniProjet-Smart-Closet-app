from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_from_directory, abort)
from functools import wraps
from datetime import date
import calendar as pycal
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
import database
import email_utils
import recommender  # the file containing get_outfit_recommendation

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "salma_super_secret_key_2026")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB uploads
database.initialize_db()


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*a, **kw)
    return wrapped


# ---------- auth ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        success, username, email = database.authenticate_user(
            request.form['login_input'], request.form['password'])
        if success:
            session['logged_in'] = True
            session['email'] = email
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash("Incorrect email/username or password", "error")
    return render_template('login.html')


@app.route('/signup', methods=['POST'])
def signup():
    success, message = database.register_user(
        request.form['email'], request.form['username'], request.form['password'])
    flash("Account created! Please log in." if success else message,
          "success" if success else "error")
    return redirect(url_for('login'))


@app.route('/reset', methods=['POST'])
def reset():
    action = request.form.get('action')
    email = request.form.get('reset_email')
    if action == 'send_code':
        token = database.generate_reset_token(email)
        if token:
            email_utils.send_reset_email(email, token)
            flash("Code sent! Check your email (or terminal).", "success")
        else:
            flash("Email not found.", "error")
    elif action == 'reset_password':
        success, msg = database.reset_password(
            email, request.form.get('reset_code'), request.form.get('new_password'))
        flash(msg, "success" if success else "error")
    return redirect(url_for('login'))


# ---------- stylist (main page) ----------
def render_stylist(result=None, weather=None, temp=None):
    return render_template(
        'dashboard.html', result=result, weather=weather, temp=temp,
        weather_options=database.get_weather_options(),
        closet_count=len(database.get_closet(session['email'])))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_stylist()


@app.route('/recommend', methods=['POST'])
@login_required
def recommend():
    weather = request.form.get('weather')
    try:
        temp = float(request.form['temperature'])
    except (KeyError, ValueError):
        flash("Enter a valid temperature.", "error")
        return redirect(url_for('dashboard'))
    if not weather:
        flash("Pick the weather first.", "error")
        return redirect(url_for('dashboard'))
    temp = int(temp) if temp.is_integer() else temp
    result = recommender.get_outfit_recommendation(session['email'], weather, temp)
    if result.get("error"):
        flash(result["error"], "error")
        return redirect(url_for('dashboard'))
    return render_stylist(result, weather, temp)


@app.route('/wear', methods=['POST'])
@login_required
def wear():
    ids = {c: request.form.get(f"{c.lower()}_id") for c in database.CATEGORIES}
    database.save_outfit(session['email'], request.form.get('weather'),
                         request.form.get('temperature'), ids)
    flash("Saved to your calendar.", "success")
    return redirect(url_for('calendar', m=date.today().strftime("%Y-%m"),
                            d=date.today().isoformat()))


# ---------- wardrobe / add ----------
@app.route('/wardrobe')
@login_required
def wardrobe():
    closet = database.get_closet(session['email']).to_dict('records')
    return render_template('wardrobe.html', closet=closet, categories=database.CATEGORIES)


@app.route('/add')
@login_required
def add_page():
    return render_template('add_item.html', categories=database.CATEGORIES)


@app.route('/closet/add', methods=['POST'])
@login_required
def closet_add():
    f = next((request.files[k] for k in ("image", "shot")
              if k in request.files and request.files[k].filename), None)
    ok, msg = database.add_item(session['email'], f, request.form.get('category'),
                                request.form.get('color', ''), request.form.get('name', ''))
    flash(msg, "success" if ok else "error")
    return redirect(url_for('wardrobe' if ok else 'add_page'))


@app.route('/closet/delete/<item_id>', methods=['POST'])
@login_required
def closet_delete(item_id):
    database.delete_item(session['email'], item_id)
    flash("Piece removed.", "success")
    return redirect(url_for('wardrobe'))


# ---------- calendar ----------
@app.route('/calendar')
@login_required
def calendar():
    today = date.today()
    try:
        y, m = map(int, request.args.get('m', '').split('-'))
        date(y, m, 1)
    except ValueError:
        y, m = today.year, today.month
    history = database.get_history(session['email'])
    py, pm = (y - 1, 12) if m == 1 else (y, m - 1)
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    sel = request.args.get('d')
    try:
        sel_label = date.fromisoformat(sel).strftime("%A, %B %d") if sel else None
    except ValueError:
        sel, sel_label = None, None
    return render_template(
        'calendar.html', year=y, month=m, today=today.isoformat(),
        weeks=pycal.Calendar(firstweekday=0).monthdayscalendar(y, m),
        month_label=date(y, m, 1).strftime("%B %Y"), history=history,
        cur_m=f"{y:04d}-{m:02d}", prev_m=f"{py:04d}-{pm:02d}", next_m=f"{ny:04d}-{nm:02d}",
        sel=sel, sel_label=sel_label, sel_entry=history.get(sel) if sel else None)


# ---------- profile ----------
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',
                           pieces=len(database.get_closet(session['email'])),
                           days_logged=len(database.get_history(session['email'])))


# ---------- misc ----------
@app.route('/user_image/<filename>')
@login_required
def user_image(filename):
    owned = database.get_closet(session['email'])['image_path'].astype(str).values
    if filename not in owned:
        abort(404)
    return send_from_directory(database.images_dir, filename)


@app.route('/toggle_theme', methods=['POST'])
def toggle_theme():
    session['dark_mode'] = not session.get('dark_mode', False)
    return redirect(request.referrer or url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")

