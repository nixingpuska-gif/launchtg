import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
import jwt
from datetime import datetime, timedelta
import asyncpg

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = 'telegram_automation_secret_key_2024'

CORS(app, resources={
    r'/*': {
        'origins': ['http://localhost:8000', 'http://127.0.0.1:8000'],
        'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'allow_headers': ['Content-Type', 'Authorization'],
        'supports_credentials': True
    }
} )

# Global connection pool
db_pool = None

def get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

def init_pool():
    global db_pool
    if db_pool is None:
        loop = get_event_loop()
        db_pool = loop.run_until_complete(asyncpg.create_pool(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='telegram_automation',
            min_size=2,
            max_size=10
        ))
    return db_pool

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        pool = init_pool()
        loop = get_event_loop()
        
        async def do_login():
            async with pool.acquire() as conn:
                user = await conn.fetchrow(
                    'SELECT id, username, password_hash, role FROM users WHERE username = \',
                    username
                )
                
                if not user:
                    return None
                
                if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return None
                
                await conn.execute(
                    'UPDATE users SET last_login = \ WHERE id = \',
                    datetime.now(), user['id']
                )
                
                return user
        
        user = loop.run_until_complete(do_login())
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        print(f'Login error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def get_stats():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No token'}), 401
        
        token = auth_header.split(' ')[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
        
        pool = init_pool()
        loop = get_event_loop()
        
        async def get_counts():
            async with pool.acquire() as conn:
                accounts = await conn.fetchval('SELECT COUNT(*) FROM accounts WHERE user_id = \', user_id) or 0
                groups = await conn.fetchval('SELECT COUNT(*) FROM groups WHERE user_id = \', user_id) or 0
                users = await conn.fetchval('SELECT COUNT(*) FROM parsed_users WHERE user_id = \', user_id) or 0
                campaigns = await conn.fetchval('SELECT COUNT(*) FROM campaigns WHERE user_id = \', user_id) or 0
                return {'accounts': accounts, 'groups': groups, 'users': users, 'campaigns': campaigns}
        
        stats = loop.run_until_complete(get_counts())
        return jsonify(stats), 200
        
    except Exception as e:
        print(f'Stats error: {e}')
        return jsonify({'accounts': 0, 'groups': 0, 'users': 0, 'campaigns': 0}), 200

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify([]), 200
        
        token = auth_header.split(' ')[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
        
        pool = init_pool()
        loop = get_event_loop()
        
        async def fetch_accounts():
            async with pool.acquire() as conn:
                accounts = await conn.fetch(
                    'SELECT id, phone, name, status, created_at FROM accounts WHERE user_id = \',
                    user_id
                )
                return accounts
        
        accounts = loop.run_until_complete(fetch_accounts())
        return jsonify([dict(acc) for acc in accounts]), 200
        
    except Exception as e:
        print(f'Accounts error: {e}')
        return jsonify([]), 200

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify([]), 200
        
        token = auth_header.split(' ')[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
        
        pool = init_pool()
        loop = get_event_loop()
        
        async def fetch_notifs():
            async with pool.acquire() as conn:
                notifs = await conn.fetch(
                    'SELECT id, type, message, created_at FROM notifications WHERE user_id = \ ORDER BY created_at DESC LIMIT 10',
                    user_id
                )
                return notifs
        
        notifs = loop.run_until_complete(fetch_notifs())
        return jsonify([dict(n) for n in notifs]), 200
        
    except Exception as e:
        print(f'Notifications error: {e}')
        return jsonify([]), 200

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No token'}), 401
        
        token = auth_header.split(' ')[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        return jsonify({
            'id': data['user_id'],
            'username': data['username'],
            'role': data.get('role', 'user')
        }), 200
        
    except Exception as e:
        print(f'Get me error: {e}')
        return jsonify({'error': str(e)}), 401

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    print('=' * 60)
    print('  Telegram Automation Pro - Backend API')
    print('  Version: 4.0.1 (Fixed Pool)')
    print('=' * 60)
    print(f'\nStarting server on http://127.0.0.1:8000' )
    print(f'Frontend: http://127.0.0.1:8000/' )
    print(f'API: http://127.0.0.1:8000/api/' )
    print('\nPress CTRL+C to stop\n')
    
    app.run(host='0.0.0.0', port=8000, debug=True)
