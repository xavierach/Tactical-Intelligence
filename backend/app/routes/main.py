from flask import Blueprint

main_bp = Blueprint("main", __name__)

@main_bp.route("/api/hello")
def hello():
    return {"message": "Hello from Flask"}