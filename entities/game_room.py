from database.db_setup import db
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.orm import relationship

# Association table for many-to-many relationship
player_game_room = db.Table('player_game_room',
    db.Column('player_code', db.String(6), db.ForeignKey('players.code')),
    db.Column('room_code', db.String(6), db.ForeignKey('game_rooms.room_code'))
)

class GameRoom(db.Model):
    __tablename__ = 'game_rooms'
    room_code = db.Column(db.String(6), primary_key=True)
    room_name = db.Column(db.String(50), nullable=False)
    created_by = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    players = db.relationship('Player', secondary=player_game_room, backref='rooms')

    def __init__(self, room_name, created_by):
        self.room_code = self.generate_code()
        self.room_name = room_name
        self.created_by = created_by

    def generate_code(self):
        # Reuse the code generation logic from Player
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not GameRoom.query.filter_by(room_code=code).first():
                return code

    def add_player(self, player_code):
        player = Player.query.filter_by(code=player_code).first()
        if player:
            self.players.append(player)
            db.session.commit()

    def remove_player(self, player_code):
        player = Player.query.filter_by(code=player_code).first()
        if player in self.players:
            self.players.remove(player)
            db.session.commit()

    def empty_room(self):
        self.players.clear()
        db.session.commit()

    @staticmethod
    def add_room(room):
        db.session.add(room)
        db.session.commit()

    @staticmethod
    def remove_room(room_code):
        room = GameRoom.query.filter_by(room_code=room_code).first()
        if room:
            db.session.delete(room)
            db.session.commit()
