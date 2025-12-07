from flask import Flask
from extensions import db, login_manager, bcrypt

def create_app():
    app = Flask(__name__)

    # Secret key for sessions
    app.config['SECRET_KEY'] = 'supersecretkeychangeit'

    # SQLite DB
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    # Import User model
    from models import User
    
    # Register user_loader callback
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    from routes import init_routes
    init_routes(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)