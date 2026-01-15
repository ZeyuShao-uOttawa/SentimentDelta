from flask import Flask
from logger import get_logger
from jobs import setup_scheduler

def create_app():
    app = Flask(__name__)
    
    # Setup scheduler and jobs
    setup_scheduler(app)
    
    # Standard blueprint registration
    from api import health_bp
    app.register_blueprint(health_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Note: app.run() only starts the web server, NOT the cron jobs.
    # The cron jobs are run by the system cron daemon independently.
    app.run(debug=False, host='0.0.0.0', port=3000)
