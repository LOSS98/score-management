from database.db_setup import db
from sqlalchemy import func

class Player(db.Model):
    __tablename__ = 'players'
    code = db.Column(db.String(6), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, default=0)

    def __init__(self, first_name, last_name, score=0):
        self.first_name = first_name
        self.last_name = last_name
        self.code = self.generate_code()
        self.score = score

    def generate_code(self):
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Player.query.filter_by(code=code).first():
                return code

    def verify_code(self, code):
        return self.code == code

    def add_score(self, points):
        self.score += points
        db.session.commit()

    def subtract_score(self, points):
        self.score -= points
        db.session.commit()

    def set_score(self, score):
        self.score = score
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

    def to_dict(self):
        return {
            'code': self.code,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'score': self.score
        }

    @staticmethod
    def calculate_total_score():
        total_score = db.session.query(func.sum(Player.score)).scalar()
        return total_score if total_score else 0

    @staticmethod
    def get_all_players_ordered_by_score():
        return Player.query.order_by(Player.score.desc()).all()

