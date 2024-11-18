from database.db_setup import db

class Player(db.Model):
    __tablename__ = 'players'
    code = db.Column(db.String(6), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=0)

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        self.code = self.generate_code()

    def generate_code(self):
        # Generate a unique 6-character code and ensure it's unique in the database
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Player.query.filter_by(code=code).first():
                return code

    def add_score(self, points):
        self.score += points
        db.session.commit()

    def subtract_score(self, points):
        self.score -= points
        db.session.commit()

    @staticmethod
    def add_player(player):
        db.session.add(player)
        db.session.commit()

    @staticmethod
    def remove_player(player_code):
        player = Player.query.filter_by(code=player_code).first()
        if player:
            db.session.delete(player)
            db.session.commit()
