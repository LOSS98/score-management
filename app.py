from flask import Flask, session, request, redirect, url_for, render_template, jsonify
from flask_assets import Environment, Bundle
from database.db_setup import db
from flask_migrate import Migrate
from flask_session import Session

from flask_mail import Mail, Message
from entities.player import Player
from entities.game_room import GameRoom
from entities.admin import Admin

from dotenv import load_dotenv
import os

app = Flask(__name__)
assets = Environment(app)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'idfghjkagfuykagsf76GHKSGDFJ87vk'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///score_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

db.init_app(app)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

# Configuration du bundle SCSS
scss = Bundle('scss/styles.scss', filters='libsass', output='css/styles.css')
assets.register('scss_all', scss)


def is_admin_logged_in():
    if 'admin_id' in session and 'user_type' in session:
        if session.get('user_type') == 'admin':
            admin_id = session.get('admin_id')
            admin = Admin.query.get(admin_id)
            if admin:
                return True
    return False


def is_player_logged_in():
    if 'player_code' in session and 'user_type' in session:
        if session.get('user_type') == 'player':
            code = session.get('player_code')
            player = Player.query.get(code)
            if player:
                return True
    return False


'''PLAYER '''


@app.route('/', methods=['GET', 'POST'])
def index():
    if is_player_logged_in():
        player = Player.query.filter_by(code=session['player_code']).first()
        return render_template('player-score.html', code=session['player_code'], score=player.score,
                               fname=session['player_fname'], lname=session['player_lname'])
    if request.method == 'POST':
        code = str(request.form.get('digit1')) + str(request.form.get('digit2')) + str(
            request.form.get('digit3')) + str(request.form.get('digit4')) + str(request.form.get('digit5')) + str(
            request.form.get('digit6'))
        print(code)
        player = Player.query.filter_by(code=code).first()
        if player and player.verify_code(code):
            session['player_code'] = player.code
            session['user_type'] = 'player'
            session['player_fname'] = player.first_name
            session['player_lname'] = player.last_name
            return redirect(url_for('index'))
        else:
            return 'Invalid code', 401
    return render_template('access.html')

'''@app.route('/player-score')
def playerScore():
    if is_player_logged_in():
        return render_template('player-score.html')
    return redirect(url_for('index'))'''

@app.route('/logout')
def logout():
    session.pop('player_code', None)
    session.pop('user_type', None)
    session.pop('player_fname', None)
    session.pop('player_lname', None)
    return redirect(url_for('index'))


@app.route('/ranking')
def ranking():
    return_link = './'
    players_list = []
    players = Player.get_all_players_ordered_by_score()
    for player in players:
        players_list.append(player.to_dict())
    if is_admin_logged_in():
        return_link = './menu'
        return render_template('ranking.html', return_link=return_link, players=players, count_players=len(players_list))
    if is_player_logged_in():
        return render_template('ranking.html', return_link=return_link, players=players, count_players=len(players_list))
    return redirect(url_for('index'))


'''ADMIN'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_admin_logged_in():
        return redirect(url_for('menu'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(email, password)
        admin = Admin.query.filter_by(email=email).first()
        print(admin)
        if admin and admin.verify_password(password):
            session['admin_id'] = admin.id
            session['user_type'] = 'admin'
            session['admin_fname'] = admin.first_name
            session['admin_lname'] = admin.last_name
            session['admin_email'] = admin.email
            return redirect(url_for('menu'))
        else:
            return 'Invalid email or password', 401

    return render_template('login.html')


@app.route('/logout-admin')
def logout_admin():
    session.pop('admin_id', None)
    session.pop('admin_fname', None)
    session.pop('user_type', None)
    session.pop('admin_lname', None)
    session.pop('admin_email', None)
    return redirect(url_for('login'))


@app.route('/menu')
def menu():
    if is_admin_logged_in():
        return render_template('menu.html',admin_fname = session['admin_fname'])
    return redirect(url_for('login'))


'''Game's rooms'''
@app.route('/games', methods=['GET'])
def games():
    message = request.args.get('message')
    if not message:
        message = ''
    error = request.args.get('error')
    if not error:
        error = ''
    if is_admin_logged_in():
        game_rooms = GameRoom.query.all()
        rooms = []
        for room in game_rooms:
            rooms.append(room.to_dict())
        print(rooms)
        return render_template('games.html', game_rooms=rooms, message=message, error=error)
    return redirect(url_for('login'))


@app.route('/delete-game-room', methods=['GET', 'POST'])
def delete_game_room():
    if is_admin_logged_in():
        room_code = request.form.get('room_code')
        if not room_code:
            return redirect(url_for('games', error='room_id is required'))
        room = GameRoom.query.filter_by(room_code=room_code).first()
        if not room:
            return redirect(url_for('games', error='Game room not found'))
        db.session.delete(room)
        db.session.commit()
        return redirect(url_for('games', message=f'Game room {room_code} has been deleted successfully'))
    return redirect(url_for('login'))


@app.route('/add-game-room', methods=['GET', 'POST'])
def add_game_room():
    if is_admin_logged_in():
        room_name = request.form.get('room_name')
        created_by = session['admin_id']
        if not room_name or not created_by:
            return redirect(url_for('games', error='Room name and created_by are required'))
        new_room = GameRoom(room_name=room_name, created_by=created_by)
        db.session.add(new_room)
        db.session.commit()
        return redirect(url_for('games',
                                message=f'Game room {new_room.room_code} - {new_room.room_name} has been added successfully'))
    return redirect(url_for('login'))


@app.route('/game-party/<room_code>', methods=['GET'])
def gameparty(room_code=None):
    if is_admin_logged_in():
        message = request.args.get('message')
        if not message:
            message = ''
        error = request.args.get('error')
        if not error:
            error = ''
        if room_code:
            existing_room = GameRoom.query.filter_by(room_code=room_code).first()
            if existing_room:
                players = [{'code': player.code, 'first_name': player.first_name, 'last_name': player.last_name,
                            'score': player.score}
                           for player in existing_room.players]
                existing_room = existing_room.to_dict()
                return render_template('game-party.html', room=existing_room, message=message, error=error,
                                       players=players)
            return redirect(url_for('games', error=f'Room #{room_code} doesn\'t exist'))
        return redirect(url_for('games', error=f'room_code is required'))
    return redirect(url_for('login'))


@app.route('/add-score-game', methods=['POST'])
def add_score_game():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')
        score_to_add = request.form.get('plus')
        room_code = request.form.get('room_code')

        if not player_code or not score_to_add:
            return redirect(url_for('gameparty', room_code=room_code, error='Player code and score are required'))

        player = Player.query.filter_by(code=player_code).first()
        if not player:
            return redirect(url_for('gameparty', room_code=room_code, error='Player not found'))

        try:
            score_to_add = int(score_to_add)
        except ValueError:
            return redirect(url_for('gameparty', error='Invalid score value'))

        if not room_code:
            return redirect(url_for('gameparty', room_code=room_code, error='Room code is required'))

        room = GameRoom.query.filter_by(room_code=room_code).first()
        if not room:
            return redirect(url_for('gameparty', room_code=room_code, error='Room not found'))

        player.add_score(score_to_add)
        return redirect(url_for('gameparty', room_code=room_code, message=f'Score added to player {player_code}'))
    return redirect(url_for('login'))


@app.route('/remove-score-game', methods=['POST'])
def remove_score_game():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')
        score_to_remove = request.form.get('minus')
        room_code = request.form.get('room_code')

        if not player_code or not score_to_remove:
            return redirect(url_for('gameparty', room_code=room_code, error='Player code and score are required'))

        try:
            score_to_remove = int(score_to_remove)
        except ValueError:
            return redirect(url_for('gameparty', error='Invalid score value'))

        player = Player.query.filter_by(code=player_code).first()
        if not player:
            return redirect(url_for('gameparty', room_code=room_code, error='Player not found'))

        if not room_code:
            return redirect(url_for('gameparty', room_code=room_code, error='Room code is required'))

        room = GameRoom.query.filter_by(room_code=room_code).first()
        if not room:
            return redirect(url_for('gameparty', room_code=room_code, error='Room not found'))

        player.subtract_score(score_to_remove)
        return redirect(url_for('gameparty', room_code=room_code, message=f'Score removed from player {player_code}'))
    return redirect(url_for('login'))

@app.route('/remove-player-from-room', methods=['GET', 'POST'])
def remove_player_from_room():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')
        room_code = request.form.get('room_code')

        if not player_code:
            return redirect(url_for('gameparty', room_code=room_code, error='Player code is required'))

        player = Player.query.filter_by(code=player_code).first()
        if not player:
            return redirect(url_for('gameparty', room_code=room_code, error='Player not found'))

        if not room_code:
            return redirect(url_for('gameparty', room_code=room_code, error='Room code is required'))

        room = GameRoom.query.filter_by(room_code=room_code).first()
        if not room:
            return redirect(url_for('gameparty', room_code=room_code, error='Room not found'))

        room.remove_player(player.code)
        db.session.commit()

        return redirect(
            url_for('gameparty', room_code=room_code, message=f'Player {player_code} removed from room {room_code}'))
    return redirect(url_for('login'))


@app.route('/add-player-to-room', methods=['GET', 'POST'])
def add_player_to_room():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')
        room_code = request.form.get('room_code')

        if not player_code:
            return redirect(url_for('gameparty', room_code=room_code, error='Player code is required'))

        player = Player.query.filter_by(code=player_code).first()
        if not player:
            return redirect(url_for('gameparty', room_code=room_code, error='Player not found'))

        if not room_code:
            return redirect(url_for('gameparty', room_code=room_code, error='Room code is required'))

        room = GameRoom.query.filter_by(room_code=room_code).first()
        if not room:
            return redirect(url_for('gameparty', room_code=room_code, error='Room not found'))

        room.add_player(player.code)
        db.session.commit()

        return redirect(
            url_for('gameparty', room_code=room_code, message=f'Player {player_code} added at room {room_code}'))
    return redirect(url_for('login'))



''' Score '''

@app.route('/add-score', methods=['POST'])
def add_score():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')
        score_to_add = request.form.get('plus')
        print(score_to_add)
        if not player_code or not score_to_add:
            return redirect(url_for('score', error='Player code and score are required'))

        try:
            score_to_add = int(score_to_add)
        except ValueError:
            return redirect(url_for('score', error='Invalid score value'))

        player = Player.query.filter_by(code=player_code).first()
        if not player:
            return redirect(url_for('score', error='Player not found'))

        player.add_score(score_to_add)
        return redirect(url_for('score', message=f'Score {score_to_add}pts added to player {player_code}:{player.first_name} {player.last_name}'))
    return redirect(url_for('login'))


@app.route('/remove-score', methods=['POST'])
def remove_score():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')
        score_to_remove = request.form.get('minus')

        if not player_code or not score_to_remove:
            return redirect(url_for('score', error='Player code and score are required'))

        try:
            score_to_remove = int(score_to_remove)
        except ValueError:
            return redirect(url_for('score', error='Invalid score value'))

        player = Player.query.filter_by(code=player_code).first()
        if not player:
            return redirect(url_for('score', error='Player not found'))

        player.subtract_score(score_to_remove)
        return redirect(url_for('score', message=f'Score {score_to_remove}pts removed from player {player_code}:{player.first_name} {player.last_name}'))
    return redirect(url_for('login'))


@app.route('/set-score', methods=['POST'])
def set_score():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')
        score = request.form.get('set')

        if not player_code or not score:
            return redirect(url_for('score', error='Player code and score are required'))

        player = Player.query.filter_by(code=player_code).first()
        if not player:
            return redirect(url_for('score', error='Player not found'))

        player.set_score(score)
        return redirect(url_for('score', message=f'Score {score}pts set to player {player_code}:{player.first_name} {player.last_name}'))
    return redirect(url_for('login'))


@app.route('/add-score-all', methods=['POST'])
def add_score_all():
    if is_admin_logged_in():
        score_to_add = request.form.get('plus')

        if not score_to_add:
            return redirect(url_for('score', error='Score are required'))

        try:
            score_to_add = int(score_to_add)
        except ValueError:
            return redirect(url_for('score', error='Invalid score value'))
        players = Player.query.all()

        for player in players:
            player.add_score = score_to_add
        return redirect(url_for('score', message=f'Score {score_to_add}pts added to all players'))
    return redirect(url_for('login'))


@app.route('/remove-score-all', methods=['POST'])
def remove_score_all():
    if is_admin_logged_in():
        score_to_remove = request.form.get('minus')

        if not score_to_remove:
            return redirect(url_for('score', error='Score are required'))

        try:
            score_to_remove = int(score_to_remove)
        except ValueError:
            return redirect(url_for('score', error='Invalid score value'))

        players = Player.query.all()
        for player in players:
            player.subtract_score(score_to_remove)

        return redirect(url_for('score', message=f'Score {score_to_remove}pts removed for all players'))
    return redirect(url_for('login'))


@app.route('/set-score-all', methods=['POST'])
def set_score_all():
    if is_admin_logged_in():
        score = request.form.get('set')

        if not score:
            return redirect(url_for('score', error='Score is required'))

        try:
            score = int(score)
        except ValueError:
            return redirect(url_for('score', error='Invalid score value'))

        players = Player.query.all()
        for player in players:
            player.set_score(score)

        db.session.commit()
        return redirect(url_for('score', message=f'Score {score}pts set for all players successfully'))
    return redirect(url_for('login'))
@app.route('/score')
def score():
    if is_admin_logged_in():
        message = request.args.get('message')
        if not message:
            message = ''
        error = request.args.get('error')
        if not error:
            error = ''
        players = Player.query.all()
        players_list = []
        for player in players:
            players_list.append(player.to_dict())
        total_score = Player.calculate_total_score()
        return render_template('score.html', players=players_list, total_score=total_score, message=message,
                               error=error)
    return redirect(url_for('login'))


''' Players '''
@app.route('/players', methods=['GET'])
def players():
    if is_admin_logged_in():
        message = request.args.get('message')
        if not message:
            message = ''
        error = request.args.get('error')
        if not error:
            error = ''
        players = Player.query.all()
        players_list = []
        for player in players:
            players_list.append(player.to_dict())
        return render_template('players.html', players=players_list, message=message, error=error)
    return redirect(url_for('login'))


@app.route('/create-player', methods=['GET', 'POST'])
def create_player():
    if is_admin_logged_in():
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        score = request.form.get('score')

        if not first_name or not last_name:
            return redirect(url_for('players', error='First name and last name are required'))

        new_player = Player(first_name=first_name, last_name=last_name, score=score)
        Player.add_player(new_player)

        return redirect(url_for('players',
                                message=f'Player {new_player.first_name} {new_player.last_name} created successfully with code {new_player.code}'))
    return redirect(url_for('login'))


@app.route('/delete-player', methods=['GET', 'POST'])
def delete_player():
    if is_admin_logged_in():
        player_code = request.form.get('player_code')

        if not player_code:
            return redirect(url_for('players', error='player_code is required'))

        Player.remove_player(player_code)

        return redirect(url_for('players', message=f'Player {player_code} deleted successfully'))
    return redirect(url_for('login'))


@app.route('/admins', methods=['GET'])
def admins():
    if is_admin_logged_in():
        message = request.args.get('message')
        if not message:
            message = ''
        error = request.args.get('error')
        if not error:
            error = ''
        admins = Admin.query.all()
        admins_list = [admin.to_dict() for admin in admins]
        return render_template('admins.html', admins = admins_list, message=message, error=error)
    return redirect(url_for('login'))

@app.route('/delete-admin', methods=['GET', 'POST'])
def delete_admin():
    if is_admin_logged_in():
        admin_id = request.form.get('admin_id')

        if not admin_id:
            return redirect(url_for('admins', error='admin_id is required'))

        Admin.remove_admin(admin_id)

        return redirect(url_for('admins', message=f'Admin {admin_id} deleted successfully'))
    return redirect(url_for('login'))

@app.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    if is_admin_logged_in():
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')

        if not first_name or not last_name or not email:
            return redirect(url_for('admins', error='All fields are required'))

        new_admin = Admin(first_name=first_name, last_name=last_name, email=email, created_by=session['admin_id'])
        Admin.add_admin(new_admin)

        new_admin.send_password_email()
        return redirect(url_for('admins',
                                message=f'Admin {new_admin.first_name} {new_admin.last_name} created successfully. They should receive the password via email shortly.'))
    return redirect(url_for('login'))
@app.route('/reset-password', methods=['POST'])
def reset_password():
    if is_admin_logged_in():
        admin_id = request.form.get('admin_id')

        if not admin_id:
            return redirect(url_for('admins', error='Admin ID is required'))

        admin = Admin.query.filter_by(id=admin_id).first()
        if not admin:
            return redirect(url_for('admins', error='Admin not found'))

        admin.reset_password()

        return redirect(url_for('admins', message=f'The password for admin {admin_id} : {admin.first_name} {admin.last_name} has been reset successfully. They should receive it via email shortly.'))
    return redirect(url_for('login'))


@app.route('/createAdmin')
def createAdmin():
    admin = Admin(first_name='Khalil', last_name='Mzoughi', email='khalilmzoughi@icloud.com', created_by='Khalil')
    Admin.add_admin(admin)
    print(f"Done")

    return 'admin created'


@app.route('/createPalyer')
def createPalyer():
    player = Player(first_name='Khalil', last_name='Mzoughi')
    print(player.code)
    Player.add_player(player)
    print(f"Done")
    return 'Plauer created'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
