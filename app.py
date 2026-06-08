# =========================
# app.py
# Flask 앱 생성 + Blueprint 등록
# =========================
import logging
from flask import Flask
from flask_cors import CORS

from routes.common      import bp as common_bp
from routes.recruiting  import bp as recruiting_bp
from routes.evaluations import bp as evaluations_bp
from routes.documents   import bp as documents_bp
from routes.applicants  import bp as applicants_bp
from routes.papers      import bp as papers_bp
from routes.stats       import bp as stats_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Blueprint 등록
app.register_blueprint(common_bp)
app.register_blueprint(recruiting_bp)
app.register_blueprint(evaluations_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(applicants_bp)
app.register_blueprint(papers_bp)
app.register_blueprint(stats_bp)

if __name__ == "__main__":
    app.run(debug=True)
