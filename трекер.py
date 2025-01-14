from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask import g

from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import os
from flask_login import LoginManager
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_BINDS'] = {
    'users': 'sqlite:///message.db'
}

app.config['JWT_SECRET_KEY'] = 'new_app'
jwt = JWTManager(app)
db = SQLAlchemy(app)
#db.init_app(app)
login_manager = LoginManager(app)
#login_manager.init_app(app)
class Tasks(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user=db.Column(db.String(50), nullable=False)
  title = db.Column(db.String(100), nullable=False)
  description=db.Column(db.String(300), default='')
  done = db.Column(db.Boolean, default=False)
  def __init__(self, user: str, title: str, description: str, done: bool): 
        self.user=user
        self.title = title
        self.description = description
        self.done = done
  def to_dict(self):
        return {
            'id': self.id,
            'user': self.user,
            'title': self.title,
            'description': self.description,
            'done': self.done
        }

tasks = [
    ('Иванов Петя','Первая задача','Описание первой задачи', False
   ),
    ('Сидоров Вова', 'Вторая задача','Описание второй задачи', False
    )
    
]
# Модель пользователя
class User(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Инициализация базы данных
with app.app_context():
    db.create_all()

# Регистрация пользователя
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')

    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"msg": " Username already exists"}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User registered successfully"}), 201

# Авторизация пользователя
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username, password=password).first()

    if user is None:
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token)


@app.route('/protected')
@jwt_required()
def add():
    db.drop_all()
    db.create_all()
    
    for el in tasks: 
            t=Tasks(*el)
            db.session.add(t)
    db.session.commit()
    return "Менеджер задач"

# Получение всех задач
@app.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    tasks = Tasks.query.all()
    return jsonify([task.to_dict() for task in tasks]), 200
# Получение задачи по ID
@app.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_tasks_id(task_id):
    task = Tasks.query.get_or_404(task_id)
    return jsonify(task.to_dict())
    
# Создание новой задачи
@app.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    if not request.json or 'title' not in request.json:
        return ('', 400)
    data = request.get_json()
    if 'description' in request.json:
        new_task = (data['title'], data['description'], False
    )
    else:
       new_task = (data['title'], "", False
    ) 
    t = Tasks(*new_task)
    db.session.add(t)
    db.session.commit()
    return jsonify(t.to_dict()), 201
# Обновление задачи
@app.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    task = Tasks.query.get_or_404(task_id)
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid input, please provide data in JSON format'}), 400
    # Обновление полей задачи, если они присутствуют в входящих данных
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'done' in data:
        task.done = data['done']
    # Сохранение изменений в базе данных
    db.session.commit()

    # Возврат обновлённой задачи
    return jsonify(task.to_dict()), 200


# Удаление задачи
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    task = Tasks.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return '', 204
@app.teardown_appcontext
def teardown_db(exception):
    
    db = g.pop('db', None)
    if db is not None:
        db.close()  # Close the database connection
        
if __name__ == "__main__": 
    app.run(debug=True)