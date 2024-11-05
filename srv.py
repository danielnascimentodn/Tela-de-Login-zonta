from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import jwt
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_passoword_hash

app = Flask (__name__)
CORS (app)
DATABASE = 'users.db'
SECRET_KEY = 'lab1807102024RestFull' # Chave secreta para gerar os tokes
#basica ideal é usar uma chave privada com certificado ou nr-primeiro

# Conectar ao banco de dados 
def get_db():
    db = getattr(g,'_database_', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

#Inicializar banco de dados 
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor ()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL -- Adicionando campo de senha
            ) 
        ''')
        db.commit

# Fechar conexão com banco de dados ao finalizar requisição 
@app. teardown_appcontext
def close_conncection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Função para gerar um token JWT (JSON WEB TOKEN - aqui é o acessToken)
def generate_token(username,userid):
    payloand = {
        'username': username,
        'userid': userid,
        'exp': datetime.datatime.utcnow() + datetime.timedelta(hours=1)
        }
    return jwt.encode(payloand, SECRET_KEY, algorithm='HS256')
#Middleware para validar o token JWT
def token_requerido(f):
    @wraps(f)
    def decorated (*args, **kwargs):
        token = None

        #Obtendo o token do cabeçalho da requisição
        if 'Authorization' in request.headers:
            token = request.headers ['Authorization'].split(" ") [1]

        if not token:
            return jsonify({"mensagem":"Token é necessario"})
        
        try:
            # Decodificando e validando o token
            dados = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.userid = dados["userid"]
        except jwt.ExpiredSignatureError:
            return jsonify({"mensagem": "Token expirado"})
        except jwt.ExpiredSignatureError:
            return jsonify({"mensagem": "Token inválidado"})
        
        return f (*args, **kwargs)
    return decorated

# Rota protegida (somente acessivel com token válido)
@app.route ('/protegodp', methods =['GET'])
@token_requerido
def rota_protegida():
    return jsonify({"mensagem": "Acesso permitido", "userid": request.userid})

# Endpoint para criar um novo usuario com senha(CREATE)
# http://localhost:5000/register
@app.route('/register', methods=['POST'])
def register_user():
    data= request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and passaword ar required'})
    
#Hash da senha antes de salvar no banco de dados 
    hashed_password = generate_password_hash(password)

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_password))
    db.commit()

    return jsonify({'id': cursor.lastrowid, 'username': username, 'email': email})

#Endpoint de login que gera e retorna um token de acesso (LOGIN)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    passowrd = data.get('password')

    if not username or not passowrd:
        return jsonify ({'error': 'usuario e senha requerido'})#, 400
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    #print(user[0], user[1])

    if user is None or not check_passoword_hash(user[3], passowrd): #Verifica hash da senha 
        return jsonify({'error': 'usuario ou senha incorreto'}), #401

    #Se o login for bem-sucedido gerar um token JWT
    token = generate_token(username,user[0])
    return jsonify({'menssage': 'Login sucesso', 'token':token}) #, 200

# Fechar a conexão com o banco de dados ao finalizar a requisição
@app.teardown_appcontext
def close_conection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__== '__main__':
    init_db() #inicializa o banco de dados ao iniciar o app
    app.run(debug=True)
