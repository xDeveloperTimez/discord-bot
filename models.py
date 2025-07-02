"""
Database models for Discord bot
"""
import os
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, BigInteger, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Guild(Base):
    """Server/Guild configuration"""
    __tablename__ = 'guilds'
    
    id = Column(BigInteger, primary_key=True)  # Discord guild ID
    name = Column(String(100))
    prefix = Column(String(10), default='.')
    log_channel_id = Column(BigInteger, nullable=True)
    mod_role = Column(String(100), default='Moderator')
    admin_role = Column(String(100), default='Administrator')
    mute_role = Column(String(100), default='Muted')
    automod_enabled = Column(Boolean, default=True)
    anti_raid_enabled = Column(Boolean, default=False)
    anti_raid_config = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Warning(Base):
    """User warnings"""
    __tablename__ = 'warnings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    moderator_id = Column(BigInteger, nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class MutedUser(Base):
    """Muted users with expiration"""
    __tablename__ = 'muted_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    moderator_id = Column(BigInteger, nullable=False)
    reason = Column(Text)
    expires_at = Column(DateTime, nullable=True)  # None for permanent mute
    created_at = Column(DateTime, default=datetime.utcnow)

class AutoResponse(Base):
    """Auto responses for messages"""
    __tablename__ = 'auto_responses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    trigger = Column(String(255), nullable=False)
    response = Column(Text, nullable=False)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModerationAction(Base):
    """Log of all moderation actions"""
    __tablename__ = 'moderation_actions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    moderator_id = Column(BigInteger, nullable=False)
    target_id = Column(BigInteger, nullable=False)
    action_type = Column(String(50), nullable=False)  # kick, ban, warn, mute, etc.
    reason = Column(Text)
    duration = Column(String(50), nullable=True)  # For timed actions
    created_at = Column(DateTime, default=datetime.utcnow)

class AntiRaidLog(Base):
    """Anti-raid system logs"""
    __tablename__ = 'anti_raid_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False)
    event_type = Column(String(50), nullable=False)  # join_spike, message_spam, etc.
    affected_users = Column(JSON, default=[])  # List of user IDs
    action_taken = Column(String(100))  # lockdown, ban, etc.
    details = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class License(Base):
    """User licenses and keys"""
    __tablename__ = 'licenses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    license_key = Column(String(50), nullable=False, unique=True)
    license_type = Column(String(20), nullable=False)  # BASIC, PREMIUM, EXCLUSIVE
    status = Column(String(20), default='ACTIVE')  # ACTIVE, EXPIRED, SUSPENDED
    expires_at = Column(DateTime, nullable=True)  # None for permanent
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Payment tracking
    payment_method = Column(String(20))  # BTC, PAYPAL
    payment_reference = Column(String(255))  # Transaction ID or PayPal reference
    amount_paid = Column(String(20))  # Amount in USD
    
    # Usage tracking
    commands_used = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)


class LicenseKey(Base):
    """Available license keys for purchase"""
    __tablename__ = 'license_keys'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key_code = Column(String(50), nullable=False, unique=True)
    license_type = Column(String(20), nullable=False)  # BASIC, PREMIUM, EXCLUSIVE
    price_usd = Column(String(10), nullable=False)
    duration_days = Column(Integer, nullable=True)  # None for permanent
    status = Column(String(20), default='AVAILABLE')  # AVAILABLE, SOLD, RESERVED
    created_at = Column(DateTime, default=datetime.utcnow)
    sold_at = Column(DateTime, nullable=True)
    sold_to = Column(BigInteger, nullable=True)  # User ID who purchased


class PaymentTransaction(Base):
    """Payment transaction history"""
    __tablename__ = 'payment_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    transaction_id = Column(String(255), nullable=False, unique=True)
    payment_method = Column(String(20), nullable=False)  # BTC, PAYPAL
    amount = Column(String(20), nullable=False)
    currency = Column(String(10), default='USD')
    status = Column(String(20), default='PENDING')  # PENDING, CONFIRMED, FAILED
    license_type = Column(String(20), nullable=False)
    license_key = Column(String(50), nullable=True)  # Generated after confirmation
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)


class SupportTicket(Base):
    """Customer support tickets"""
    __tablename__ = 'support_tickets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(20), nullable=False, unique=True)  # TICKET-XXXX
    user_id = Column(BigInteger, nullable=False)
    guild_id = Column(BigInteger, nullable=True)  # Where ticket was created
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default='OPEN')  # OPEN, IN_PROGRESS, CLOSED
    priority = Column(String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    category = Column(String(50), default='GENERAL')  # GENERAL, TECHNICAL, BILLING, REFUND
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    # Support staff assignment
    assigned_to = Column(BigInteger, nullable=True)  # Staff user ID
    assigned_at = Column(DateTime, nullable=True)


class TicketMessage(Base):
    """Support ticket messages/replies"""
    __tablename__ = 'ticket_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(20), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    is_staff_reply = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SalesAnalytics(Base):
    """Sales and revenue tracking"""
    __tablename__ = 'sales_analytics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    license_type = Column(String(20), nullable=False)
    payment_method = Column(String(20), nullable=False)
    sales_count = Column(Integer, default=0)
    revenue_usd = Column(String(20), default='0.00')
    created_at = Column(DateTime, default=datetime.utcnow)


class CustomBot(Base):
    """Custom bot deployments for customers"""
    __tablename__ = 'custom_bots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    deployment_id = Column(String(50), unique=True, nullable=False)
    customer_id = Column(BigInteger, nullable=False)  # Discord user ID
    bot_token = Column(String(100), nullable=False)  # Encrypted/hashed in production
    bot_name = Column(String(100), nullable=False)
    replit_url = Column(String(255), nullable=True)
    uptime_monitor_url = Column(String(255), nullable=True)
    status = Column(String(20), default='ACTIVE')  # ACTIVE, SUSPENDED, TERMINATED
    features_enabled = Column(Text, nullable=True)  # JSON string of enabled features
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_online = Column(DateTime, nullable=True)
    
    # Deployment metadata
    deployment_notes = Column(Text, nullable=True)
    setup_completed = Column(Boolean, default=False)
    customer_notified = Column(Boolean, default=False)

# Database setup
def get_database_url():
    """Get database URL from environment"""
    return os.environ.get('DATABASE_URL')

def create_tables():
    """Create all database tables"""
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get database session"""
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize database on import
if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")