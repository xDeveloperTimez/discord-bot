"""
Database manager for Discord bot
"""
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from models import Base, Guild, Warning, MutedUser, AutoResponse, ModerationAction, AntiRaidLog
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

class DatabaseManager:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(self.engine)
            print("✓ Database tables created successfully")
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        try:
            session.close()
        except:
            pass
    
    # Guild Management
    def get_or_create_guild(self, guild_id: int, guild_name: str = None) -> Guild:
        """Get or create guild configuration"""
        session = self.get_session()
        try:
            guild = session.query(Guild).filter(Guild.id == guild_id).first()
            if not guild:
                guild = Guild(
                    id=guild_id,
                    name=guild_name or f"Guild {guild_id}",
                    anti_raid_config={
                        "enabled": False,
                        "join_threshold": 5,
                        "message_threshold": 15,
                        "auto_lockdown": False,
                        "auto_ban_raiders": False,
                        "sensitivity": "medium"
                    }
                )
                session.add(guild)
                session.commit()
            return guild
        except Exception as e:
            session.rollback()
            print(f"Error getting/creating guild: {e}")
            return None
        finally:
            self.close_session(session)
    
    def update_guild_config(self, guild_id: int, **kwargs) -> bool:
        """Update guild configuration"""
        session = self.get_session()
        try:
            guild = session.query(Guild).filter(Guild.id == guild_id).first()
            if guild:
                for key, value in kwargs.items():
                    if hasattr(guild, key):
                        setattr(guild, key, value)
                guild.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error updating guild config: {e}")
            return False
        finally:
            self.close_session(session)
    
    # Warning System
    def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        """Add a warning and return total warning count"""
        session = self.get_session()
        try:
            warning = Warning(
                guild_id=guild_id,
                user_id=user_id,
                moderator_id=moderator_id,
                reason=reason
            )
            session.add(warning)
            session.commit()
            
            # Get total warning count
            count = session.query(Warning).filter(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id
            ).count()
            return count
        except Exception as e:
            session.rollback()
            print(f"Error adding warning: {e}")
            return 0
        finally:
            self.close_session(session)
    
    def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        """Get all warnings for a user"""
        session = self.get_session()
        try:
            warnings = session.query(Warning).filter(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id
            ).order_by(Warning.created_at.desc()).all()
            
            return [{
                'id': w.id,
                'reason': w.reason,
                'moderator_id': w.moderator_id,
                'created_at': w.created_at
            } for w in warnings]
        except Exception as e:
            print(f"Error getting warnings: {e}")
            return []
        finally:
            self.close_session(session)
    
    def clear_warnings(self, guild_id: int, user_id: int) -> int:
        """Clear all warnings for a user and return count cleared"""
        session = self.get_session()
        try:
            count = session.query(Warning).filter(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id
            ).count()
            
            session.query(Warning).filter(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id
            ).delete()
            session.commit()
            return count
        except Exception as e:
            session.rollback()
            print(f"Error clearing warnings: {e}")
            return 0
        finally:
            self.close_session(session)
    
    # Mute System
    def add_mute(self, guild_id: int, user_id: int, moderator_id: int, reason: str, duration: Optional[timedelta] = None):
        """Add a muted user"""
        session = self.get_session()
        try:
            # Remove existing mute if any
            session.query(MutedUser).filter(
                MutedUser.guild_id == guild_id,
                MutedUser.user_id == user_id
            ).delete()
            
            expires_at = None
            if duration:
                expires_at = datetime.utcnow() + duration
            
            mute = MutedUser(
                guild_id=guild_id,
                user_id=user_id,
                moderator_id=moderator_id,
                reason=reason,
                expires_at=expires_at
            )
            session.add(mute)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error adding mute: {e}")
        finally:
            self.close_session(session)
    
    def remove_mute(self, guild_id: int, user_id: int):
        """Remove a user from muted list"""
        session = self.get_session()
        try:
            session.query(MutedUser).filter(
                MutedUser.guild_id == guild_id,
                MutedUser.user_id == user_id
            ).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error removing mute: {e}")
        finally:
            self.close_session(session)
    
    def is_muted(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is muted"""
        session = self.get_session()
        try:
            mute = session.query(MutedUser).filter(
                MutedUser.guild_id == guild_id,
                MutedUser.user_id == user_id
            ).first()
            
            if not mute:
                return False
            
            # Check if mute has expired
            if mute.expires_at and mute.expires_at <= datetime.utcnow():
                # Remove expired mute
                session.delete(mute)
                session.commit()
                return False
            
            return True
        except Exception as e:
            print(f"Error checking mute status: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_expired_mutes(self, guild_id: int) -> List[int]:
        """Get list of user IDs whose mutes have expired"""
        session = self.get_session()
        try:
            expired_mutes = session.query(MutedUser).filter(
                MutedUser.guild_id == guild_id,
                MutedUser.expires_at <= datetime.utcnow(),
                MutedUser.expires_at.isnot(None)
            ).all()
            
            user_ids = [mute.user_id for mute in expired_mutes]
            
            # Remove expired mutes
            for mute in expired_mutes:
                session.delete(mute)
            session.commit()
            
            return user_ids
        except Exception as e:
            session.rollback()
            print(f"Error getting expired mutes: {e}")
            return []
        finally:
            self.close_session(session)
    
    # Auto Responses
    def add_auto_response(self, guild_id: int, trigger: str, response: str, created_by: int) -> bool:
        """Add an auto response"""
        session = self.get_session()
        try:
            # Remove existing response with same trigger
            session.query(AutoResponse).filter(
                AutoResponse.guild_id == guild_id,
                AutoResponse.trigger == trigger
            ).delete()
            
            auto_response = AutoResponse(
                guild_id=guild_id,
                trigger=trigger,
                response=response,
                created_by=created_by
            )
            session.add(auto_response)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding auto response: {e}")
            return False
        finally:
            self.close_session(session)
    
    def remove_auto_response(self, guild_id: int, trigger: str) -> bool:
        """Remove an auto response"""
        session = self.get_session()
        try:
            deleted = session.query(AutoResponse).filter(
                AutoResponse.guild_id == guild_id,
                AutoResponse.trigger == trigger
            ).delete()
            session.commit()
            return deleted > 0
        except Exception as e:
            session.rollback()
            print(f"Error removing auto response: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_auto_responses(self, guild_id: int) -> Dict[str, str]:
        """Get all auto responses for a guild"""
        session = self.get_session()
        try:
            responses = session.query(AutoResponse).filter(
                AutoResponse.guild_id == guild_id
            ).all()
            
            return {r.trigger: r.response for r in responses}
        except Exception as e:
            print(f"Error getting auto responses: {e}")
            return {}
        finally:
            self.close_session(session)
    
    # Moderation Logging
    def log_moderation_action(self, guild_id: int, moderator_id: int, target_id: int, 
                            action_type: str, reason: str = None, duration: str = None):
        """Log a moderation action"""
        session = self.get_session()
        try:
            action = ModerationAction(
                guild_id=guild_id,
                moderator_id=moderator_id,
                target_id=target_id,
                action_type=action_type,
                reason=reason,
                duration=duration
            )
            session.add(action)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error logging moderation action: {e}")
        finally:
            self.close_session(session)
    
    # Anti-Raid Logging
    def log_anti_raid_event(self, guild_id: int, event_type: str, affected_users: List[int], 
                          action_taken: str, details: Dict = None):
        """Log an anti-raid event"""
        session = self.get_session()
        try:
            log_entry = AntiRaidLog(
                guild_id=guild_id,
                event_type=event_type,
                affected_users=affected_users,
                action_taken=action_taken,
                details=details or {}
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error logging anti-raid event: {e}")
        finally:
            self.close_session(session)
    
    # License Management Methods
    def get_user_license(self, user_id: int):
        """Get user's license information"""
        session = self.get_session()
        try:
            from models import License
            license_obj = session.query(License).filter_by(user_id=user_id).first()
            return license_obj
        finally:
            self.close_session(session)
    
    def create_license(self, user_id: int, license_key: str, license_type: str, 
                      expires_at=None, payment_method=None, payment_reference=None, amount_paid=None):
        """Create a new license for a user"""
        session = self.get_session()
        try:
            from models import License
            from datetime import datetime
            
            # Check if user already has a license
            existing = session.query(License).filter_by(user_id=user_id).first()
            if existing:
                # Update existing license
                existing.license_key = license_key
                existing.license_type = license_type
                existing.status = 'ACTIVE'
                existing.expires_at = expires_at
                existing.payment_method = payment_method
                existing.payment_reference = payment_reference
                existing.amount_paid = amount_paid
                existing.updated_at = datetime.utcnow()
                license_obj = existing
            else:
                # Create new license
                license_obj = License(
                    user_id=user_id,
                    license_key=license_key,
                    license_type=license_type,
                    expires_at=expires_at,
                    payment_method=payment_method,
                    payment_reference=payment_reference,
                    amount_paid=amount_paid
                )
                session.add(license_obj)
            
            session.commit()
            return license_obj
            
        except Exception as e:
            session.rollback()
            print(f"Error creating license: {e}")
            return None
        finally:
            self.close_session(session)
    
    def check_user_access(self, user_id: int, required_level: str = 'BASIC') -> bool:
        """Check if user has access to specific features"""
        license_obj = self.get_user_license(user_id)
        if not license_obj:
            return False
        
        if license_obj.status != 'ACTIVE':
            return False
        
        # Check expiration
        if license_obj.expires_at:
            from datetime import datetime
            if datetime.utcnow() > license_obj.expires_at:
                return False
        
        # Check license level - handle both old and new license types
        levels = {
            'BASIC': 1, 'BASIC_MONTHLY': 1, 'BASIC_YEARLY': 1,
            'PREMIUM': 2, 'PREMIUM_MONTHLY': 2, 'PREMIUM_YEARLY': 2,
            'EXCLUSIVE': 3, 'EXCLUSIVE_MONTHLY': 3
        }
        
        # Normalize license type to base type for comparison
        user_license_base = license_obj.license_type.replace('_MONTHLY', '').replace('_YEARLY', '')
        user_level = levels.get(license_obj.license_type, levels.get(user_license_base, 0))
        required_level_num = levels.get(required_level, 1)
        
        return user_level >= required_level_num
    
    def update_license_usage(self, user_id: int):
        """Update license usage statistics"""
        session = self.get_session()
        try:
            from models import License
            from datetime import datetime
            
            license_obj = session.query(License).filter_by(user_id=user_id).first()
            if license_obj:
                license_obj.commands_used += 1
                license_obj.last_used = datetime.utcnow()
                session.commit()
                
        except Exception as e:
            session.rollback()
            print(f"Error updating license usage: {e}")
        finally:
            self.close_session(session)
    
    def generate_license_key(self, license_type: str, price_usd: str, duration_days: int = None) -> str:
        """Generate a new license key"""
        session = self.get_session()
        try:
            from models import LicenseKey
            import random, string
            
            # Generate unique key
            while True:
                key_code = f"GUARD-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
                
                # Check if key already exists
                existing = session.query(LicenseKey).filter_by(key_code=key_code).first()
                if not existing:
                    break
            
            # Create license key record
            license_key = LicenseKey(
                key_code=key_code,
                license_type=license_type,
                price_usd=price_usd,
                duration_days=duration_days
            )
            
            session.add(license_key)
            session.commit()
            
            return key_code
            
        except Exception as e:
            session.rollback()
            print(f"Error generating license key: {e}")
            return None
        finally:
            self.close_session(session)
    
    def redeem_license_key(self, user_id: int, key_code: str) -> bool:
        """Redeem a license key"""
        session = self.get_session()
        try:
            from models import LicenseKey
            from datetime import datetime, timedelta
            
            # Find the key
            key_obj = session.query(LicenseKey).filter_by(key_code=key_code, status='AVAILABLE').first()
            if not key_obj:
                return False
            
            # Calculate expiration
            expires_at = None
            if key_obj.duration_days:
                expires_at = datetime.utcnow() + timedelta(days=key_obj.duration_days)
            
            # Create license
            license_obj = self.create_license(
                user_id=user_id,
                license_key=key_code,
                license_type=key_obj.license_type,
                expires_at=expires_at
            )
            
            if license_obj:
                # Mark key as sold
                key_obj.status = 'SOLD'
                key_obj.sold_at = datetime.utcnow()
                key_obj.sold_to = user_id
                session.commit()
                return True
                
            return False
            
        except Exception as e:
            session.rollback()
            print(f"Error redeeming license key: {e}")
            return False
        finally:
            self.close_session(session)
    
    def create_payment_transaction(self, user_id: int, transaction_id: str, payment_method: str, 
                                 amount: str, license_type: str) -> bool:
        """Create a payment transaction record"""
        session = self.get_session()
        try:
            from models import PaymentTransaction
            
            transaction = PaymentTransaction(
                user_id=user_id,
                transaction_id=transaction_id,
                payment_method=payment_method,
                amount=amount,
                license_type=license_type
            )
            
            session.add(transaction)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error creating payment transaction: {e}")
            return False
        finally:
            self.close_session(session)
    
    def confirm_payment_transaction(self, transaction_id: str) -> bool:
        """Confirm a payment transaction and generate license"""
        session = self.get_session()
        try:
            from models import PaymentTransaction
            from datetime import datetime
            
            transaction = session.query(PaymentTransaction).filter_by(
                transaction_id=transaction_id, 
                status='PENDING'
            ).first()
            
            if not transaction:
                return False
            
            # Generate license key
            license_key = self.generate_license_key(
                license_type=transaction.license_type,
                price_usd=transaction.amount,
                duration_days=365 if transaction.license_type in ['BASIC', 'PREMIUM'] else None
            )
            
            if license_key:
                # Update transaction
                transaction.status = 'CONFIRMED'
                transaction.license_key = license_key
                transaction.confirmed_at = datetime.utcnow()
                
                # Auto-redeem for user
                self.redeem_license_key(transaction.user_id, license_key)
                
                session.commit()
                return True
                
            return False
            
        except Exception as e:
            session.rollback()
            print(f"Error confirming payment transaction: {e}")
            return False
        finally:
            self.close_session(session)
    
    def create_support_ticket(self, user_id: int, guild_id: int, subject: str, description: str, 
                            category: str = 'GENERAL') -> str:
        """Create a support ticket"""
        session = self.get_session()
        try:
            from models import SupportTicket, TicketMessage
            import random
            
            # Generate ticket ID
            ticket_id = f"TICKET-{random.randint(1000, 9999)}"
            
            # Ensure unique ticket ID
            while session.query(SupportTicket).filter_by(ticket_id=ticket_id).first():
                ticket_id = f"TICKET-{random.randint(1000, 9999)}"
            
            # Create ticket
            ticket = SupportTicket(
                ticket_id=ticket_id,
                user_id=user_id,
                guild_id=guild_id,
                subject=subject,
                description=description,
                category=category
            )
            
            session.add(ticket)
            
            # Add initial message
            message = TicketMessage(
                ticket_id=ticket_id,
                user_id=user_id,
                message=description,
                is_staff_reply=False
            )
            
            session.add(message)
            session.commit()
            
            return ticket_id
            
        except Exception as e:
            session.rollback()
            print(f"Error creating support ticket: {e}")
            return None
        finally:
            self.close_session(session)
    
    def get_user_tickets(self, user_id: int):
        """Get all tickets for a user"""
        session = self.get_session()
        try:
            from models import SupportTicket
            tickets = session.query(SupportTicket).filter_by(user_id=user_id).order_by(SupportTicket.created_at.desc()).all()
            return tickets
        finally:
            self.close_session(session)
    
    def get_sales_stats(self) -> Dict:
        """Get sales statistics"""
        session = self.get_session()
        try:
            from models import PaymentTransaction, License
            from datetime import datetime, timedelta
            
            # Total sales
            total_sales = session.query(PaymentTransaction).filter_by(status='CONFIRMED').count()
            
            # Revenue
            transactions = session.query(PaymentTransaction).filter_by(status='CONFIRMED').all()
            total_revenue = sum(float(t.amount) for t in transactions)
            
            # Active licenses
            active_licenses = session.query(License).filter_by(status='ACTIVE').count()
            
            # Sales by type
            basic_sales = session.query(PaymentTransaction).filter_by(status='CONFIRMED', license_type='BASIC').count()
            premium_sales = session.query(PaymentTransaction).filter_by(status='CONFIRMED', license_type='PREMIUM').count()
            exclusive_sales = session.query(PaymentTransaction).filter_by(status='CONFIRMED', license_type='EXCLUSIVE').count()
            
            # Recent sales (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_sales = session.query(PaymentTransaction).filter(
                PaymentTransaction.status == 'CONFIRMED',
                PaymentTransaction.confirmed_at >= thirty_days_ago
            ).count()
            
            return {
                'total_sales': total_sales,
                'total_revenue': f"${total_revenue:.2f}",
                'active_licenses': active_licenses,
                'basic_sales': basic_sales,
                'premium_sales': premium_sales,
                'exclusive_sales': exclusive_sales,
                'recent_sales': recent_sales
            }
            
        finally:
            self.close_session(session)
    
    def create_custom_bot(self, deployment_id: str, customer_id: int, bot_token: str, bot_name: str) -> bool:
        """Create a custom bot deployment record"""
        session = self.get_session()
        try:
            from models import CustomBot
            from datetime import datetime
            
            # Create custom bot record
            custom_bot = CustomBot(
                deployment_id=deployment_id,
                customer_id=customer_id,
                bot_token=bot_token,
                bot_name=bot_name,
                status='ACTIVE',
                setup_completed=True,
                customer_notified=False,
                created_at=datetime.utcnow()
            )
            
            session.add(custom_bot)
            session.commit()
            
            print(f"✓ Created custom bot deployment: {deployment_id} for customer {customer_id}")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error creating custom bot deployment: {e}")
            return False
        finally:
            self.close_session(session)

# Global database manager instance
db_manager = DatabaseManager()