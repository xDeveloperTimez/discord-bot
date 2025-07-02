#!/usr/bin/env python3
"""
Flask application for Replit deployment with Discord bot integration
This is the main entry point that Replit deployment expects
"""

import os
import sys
import threading
import time
import requests
from flask import Flask, jsonify, send_from_directory, request
from datetime import datetime

# Create Flask application
app = Flask(__name__)

# Global variable to track bot status
bot_status = {"connected": False, "guilds": 0, "users": 0}

@app.route('/')
def home():
    """Serve the main HTML page"""
    try:
        with open('index.html', 'r') as f:
            content = f.read()
        response = app.response_class(
            response=content,
            status=200,
            mimetype='text/html'
        )
        response.headers['Cache-Control'] = 'no-cache'
        return response
    except:
        return jsonify({
            "status": "healthy",
            "service": "Guardian Discord Bot",
            "timestamp": datetime.utcnow().isoformat(),
            "ready": True,
            "bot_connected": bot_status["connected"]
        })

@app.route('/api/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Guardian Discord Bot",
        "timestamp": datetime.utcnow().isoformat(),
        "ready": True,
        "bot_connected": bot_status["connected"]
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        "bot_name": "Guardian Bot",
        "version": "1.0.0",
        "status": "online",
        "bot_connected": bot_status["connected"],
        "guilds": bot_status["guilds"],
        "users": bot_status["users"],
        "features": [
            "Moderation Commands",
            "Music Player", 
            "Anti-Raid Protection",
            "Auto-Moderation",
            "Utility Commands"
        ],
        "commands": 73,
        "uptime": datetime.utcnow().isoformat()
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    response = app.response_class(
        response="pong",
        status=200,
        mimetype='text/plain'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/ready')
def ready():
    """Kubernetes-style readiness probe"""
    return jsonify({"ready": True, "status": "ok"})

@app.route('/live')  
def live():
    """Kubernetes-style liveness probe"""
    return jsonify({"alive": True, "status": "ok"})

@app.route('/purchase')
@app.route('/purchase.html')
def purchase_portal():
    """Purchase portal page"""
    try:
        with open('purchase.html', 'r') as f:
            content = f.read()
        response = app.response_class(
            response=content,
            status=200,
            mimetype='text/html'
        )
        response.headers['Cache-Control'] = 'no-cache'
        return response
    except:
        return jsonify({"error": "Purchase portal not available"}), 500

@app.route('/attached_assets/<filename>')
def serve_assets(filename):
    """Serve static assets like images and GIFs"""
    try:
        return send_from_directory('attached_assets', filename)
    except:
        return jsonify({"error": "Asset not found"}), 404

@app.route('/dashboard')
@app.route('/dashboard.html')
def guardian_dashboard():
    """Guardian Bot server dashboard"""
    try:
        with open('guardian-dashboard.html', 'r') as f:
            content = f.read()
        response = app.response_class(
            response=content,
            status=200,
            mimetype='text/html'
        )
        response.headers['Cache-Control'] = 'no-cache'
        return response
    except:
        return jsonify({"error": "Dashboard not available"}), 500

@app.route('/custom-dashboard')
@app.route('/custom-dashboard.html')
def custom_dashboard():
    """Custom bot management dashboard"""
    try:
        with open('dashboard.html', 'r') as f:
            content = f.read()
        response = app.response_class(
            response=content,
            status=200,
            mimetype='text/html'
        )
        response.headers['Cache-Control'] = 'no-cache'
        return response
    except:
        return jsonify({"error": "Custom dashboard not available"}), 500

@app.route('/auth/discord/callback')
def discord_oauth_callback():
    """Discord OAuth callback page"""
    try:
        with open('oauth-callback.html', 'r') as f:
            content = f.read()
        response = app.response_class(
            response=content,
            status=200,
            mimetype='text/html'
        )
        response.headers['Cache-Control'] = 'no-cache'
        return response
    except:
        return jsonify({"error": "OAuth callback not available"}), 500

@app.route('/auth/discord/token', methods=['POST'])
def discord_oauth_token():
    """Exchange OAuth code for access token"""
    try:
        import requests
        import os
        
        data = request.get_json()
        code = data.get('code')
        redirect_uri = data.get('redirect_uri')
        
        if not code:
            return jsonify({'success': False, 'error': 'No authorization code provided'})
        
        # Discord OAuth token endpoint
        token_url = 'https://discord.com/api/oauth2/token'
        client_id = '1388909466556043396'  # Guardian Bot application ID
        client_secret = os.getenv('DISCORD_CLIENT_SECRET')  # Add this to secrets
        
        if not client_secret:
            return jsonify({'success': False, 'error': 'Discord client secret not configured'})
        
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        print(f"Token exchange request: {token_data}", flush=True)
        response = requests.post(token_url, data=token_data, headers=headers)
        print(f"Discord response status: {response.status_code}", flush=True)
        print(f"Discord response: {response.text}", flush=True)
        
        if response.status_code == 200:
            token_info = response.json()
            access_token = token_info['access_token']
            
            # Get user info
            user_response = requests.get('https://discord.com/api/users/@me', 
                                       headers={'Authorization': f'Bearer {access_token}'})
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                return jsonify({
                    'success': True,
                    'access_token': access_token,
                    'user_id': user_info['id'],
                    'username': user_info['username']
                })
            else:
                print(f"User info error: {user_response.status_code} - {user_response.text}")
                return jsonify({'success': False, 'error': 'Failed to fetch user info'})
        else:
            try:
                error_data = response.json()
                print(f"Discord error data: {error_data}")
                return jsonify({
                    'success': False, 
                    'error': error_data.get('error_description', error_data.get('error', 'Failed to exchange code for token'))
                })
            except:
                return jsonify({
                    'success': False, 
                    'error': f'Discord API error: {response.status_code} - {response.text}'
                })
            
    except Exception as e:
        import traceback
        print(f"OAuth token exchange error: {e}", flush=True)
        print(f"Full traceback: {traceback.format_exc()}", flush=True)
        return jsonify({'success': False, 'error': f'Internal server error: {str(e)}'})

@app.route('/api/dashboard/check-bot-guilds', methods=['POST'])
def check_bot_guilds():
    """Check which guilds have the bot present"""
    try:
        data = request.get_json()
        guild_ids = data.get('guild_ids', [])
        
        # Get bot instance and check guild membership
        if hasattr(app, 'discord_bot') and app.discord_bot:
            bot_guild_ids = [str(guild.id) for guild in app.discord_bot.guilds]
            present_guilds = [gid for gid in guild_ids if gid in bot_guild_ids]
            
            return jsonify({
                'success': True,
                'bot_guilds': present_guilds
            })
        else:
            return jsonify({'success': False, 'error': 'Bot not available'})
            
    except Exception as e:
        print(f"Error checking bot guilds: {e}")
        return jsonify({'success': False, 'error': 'Failed to check bot presence'})

# Dashboard API endpoints
@app.route('/api/dashboard/server/<guild_id>')
def get_server_config(guild_id):
    """Get Guardian Bot configuration for a specific server"""
    try:
        # Get user_id from Discord access token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'User authentication required'})
        
        access_token = auth_header.split(' ')[1]
        
        # Get user info from Discord API
        import requests
        discord_response = requests.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if discord_response.status_code != 200:
            return jsonify({'success': False, 'error': 'Invalid or expired token'})
        
        user_data = discord_response.json()
        user_id = int(user_data['id'])
        
        # Check user license level
        from database import DatabaseManager
        db_manager = DatabaseManager()
        
        # For now, allow owner access for testing (user_id 344210326251896834 has owner privileges)
        if int(user_id) == 344210326251896834:
            license_type = 'EXCLUSIVE'
        else:
            # Verify user has at least Basic license for dashboard access
            if not db_manager.check_user_access(int(user_id), 'BASIC'):
                return jsonify({'success': False, 'error': 'Basic license required for dashboard access'})
            
            # Get user's license to determine available features
            user_license = db_manager.get_user_license(int(user_id))
            license_type = user_license.license_type if user_license else 'FREE'
        
        guild = db_manager.get_or_create_guild(int(guild_id))
        
        if guild:
            config = {
                'guild_id': guild_id,
                'guild_name': getattr(guild, 'name', 'Unknown Server'),
                'prefix': getattr(guild, 'prefix', '.'),
                'log_channel_id': getattr(guild, 'log_channel_id', None),
                'mod_role': getattr(guild, 'mod_role', 'Moderator'),
                'admin_role': getattr(guild, 'admin_role', 'Administrator'),
                'mute_role': getattr(guild, 'mute_role', 'Muted'),
                'automod_enabled': getattr(guild, 'automod_enabled', True),
                'anti_raid_enabled': getattr(guild, 'anti_raid_enabled', False),
                'anti_raid_config': getattr(guild, 'anti_raid_config', {}),
                'user_license': license_type,
                'available_features': get_available_features(license_type)
            }
            return jsonify({'success': True, 'config': config})
        else:
            return jsonify({'success': False, 'error': 'Server not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_available_features(license_type):
    """Return available features based on license type"""
    features = {
        'FREE': ['basic_moderation', 'logging'],
        'BASIC': ['basic_moderation', 'logging', 'automod', 'auto_responses'],
        'PREMIUM': ['basic_moderation', 'logging', 'automod', 'auto_responses', 'anti_raid', 'advanced_moderation'],
        'EXCLUSIVE': ['basic_moderation', 'logging', 'automod', 'auto_responses', 'anti_raid', 'advanced_moderation', 'custom_commands', 'premium_features']
    }
    return features.get(license_type, features['FREE'])

@app.route('/api/dashboard/server/<guild_id>', methods=['POST'])
def update_server_config(guild_id):
    """Update Guardian Bot configuration for a specific server"""
    try:
        # Authenticate user via Discord token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'User authentication required'})
        
        access_token = auth_header.split(' ')[1]
        
        # Get user info from Discord API
        import requests
        discord_response = requests.get(
            'https://discord.com/api/users/@me',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if discord_response.status_code != 200:
            return jsonify({'success': False, 'error': 'Invalid or expired token'})
        
        user_data = discord_response.json()
        user_id = int(user_data['id'])
        
        data = request.get_json()
        from database import DatabaseManager
        db_manager = DatabaseManager()
        
        success = db_manager.update_guild_config(
            int(guild_id),
            prefix=data.get('prefix'),
            log_channel_id=data.get('log_channel_id'),
            mod_role=data.get('mod_role'),
            admin_role=data.get('admin_role'),
            mute_role=data.get('mute_role'),
            automod_enabled=data.get('automod_enabled'),
            anti_raid_enabled=data.get('anti_raid_enabled'),
            anti_raid_config=data.get('anti_raid_config')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Configuration updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update configuration'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/custom/<deployment_id>')
def get_custom_bot_info(deployment_id):
    """Get custom bot information and status"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'User authentication required'})
        
        from database import DatabaseManager
        db_manager = DatabaseManager()
        session = db_manager.get_session()
        
        from models import CustomBot
        custom_bot = session.query(CustomBot).filter_by(
            deployment_id=deployment_id,
            customer_id=int(user_id)
        ).first()
        
        if custom_bot:
            bot_info = {
                'deployment_id': custom_bot.deployment_id,
                'bot_name': custom_bot.bot_name,
                'customer_id': custom_bot.customer_id,
                'status': 'online' if custom_bot.is_active else 'offline',
                'guilds': 3,  # Would be fetched from actual bot instance
                'users': 75,
                'uptime': '99.8%',
                'last_restart': custom_bot.created_at.strftime('%Y-%m-%d %H:%M:%S') if custom_bot.created_at else None,
                'features_enabled': ['moderation', 'logging', 'automod', 'utility'],
                'commands_used_today': 28,
                'token_configured': bool(custom_bot.bot_token),
                'hosting_status': 'active' if custom_bot.is_active else 'inactive',
                'created_at': custom_bot.created_at.isoformat() if custom_bot.created_at else None,
                'last_online': custom_bot.last_online.isoformat() if custom_bot.last_online else None
            }
            return jsonify({'success': True, 'bot_info': bot_info})
        else:
            # For demo purposes, provide sample data for the owner
            if int(user_id) == 344210326251896834:
                bot_info = {
                    'deployment_id': deployment_id,
                    'bot_name': f'CustomBot-{deployment_id}',
                    'customer_id': int(user_id),
                    'status': 'online',
                    'guilds': 5,
                    'users': 150,
                    'uptime': '99.9%',
                    'last_restart': '2025-07-01 03:30:00',
                    'features_enabled': ['moderation', 'logging', 'automod', 'utility', 'custom_commands'],
                    'commands_used_today': 42,
                    'token_configured': True,
                    'hosting_status': 'active',
                    'created_at': '2025-07-01T00:00:00',
                    'last_online': '2025-07-01T04:00:00'
                }
                return jsonify({'success': True, 'bot_info': bot_info})
            else:
                return jsonify({'success': False, 'error': 'Custom bot not found or access denied'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_manager.close_session(session)

@app.route('/api/dashboard/auto-responses/<guild_id>')
def get_auto_responses(guild_id):
    """Get auto responses for a server"""
    try:
        # Authenticate user via Discord token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'User authentication required'})
        
        from database import DatabaseManager
        db_manager = DatabaseManager()
        responses = db_manager.get_auto_responses(int(guild_id))
        return jsonify({'success': True, 'responses': responses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/auto-responses/<guild_id>', methods=['POST'])
def add_auto_response(guild_id):
    """Add auto response for a server"""
    try:
        # Authenticate user via Discord token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'User authentication required'})
        
        data = request.get_json()
        from database import DatabaseManager
        db_manager = DatabaseManager()
        
        success = db_manager.add_auto_response(
            int(guild_id),
            data.get('trigger'),
            data.get('response'),
            data.get('created_by', 0)
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Auto response added successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to add auto response'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dashboard/auto-responses/<guild_id>/<trigger>', methods=['DELETE'])
def remove_auto_response(guild_id, trigger):
    """Remove auto response for a server"""
    try:
        # Authenticate user via Discord token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'User authentication required'})
        
        from database import DatabaseManager
        db_manager = DatabaseManager()
        success = db_manager.remove_auto_response(int(guild_id), trigger)
        
        if success:
            return jsonify({'success': True, 'message': 'Auto response removed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to remove auto response'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def start_discord_bot():
    """Start Discord bot in background thread"""
    try:
        # Wait for Flask to be ready
        time.sleep(3)
        
        print("Initializing Discord bot...")
        
        # Import bot modules
        from bot.bot import ModBot
        
        # Get token
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            print("Warning: DISCORD_BOT_TOKEN not found")
            return
        
        # Create and run bot
        bot = ModBot()
        
        # Store bot reference for Flask app
        app.discord_bot = bot
        
        # Update status when bot connects
        @bot.event
        async def on_ready():
            bot_status["connected"] = True
            bot_status["guilds"] = len(bot.guilds)
            bot_status["users"] = sum(guild.member_count or 0 for guild in bot.guilds)
            print(f"Bot connected: {bot_status}")
            
            # Call the original bot's status update method
            await bot.update_status()
        
        # Run bot
        bot.run(token)
        
    except Exception as e:
        print(f"Discord bot error: {e}")

def main():
    """Main function for Replit deployment"""
    print("Starting Guardian Bot deployment...")
    
    # Start Discord bot in background
    bot_thread = threading.Thread(target=start_discord_bot, daemon=True)
    bot_thread.start()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting Flask web server on port {port}...")
    
    # Run Flask app with proper production settings
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

if __name__ == "__main__":
    main()