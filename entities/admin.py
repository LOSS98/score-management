from database.db_setup import db
import random
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message, Mail
import smtplib


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(6), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    creator = db.relationship('Admin', remote_side=[id], backref='created_admins')

    def __init__(self, first_name, last_name, email, created_by):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = self.generate_password()
        self.created_by = created_by

    def generate_password(self):
        return ''.join(random.choices('0123456789', k=6))

    def reset_password(self):
        self.password = self.generate_password()
        db.session.commit()
        self.send_password_email()

    def verify_password(self, password):
        return self.password == password

    def send_password_email(self):
        try:
            from app import mail
            body = (f'Hey heyy heyyy,\n\n'
                    f'{self.creator.first_name} {self.creator.last_name} t\'a créé un compte admin pour que tu puisses faire partie du staff de FaitesVosJE.\n\n'
                    f'Voici tes identifiants, à garder top secret ! (Sinon, quelqu\'un pourrait piquer des 🧪 tubes à essai 🧪 et provoquer un chaos dans le casino 😱)\n'
                    f'\t📧 E-mail : Bahh, c\'est le tien ! Mais vu que parfois ta mémoire flanche comme l\'azote liquide (nitrogène pour les anciens), le revoici -> {self.email}\n'
                    f'\t🔒 Mot de passe : {self.password}\n\n'
                    f'Bonne soirée et molo avec l\'alcool, je te rappelle que tu staffs,\n\nMoi.')
            print(body)
            msg = Message(
                subject="FaitesVosJE - To compte admin ;)",
                recipients=[self.email],
                body=body
            )
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send password email to {self.email}: {str(e)}")

    @staticmethod
    def add_admin(admin):
        db.session.add(admin)
        db.session.commit()

    @staticmethod
    def remove_admin(admin_id):
        admin = Admin.query.get(admin_id)
        if admin:
            db.session.delete(admin)
            db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
        }
