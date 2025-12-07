from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models import User, Simulation
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import io, base64

def init_routes(app):

    @app.route("/")
    @login_required
    def home():
        return render_template("home.html")


    @app.route("/dashboard")
    @login_required
    def dashboard():
        # Quick stats for the logged-in user
        total = Simulation.query.filter_by(user_id=current_user.id).count()
        last_sim = Simulation.query.filter_by(user_id=current_user.id).order_by(Simulation.id.desc()).first()
        recent = Simulation.query.filter_by(user_id=current_user.id).order_by(Simulation.id.desc()).limit(5).all()
        return render_template("dashboard.html", total=total, last_sim=last_sim, recent=recent)


    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")

            user = User(username=username, email=email)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash("Account created!", "success")
            login_user(user)
            return redirect(url_for("dashboard"))


        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        # If already logged in, don't show the login page
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("dashboard"))
            else:
                flash("Login failed!", "danger")

        return render_template("login.html")


    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("login"))
    
    @app.route("/montecarlo")
    @login_required
    def montecarlo():
        return render_template("montecarlo.html")
    
    @app.route("/simulate", methods=["POST"])
    @login_required
    def simulate():
        # Get form inputs
        s0 = float(request.form['s0'])
        sigma = float(request.form['sigma'])
        T = 1          # 1 year
        r = 0.05       # risk-free rate

        # Monte Carlo Simulation (1000 runs)
        n_simulations = 1000
        Z = np.random.standard_normal(n_simulations)
        prices = s0 * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)

        # Average Price
        avg_price = np.mean(prices)

        # Save to DB
        sim = Simulation(
            user_id=current_user.id,
            s0=s0,
            sigma=sigma,
            average_price=avg_price
        )
        db.session.add(sim)
        db.session.commit()

        # Generate 5 random paths for chart
        n_steps = 252  # trading days
        paths = []
        for _ in range(5):
            dt = T/n_steps
            path = [s0]
            for _ in range(n_steps):
                Z = np.random.standard_normal()
                S_prev = path[-1]
                S_new = S_prev * np.exp((r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
                path.append(S_new)
            paths.append(path)

        # Plot paths
        fig, ax = plt.subplots()
        for path in paths:
            ax.plot(path)
        ax.set_title("5 Random Monte Carlo Paths")
        ax.set_xlabel("Days")
        ax.set_ylabel("Price")

        # Convert plot to base64
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

        return render_template("results.html", avg_price=avg_price, plot_url=plot_url)
    
    @app.route("/history")
    @login_required
    def history():
        # Get all simulations for the current user, most recent first
        sims = Simulation.query.filter_by(user_id=current_user.id).order_by(Simulation.id.desc()).all()
        return render_template("history.html", simulations=sims)


