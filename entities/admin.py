from database.db_setup import db
import random
import smtplib

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(6), nullable=False)
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, first_name, last_name, email, created_by):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = self.generate_password()
        self.created_by = created_by
        self.send_password_email()

    def generate_password(self):
        return ''.join(random.choices('0123456789', k=6))

    def send_password_email(self):
        # Use a mailing library to send the password to the admin's email
        print(f"Password sent to {self.email}: {self.password}")

    def reset_password(self):
        self.password = self.generate_password()
        db.session.commit()
        self.send_password_email()

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
