from app import app, db
from app.models import User, Rezepteintrag, Bewertung


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Rezepteintrag': Rezepteintrag, 'Bewertung': Bewertung}
