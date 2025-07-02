"""
Standalone Purchase Bot for Guardian Bot License Sales
This bot handles all purchase operations and can be run separately from the main bot
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import aiohttp
import json
import os
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List
from database import DatabaseManager


class PurchaseBot(commands.Bot):
    """Standalone purchase bot for license sales"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='$',
            intents=intents,
            description='Guardian Bot Purchase System'
        )
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Pricing configuration with monthly and yearly options
        self.pricing = {
            'BASIC_MONTHLY': {'price': '4.99', 'duration': 30, 'features': ['Core moderation', 'Utility commands', 'Auto-moderation']},
            'BASIC_YEARLY': {'price': '29.99', 'duration': 365, 'features': ['Core moderation', 'Utility commands', 'Auto-moderation']},
            'PREMIUM_MONTHLY': {'price': '9.99', 'duration': 30, 'features': ['All Basic features', 'Music system', 'Advanced anti-raid', 'Enhanced spam protection']},
            'PREMIUM_YEARLY': {'price': '59.99', 'duration': 365, 'features': ['All Basic features', 'Music system', 'Advanced anti-raid', 'Enhanced spam protection']},
            'EXCLUSIVE_MONTHLY': {'price': '19.99', 'duration': 30, 'features': ['All Premium features', 'Priority support', 'Custom features']},
            'EXCLUSIVE': {'price': '99.99', 'duration': None, 'features': ['All Premium features', 'Lifetime access', 'Priority support', 'Custom features']},
            'CUSTOM_BOT': {'price': '50.00', 'duration': None, 'features': ['Your own personal bot', 'All Guardian features', 'Custom branding', 'Private hosting', 'Full source code', 'Setup assistance']}
        }
        
        # Your payment details
        self.btc_address = "bc1qa29gd8cec3n8cndl8ge9nf3p6wks9ddqqcww6s"
        self.paypal_email = "lanagotcake@gmail.com"
        self.discord_server = "https://discord.gg/FQvU3DAgCk"
        
        # Bot owner for admin commands
        self.owner_id = 344210326251896834

    async def setup_hook(self):
        """Initialize the bot"""
        print("Setting up Purchase Bot...")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            print(f"✓ Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"✗ Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f"\n💰 {self.user} is now online!")
        print(f"📊 Connected to {len(self.guilds)} guilds")
        print(f"🛒 Ready to process license purchases")
        
        # Set activity
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for license purchases 💰"
        )
        await self.change_presence(activity=activity)


class PaymentView(discord.ui.View):
    """Payment selection view"""
    def __init__(self, bot, license_type: str, price: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.license_type = license_type
        self.price = price

    @discord.ui.button(label="₿ Bitcoin", style=discord.ButtonStyle.primary)
    async def bitcoin_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle Bitcoin payment"""
        embed = discord.Embed(
            title="₿ Bitcoin Payment Instructions",
            description=f"**License:** {self.license_type}\n**Price:** ${self.price} USD",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="📍 Send Bitcoin to:",
            value=f"`{self.bot.btc_address}`",
            inline=False
        )
        embed.add_field(
            name="💰 Amount",
            value=f"Send the current USD equivalent of **${self.price}** in Bitcoin",
            inline=False
        )
        embed.add_field(
            name="✅ After Payment",
            value="Use `$verify btc <transaction_id>` to verify your payment and receive your license key automatically.",
            inline=False
        )
        embed.add_field(
            name="⚡ Important Notes",
            value="• Send the exact USD equivalent in BTC\n• Wait for blockchain confirmation\n• Keep your transaction ID\n• Verification is automatic",
            inline=False
        )
        
        embed.set_footer(text="⚠️ Make sure to send the exact amount and use the verify command after payment!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="💳 PayPal", style=discord.ButtonStyle.success)
    async def paypal_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle PayPal payment"""
        embed = discord.Embed(
            title="💳 PayPal Payment Instructions",
            description=f"**License:** {self.license_type}\n**Price:** ${self.price} USD",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📧 Send Payment to:",
            value=f"{self.bot.paypal_email}",
            inline=False
        )
        embed.add_field(
            name="💰 Amount",
            value=f"**${self.price} USD**",
            inline=False
        )
        embed.add_field(
            name="📝 Required Note",
            value=f"License: {self.license_type} for Discord User: {interaction.user.id}",
            inline=False
        )
        embed.add_field(
            name="✅ After Payment",
            value="Use `$verify paypal <transaction_id>` or contact support with your PayPal transaction ID.",
            inline=False
        )
        embed.add_field(
            name="📞 Support",
            value=f"Join our Discord server: {self.bot.discord_server}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TicketCategorySelect(discord.ui.Select):
    """Dropdown for selecting ticket category"""
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label="Purchase Support", 
                value="PURCHASE",
                description="Help with buying licenses or payment issues",
                emoji="🛒"
            ),
            discord.SelectOption(
                label="Technical Support", 
                value="TECHNICAL",
                description="Bot functionality or command issues",
                emoji="🔧"
            ),
            discord.SelectOption(
                label="Refund Request", 
                value="REFUND",
                description="Request a refund for your purchase",
                emoji="💰"
            ),
            discord.SelectOption(
                label="General Support", 
                value="GENERAL",
                description="General questions or other issues",
                emoji="💬"
            )
        ]
        super().__init__(placeholder="Select ticket category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        modal = SupportTicketModal(self.bot, category)
        await interaction.response.send_modal(modal)


class TicketPanelView(discord.ui.View):
    """Enhanced ticket panel with buttons and dropdown"""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(TicketCategorySelect(bot))

    @discord.ui.button(label="🎫 Create Ticket", style=discord.ButtonStyle.primary, row=1)
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick ticket creation button"""
        modal = SupportTicketModal(self.bot, "GENERAL")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="❓ FAQ", style=discord.ButtonStyle.secondary, row=1)
    async def faq_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show frequently asked questions"""
        embed = discord.Embed(
            title="❓ Frequently Asked Questions",
            description="Common questions and answers",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💳 How do I purchase a license?",
            value="Use `/buy` command to see pricing and payment options. We accept Bitcoin (automatic) and PayPal (manual review).",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ How long does activation take?",
            value="Bitcoin payments are verified automatically. PayPal payments are reviewed manually within 24 hours.",
            inline=False
        )
        
        embed.add_field(
            name="💰 What if I want a refund?",
            value="Create a refund ticket with your transaction details. Refunds are reviewed case-by-case.",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Bot not working?",
            value="First check your license status with `/license` on the main bot. Create a technical support ticket if issues persist.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📊 My Tickets", style=discord.ButtonStyle.secondary, row=1)
    async def my_tickets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show user's tickets"""
        tickets = self.bot.db_manager.get_user_tickets(interaction.user.id)
        
        if not tickets:
            embed = discord.Embed(
                title="📋 No Tickets Found",
                description="You don't have any support tickets.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎫 Your Support Tickets",
            color=discord.Color.blue()
        )
        
        for ticket in tickets[:5]:  # Show last 5 tickets
            status_emoji = "🟢" if ticket.status == "OPEN" else "🟡" if ticket.status == "IN_PROGRESS" else "🔴"
            embed.add_field(
                name=f"{status_emoji} {ticket.ticket_id}",
                value=f"**Subject:** {ticket.subject}\n**Status:** {ticket.status}\n**Created:** <t:{int(ticket.created_at.timestamp())}:R>",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class SupportTicketModal(discord.ui.Modal):
    """Modal for creating support tickets with predefined category"""
    def __init__(self, bot, category="GENERAL"):
        super().__init__(title=f"Create {category.title()} Ticket")
        self.bot = bot
        self.category = category

    subject = discord.ui.TextInput(
        label="Subject",
        placeholder="Brief description of your issue...",
        max_length=200,
        required=True
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="Detailed description of your issue...",
        style=discord.TextStyle.paragraph,
        max_length=2000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Send immediate response to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Create ticket channel in specified category
            guild = interaction.guild
            print(f"🔍 PURCHASE BOT DEBUG: Guild: {guild.name if guild else 'None'} (ID: {guild.id if guild else 'None'})")
            
            if not guild:
                await interaction.followup.send("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            # Get the ticket category channel
            ticket_category_id = 1389368950571405414
            print(f"🔍 PURCHASE BOT DEBUG: Looking for category ID: {ticket_category_id}")
            
            category = guild.get_channel(ticket_category_id)
            print(f"🔍 PURCHASE BOT DEBUG: Category found: {category.name if category else 'None'} (Type: {type(category).__name__ if category else 'None'})")
            
            if not category:
                # Let's list all channels to debug
                all_channels = guild.channels
                print(f"🔍 PURCHASE BOT DEBUG: All guild channels ({len(all_channels)}):")
                for ch in all_channels:
                    print(f"  - {ch.name} (ID: {ch.id}, Type: {type(ch).__name__})")
                
                await interaction.followup.send(f"❌ Ticket category channel not found. Looking for ID: {ticket_category_id}. Please contact an administrator.", ephemeral=True)
                return
            
            # Ensure category is a CategoryChannel
            if not isinstance(category, discord.CategoryChannel):
                print(f"🔍 PURCHASE BOT DEBUG: ERROR - Category is not a CategoryChannel! Type: {type(category).__name__}")
                await interaction.followup.send(f"❌ Found channel but it's not a category (Type: {type(category).__name__}). Please ensure ID {ticket_category_id} is a category channel.", ephemeral=True)
                return
            
            # Generate unique ticket ID
            import random
            import string
            ticket_number = ''.join(random.choices(string.digits, k=4))
            
            # Create ticket channel
            channel_name = f"ticket-{interaction.user.name}-{ticket_number}"
            print(f"🔍 PURCHASE BOT DEBUG: Creating channel: {channel_name}")
            
            # Set permissions for the ticket channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                )
            }
            
            # Add admin permissions (bot owner)
            owner = guild.get_member(344210326251896834)
            print(f"🔍 PURCHASE BOT DEBUG: Bot owner found: {owner.name if owner else 'None'}")
            if owner:
                overwrites[owner] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True,
                    embed_links=True,
                    attach_files=True,
                    read_message_history=True
                )
            
            print(f"🔍 PURCHASE BOT DEBUG: Permission overwrites set up for {len(overwrites)} entities")
            print(f"🔍 PURCHASE BOT DEBUG: Bot permissions in guild: {guild.me.guild_permissions}")
            print(f"🔍 PURCHASE BOT DEBUG: Can manage channels: {guild.me.guild_permissions.manage_channels}")
            
            # Create the channel
            print(f"🔍 PURCHASE BOT DEBUG: Attempting to create channel in category: {category.name}")
            ticket_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Support ticket for {interaction.user} | Subject: {self.subject.value}"
            )
            print(f"🔍 PURCHASE BOT DEBUG: Channel created successfully: {ticket_channel.name} (ID: {ticket_channel.id})")
            print(f"🔍 PURCHASE BOT DEBUG: Channel category: {ticket_channel.category.name if ticket_channel.category else 'None'}")
            
            # Create initial ticket embed
            ticket_embed = discord.Embed(
                title="🎫 Support Ticket Created",
                description=f"**User:** {interaction.user.mention}\n**Subject:** {self.subject.value}\n**Category:** {self.category}",
                color=discord.Color.blue(),
                timestamp=interaction.created_at
            )
            ticket_embed.add_field(
                name="📝 Description",
                value=self.description.value,
                inline=False
            )
            ticket_embed.add_field(
                name="ℹ️ Information",
                value="• A support team member will assist you shortly\n• Use this channel to provide additional details\n• Click 🔒 to close this ticket when resolved",
                inline=False
            )
            ticket_embed.set_footer(text=f"Ticket #{ticket_number}")
            
            # Add close button (import from main bot)
            from cogs.licensing import TicketCloseView
            close_view = TicketCloseView()
            
            # Send initial message in ticket channel
            await ticket_channel.send(
                content=f"{interaction.user.mention} | <@344210326251896834>",
                embed=ticket_embed,
                view=close_view
            )
            
            # Store ticket in database for tracking
            ticket_id = self.bot.db_manager.create_support_ticket(
                user_id=interaction.user.id,
                guild_id=interaction.guild.id,
                subject=str(self.subject.value),
                description=f"Channel: {ticket_channel.mention}\n\n{self.description.value}",
                category=self.category
            )
            
            # Respond to user
            response_embed = discord.Embed(
                title="✅ Ticket Created Successfully",
                description=f"Your support ticket has been created in {ticket_channel.mention}",
                color=discord.Color.green()
            )
            response_embed.add_field(
                name="Ticket Details",
                value=f"**Number:** #{ticket_number}\n**Subject:** {self.subject.value}\n**Channel:** {ticket_channel.mention}",
                inline=False
            )
            
            await interaction.followup.send(embed=response_embed, ephemeral=True)
            
        except Exception as e:
            print(f"🔍 PURCHASE BOT DEBUG: Exception occurred: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Error Creating Ticket",
                description=f"Failed to create support ticket: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


class AdminPanel(discord.ui.View):
    """Admin panel for license management"""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="📊 Sales Stats", style=discord.ButtonStyle.primary)
    async def sales_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show sales statistics"""
        stats = self.bot.db_manager.get_sales_stats()
        
        embed = discord.Embed(
            title="📊 Sales Analytics Dashboard",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="💰 Total Revenue", value=stats['total_revenue'], inline=True)
        embed.add_field(name="📈 Total Sales", value=f"{stats['total_sales']:,}", inline=True)
        embed.add_field(name="👥 Active Licenses", value=f"{stats['active_licenses']:,}", inline=True)
        
        embed.add_field(name="🔰 Basic Sales", value=f"{stats['basic_sales']:,}", inline=True)
        embed.add_field(name="⭐ Premium Sales", value=f"{stats['premium_sales']:,}", inline=True)
        embed.add_field(name="💎 Exclusive Sales", value=f"{stats['exclusive_sales']:,}", inline=True)
        
        embed.add_field(name="📅 Recent Sales (30d)", value=f"{stats['recent_sales']:,}", inline=False)
        
        embed.set_footer(text=f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🔑 Generate Keys", style=discord.ButtonStyle.secondary)
    async def generate_keys(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generate license keys"""
        await interaction.response.send_modal(GenerateKeyModal(self.bot))


class GenerateKeyModal(discord.ui.Modal):
    """Modal for generating license keys"""
    def __init__(self, bot):
        super().__init__(title="Generate License Key")
        self.bot = bot

    license_type = discord.ui.TextInput(
        label="License Type",
        placeholder="BASIC, PREMIUM, or EXCLUSIVE",
        default="BASIC",
        required=True
    )

    price = discord.ui.TextInput(
        label="Price (USD)",
        placeholder="e.g., 29.99",
        required=True
    )

    duration = discord.ui.TextInput(
        label="Duration (days)",
        placeholder="365 for 1 year, leave empty for permanent",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            duration_days = int(self.duration.value) if self.duration.value else None
        except ValueError:
            duration_days = None
        
        key = self.bot.db_manager.generate_license_key(
            license_type=str(self.license_type.value).upper(),
            price_usd=str(self.price.value),
            duration_days=duration_days
        )
        
        if key:
            embed = discord.Embed(
                title="🔑 License Key Generated",
                description=f"**Key:** `{key}`\n**Type:** {self.license_type.value}\n**Price:** ${self.price.value}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to generate license key.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


# Initialize bot
bot = PurchaseBot()

@bot.tree.command(name="buy", description="Purchase a Guardian Bot license")
async def buy_license(interaction: discord.Interaction):
    """Display license purchase options"""
    embed = discord.Embed(
        title="🛒 Guardian Bot Licenses",
        description="Choose your license tier and duration to unlock powerful Discord moderation features:",
        color=discord.Color.gold()
    )
    
    # Basic Tier
    embed.add_field(
        name="🔰 BASIC License",
        value="**Monthly:** $4.99/month\n(30 days)\n**Yearly:** $29.99/year\n(365 days)\n• Core moderation\n• Utility commands\n• Auto-moderation",
        inline=True
    )
    
    # Premium Tier
    embed.add_field(
        name="⭐ PREMIUM License", 
        value="**Monthly:** $9.99/month\n(30 days)\n**Yearly:** $59.99/year\n(365 days)\n• All Basic features\n• Music system\n• Advanced anti-raid\n• Enhanced spam protection",
        inline=True
    )
    
    # Exclusive Tier
    embed.add_field(
        name="💎 EXCLUSIVE License",
        value="**Monthly:** $19.99/month\n(30 days)\n**Lifetime:** $99.99\n(Forever)\n• All Premium features\n• Priority support\n• Custom features",
        inline=True
    )
    
    # Custom Bot Tier
    embed.add_field(
        name="🤖 CUSTOM BOT Setup",
        value="**One-time:** $50.00\n• Your own personal bot\n• All Guardian features\n• Custom branding\n• Private hosting\n• Full source code\n• Setup assistance",
        inline=False
    )
    
    embed.add_field(
        name="💳 Payment Methods",
        value="• Bitcoin (₿)\n• PayPal (💳)",
        inline=False
    )
    
    embed.add_field(
        name="💡 Save Money!",
        value="Choose yearly plans to save money compared to monthly subscriptions!",
        inline=False
    )
    
    embed.set_footer(text="Select a license option below to proceed with payment")
    
    # Create selection dropdown with all options
    select = discord.ui.Select(
        placeholder="Choose your license type and duration...",
        options=[
            discord.SelectOption(
                label="BASIC Monthly - $4.99",
                description="30 days - Core moderation features",
                value="BASIC_MONTHLY",
                emoji="🔰"
            ),
            discord.SelectOption(
                label="BASIC Yearly - $29.99",
                description="365 days - Save $29.89 vs monthly",
                value="BASIC_YEARLY", 
                emoji="🔰"
            ),
            discord.SelectOption(
                label="PREMIUM Monthly - $9.99",
                description="30 days - All Basic + Music & Anti-raid",
                value="PREMIUM_MONTHLY",
                emoji="⭐"
            ),
            discord.SelectOption(
                label="PREMIUM Yearly - $59.99",
                description="365 days - Save $59.89 vs monthly",
                value="PREMIUM_YEARLY",
                emoji="⭐"
            ),
            discord.SelectOption(
                label="EXCLUSIVE Monthly - $19.99",
                description="30 days - All features + Priority support",
                value="EXCLUSIVE_MONTHLY",
                emoji="💎"
            ),
            discord.SelectOption(
                label="EXCLUSIVE Lifetime - $149.99",
                description="Forever - One-time payment for lifetime access",
                value="EXCLUSIVE",
                emoji="💎"
            ),
            discord.SelectOption(
                label="CUSTOM BOT - $50.00",
                description="Your own personal bot with all features",
                value="CUSTOM_BOT",
                emoji="🤖"
            )
        ]
    )
    
    async def select_callback(select_interaction):
        license_type = select.values[0]
        price = bot.pricing[license_type]['price']
        
        embed = discord.Embed(
            title=f"💳 Payment for {license_type} License",
            description=f"You selected: **{license_type}** license for **${price}**",
            color=discord.Color.blue()
        )
        
        view = PaymentView(bot, license_type, price)
        await select_interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    select.callback = select_callback
    view = discord.ui.View()
    view.add_item(select)
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="verify", description="Verify payment and get license key")
@app_commands.describe(
    method="Payment method",
    transaction_id="Transaction ID or reference"
)
@app_commands.choices(method=[
    app_commands.Choice(name="Bitcoin", value="btc"),
    app_commands.Choice(name="PayPal", value="paypal")
])
async def verify_payment(interaction: discord.Interaction, method: str, transaction_id: str):
    """Verify payment and automatically issue license"""
    await interaction.response.defer(ephemeral=True)
    
    if method == "btc":
        # Verify BTC transaction
        success, result = await verify_btc_transaction(transaction_id)
        if success:
            # Extract amount and determine license type
            amount_btc = result.get('amount', 0)
            amount_usd = await btc_to_usd(amount_btc)
            license_type = determine_license_type(amount_usd)
            
            if license_type:
                # Create transaction record
                bot.db_manager.create_payment_transaction(
                    user_id=interaction.user.id,
                    transaction_id=transaction_id,
                    payment_method="BTC",
                    amount=str(amount_usd),
                    license_type=license_type
                )
                
                # Confirm transaction and generate license
                success = bot.db_manager.confirm_payment_transaction(transaction_id)
                
                if success:
                    if license_type == "CUSTOM_BOT":
                        # Create special custom bot setup ticket
                        ticket_id = bot.db_manager.create_support_ticket(
                            user_id=interaction.user.id,
                            guild_id=interaction.guild.id if interaction.guild else 0,
                            subject="Custom Bot Setup Request",
                            description=f"Custom bot setup for user {interaction.user.mention}\nTransaction ID: {transaction_id}\nAmount Paid: ${amount_usd:.2f} USD",
                            category="CUSTOM_BOT"
                        )
                        
                        embed = discord.Embed(
                            title="✅ Custom Bot Order Confirmed!",
                            description=f"Your payment has been verified! A custom bot setup ticket has been created.",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Transaction ID", value=transaction_id, inline=False)
                        embed.add_field(name="Amount", value=f"${amount_usd:.2f} USD", inline=True)
                        embed.add_field(name="Ticket ID", value=ticket_id, inline=True)
                        embed.add_field(
                            name="Next Steps",
                            value="Our team will contact you within 24 hours to set up your custom bot. You'll receive:\n• Your own Discord bot application\n• All Guardian Bot features\n• Custom branding\n• Full source code\n• Setup assistance",
                            inline=False
                        )
                    else:
                        embed = discord.Embed(
                            title="✅ Payment Verified!",
                            description=f"Your Bitcoin payment has been verified and your **{license_type}** license has been activated!",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Transaction ID", value=transaction_id, inline=False)
                        embed.add_field(name="Amount", value=f"${amount_usd:.2f} USD", inline=True)
                        embed.add_field(name="License Type", value=license_type, inline=True)
                        embed.add_field(
                            name="Next Steps",
                            value="Your license is now active! Use the Guardian Bot with all your unlocked features.",
                            inline=False
                        )
                else:
                    embed = discord.Embed(
                        title="❌ Processing Error",
                        description="Payment verified but license generation failed. Contact support.",
                        color=discord.Color.red()
                    )
            else:
                embed = discord.Embed(
                    title="❌ Invalid Amount",
                    description=f"Payment amount (${amount_usd:.2f}) doesn't match any license tier.",
                    color=discord.Color.red()
                )
        else:
            embed = discord.Embed(
                title="❌ Verification Failed",
                description="Could not verify Bitcoin transaction. Please check the transaction ID.",
                color=discord.Color.red()
            )
    
    elif method == "paypal":
        # Record PayPal transaction for manual verification
        bot.db_manager.create_payment_transaction(
            user_id=interaction.user.id,
            transaction_id=transaction_id,
            payment_method="PAYPAL",
            amount="0.00",  # Will be updated manually
            license_type="BASIC"  # Will be updated manually
        )
        
        embed = discord.Embed(
            title="💳 PayPal Verification Submitted",
            description="Your PayPal transaction has been recorded for manual verification.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Transaction ID Recorded",
            value=f"`{transaction_id}`",
            inline=False
        )
        embed.add_field(
            name="Next Steps",
            value="• Our team will verify your PayPal payment\n• License will be activated automatically\n• You'll receive a confirmation message\n• Processing time: Up to 24 hours",
            inline=False
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name="ticket", description="Create or manage support tickets")
@app_commands.describe(action="Ticket action")
@app_commands.choices(action=[
    app_commands.Choice(name="Create", value="create"),
    app_commands.Choice(name="Status", value="status"),
    app_commands.Choice(name="List", value="list")
])
async def ticket_command(interaction: discord.Interaction, action: str):
    """Support ticket management"""
    
    if action == "create":
        modal = SupportTicketModal(bot)
        await interaction.response.send_modal(modal)
    
    elif action == "status" or action == "list":
        tickets = bot.db_manager.get_user_tickets(interaction.user.id)
        
        if not tickets:
            embed = discord.Embed(
                title="📋 No Tickets Found",
                description="You don't have any support tickets.",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Create a Ticket",
                value="Use `$ticket create` to create a new support ticket.",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎫 Your Support Tickets",
            color=discord.Color.blue()
        )
        
        for ticket in tickets[:10]:  # Show last 10 tickets
            status_emoji = "🟢" if ticket.status == "OPEN" else "🟡" if ticket.status == "IN_PROGRESS" else "🔴"
            embed.add_field(
                name=f"{status_emoji} {ticket.ticket_id}",
                value=f"**Subject:** {ticket.subject}\n**Status:** {ticket.status}\n**Created:** <t:{int(ticket.created_at.timestamp())}:R>",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="admin", description="Admin panel for license management")
async def admin_panel(interaction: discord.Interaction):
    """Admin panel for managing licenses (Owner only)"""
    if interaction.user.id != bot.owner_id:
        embed = discord.Embed(
            title="❌ Access Denied",
            description="This command is restricted to bot administrators.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🔧 Purchase Bot Admin Panel",
        description="License management and sales analytics dashboard",
        color=discord.Color.purple()
    )
    
    view = AdminPanel(bot)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="info", description="Information about Guardian Bot and licensing")
async def info_command(interaction: discord.Interaction):
    """Display information about Guardian Bot"""
    embed = discord.Embed(
        title="🛡️ Guardian Bot Information",
        description="Professional Discord moderation bot with advanced features",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🔰 Basic License - $29.99/year",
        value="• Core moderation commands\n• Utility commands\n• Auto-moderation system",
        inline=False
    )
    
    embed.add_field(
        name="⭐ Premium License - $49.99/year",
        value="• All Basic features\n• Music system with voice support\n• Advanced anti-raid protection\n• Enhanced spam protection",
        inline=False
    )
    
    embed.add_field(
        name="💎 Exclusive License - $99.99 (Lifetime)",
        value="• All Premium features\n• Lifetime access\n• Priority support\n• Custom feature requests",
        inline=False
    )
    
    embed.add_field(
        name="💳 Payment Methods",
        value="• Bitcoin (Instant verification)\n• PayPal (Manual verification)",
        inline=True
    )
    
    embed.add_field(
        name="🎫 Support",
        value=f"Join our Discord: {bot.discord_server}",
        inline=True
    )
    
    embed.set_footer(text="Use /buy to purchase a license • Use /ticket to get support")
    
    await interaction.response.send_message(embed=embed)

# Helper functions
async def verify_btc_transaction(tx_id: str):
    """Verify Bitcoin transaction using Blockstream API"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://blockstream.info/api/tx/{tx_id}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if transaction exists and get outputs
                    for output in data.get('vout', []):
                        if output.get('scriptpubkey_address') == bot.btc_address:
                            amount_satoshi = output.get('value', 0)
                            amount_btc = amount_satoshi / 100000000  # Convert satoshi to BTC
                            return True, {'amount': amount_btc, 'confirmed': data.get('status', {}).get('confirmed', False)}
                    
                    return False, "Address not found in transaction"
                else:
                    return False, "Transaction not found"
    except Exception as e:
        return False, f"Error verifying transaction: {str(e)}"

async def btc_to_usd(btc_amount: float) -> float:
    """Convert BTC amount to USD"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.coindesk.com/v1/bpi/currentprice.json"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    btc_price = float(data['bpi']['USD']['rate'].replace(',', ''))
                    return btc_amount * btc_price
    except:
        pass
    return 0.0

def determine_license_type(amount_usd: float) -> str:
    """Determine license type based on payment amount"""
    if amount_usd >= 90:  # Within $10 of EXCLUSIVE lifetime price
        return "EXCLUSIVE"
    elif amount_usd >= 55:  # Within $5 of PREMIUM yearly price
        return "PREMIUM_YEARLY"
    elif amount_usd >= 45:  # Within $5 of CUSTOM_BOT price
        return "CUSTOM_BOT"
    elif amount_usd >= 25:  # Within $5 of BASIC yearly price
        return "BASIC_YEARLY"
    elif amount_usd >= 15:  # Within $5 of EXCLUSIVE monthly price
        return "EXCLUSIVE_MONTHLY"
    elif amount_usd >= 7:  # Within $3 of PREMIUM monthly price
        return "PREMIUM_MONTHLY"
    elif amount_usd >= 3:  # Within $2 of BASIC monthly price
        return "BASIC_MONTHLY"
    return None

# Prefix command for buy
@bot.command(name='buy')
async def buy_prefix(ctx):
    """Interactive license purchase menu (prefix version)"""
    embed = discord.Embed(
        title="🛒 License Purchase Options",
        description="Choose your Guardian Bot license tier",
        color=discord.Color.green()
    )
    
    for license_type, details in bot.pricing.items():
        duration_text = f"{details['duration']} days" if details['duration'] else "Lifetime"
        features_text = "\n".join([f"• {feature}" for feature in details['features'][:3]])  # Show first 3 features
        
        embed.add_field(
            name=f"{'🔰' if license_type == 'BASIC' else '⭐' if license_type == 'PREMIUM' else '💎'} {license_type}",
            value=f"**${details['price']}** - {duration_text}\n{features_text}",
            inline=False
        )
    
    embed.add_field(
        name="💳 Payment Methods",
        value="• Bitcoin (₿)\n• PayPal (💳)",
        inline=False
    )
    
    embed.set_footer(text="Use /buy to get interactive purchase menu with payment buttons")
    
    await ctx.send(embed=embed)

# Additional commands for purchase bot
@bot.hybrid_command(name='purchasecommands', aliases=['purchase_commands'])
async def purchase_commands(ctx):
    """Display all purchase bot commands"""
    embed = discord.Embed(
        title="🛒 Purchase Bot Commands",
        description="Complete list of purchase bot commands",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🛍️ Customer Commands",
        value="""
**$buy** - Interactive license purchase menu
**$verify btc <tx_id>** - Verify Bitcoin payment
**$verify paypal <tx_id>** - Verify PayPal payment  
**$ticket create** - Create support ticket
**$ticket status** - View ticket status
**$info** - License pricing information
**$purchasecommands** - Show this command list
**$buyhelp** - Get purchase help and instructions
        """,
        inline=False
    )
    
    embed.add_field(
        name="👑 Admin Commands (Owner Only)",
        value="""
**$admin** - Admin sales dashboard
**$ticket list** - List all support tickets
        """,
        inline=False
    )
    
    embed.add_field(
        name="💰 Quick Purchase Guide",
        value="""
1. Use **$buy** to see license options
2. Choose your license tier and payment method
3. Send payment to provided address/email
4. Use **$verify** with your transaction ID
5. License activates automatically on main bot
        """,
        inline=False
    )
    
    embed.set_footer(text="Guardian Purchase Bot • Use $buyhelp for detailed instructions")
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name='ticketpanel', aliases=['support_panel'])
async def ticket_panel_command(ctx):
    """Deploy enhanced ticket panel (Owner only)"""
    if ctx.author.id != bot.owner_id:
        await ctx.send("❌ Only the bot owner can deploy the ticket panel.")
        return
    
    embed = discord.Embed(
        title="🎫 Guardian Bot Support Center",
        description="Welcome to Guardian Bot support! Choose how you'd like to get help:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📋 Support Categories",
        value="""
🛒 **Purchase Support** - Help with buying licenses or payment issues
🔧 **Technical Support** - Bot functionality or command issues  
💰 **Refund Request** - Request a refund for your purchase
💬 **General Support** - General questions or other issues
        """,
        inline=False
    )
    
    embed.add_field(
        name="⚡ Quick Actions",
        value="""
• Use the dropdown to select your ticket category
• Click **🎫 Create Ticket** for general support
• Click **❓ FAQ** for instant answers
• Click **📊 My Tickets** to view your tickets
        """,
        inline=False
    )
    
    embed.add_field(
        name="📞 Contact Information",
        value=f"""
**Payment Methods:**
• Bitcoin: `{bot.btc_address}`
• PayPal: `{bot.paypal_email}`

**Support Server:** {bot.discord_server}
        """,
        inline=False
    )
    
    embed.set_footer(text="Guardian Bot Support • Response within 24 hours")
    
    view = TicketPanelView(bot)
    await ctx.send(embed=embed, view=view)

async def buy_help(ctx):
    """Detailed purchase instructions and help"""
    embed = discord.Embed(
        title="💡 Purchase Help & Instructions",
        description="Step-by-step guide to purchasing Guardian Bot licenses",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📋 Step 1: Choose License",
        value="""
Use **$buy** to see all available license tiers:
• **BASIC** ($29.99/year) - Core moderation features
• **PREMIUM** ($49.99/year) - Advanced features + music
• **EXCLUSIVE** ($99.99 lifetime) - All features + priority support
        """,
        inline=False
    )
    
    embed.add_field(
        name="💳 Step 2: Payment Methods",
        value=f"""
**Bitcoin (Automatic)**:
• Send exact USD equivalent to: `{bot.btc_address}`
• Use **$verify btc <transaction_id>** after sending
• License activates instantly upon blockchain confirmation

**PayPal (Manual Review)**:
• Send payment to: `{bot.paypal_email}`
• Include license type in payment note
• Use **$verify paypal <transaction_id>** 
• Manual review within 24 hours
        """,
        inline=False
    )
    
    embed.add_field(
        name="🎫 Step 3: Get Support",
        value="""
Need help? Create a support ticket:
• **$ticket create** - Open new ticket
• **$ticket status** - Check existing tickets
• Categories: GENERAL, TECHNICAL, BILLING, REFUND
        """,
        inline=False
    )
    
    embed.add_field(
        name="✅ Step 4: License Activation",
        value="""
After payment verification:
• License automatically activates on main Guardian Bot
• Use **/license** on main bot to check status
• Use **/redeem_key** if you have a license key
• Features unlock immediately based on tier
        """,
        inline=False
    )
    
    embed.add_field(
        name="🔧 Troubleshooting",
        value=f"""
• Payment not processing? Check transaction ID format
• License not active? Use **/license** on main bot
• Need refund? Create ticket with category REFUND
• Join support server: {bot.discord_server}
        """,
        inline=False
    )
    
    embed.set_footer(text="Guardian Purchase Bot • Professional Discord bot licensing")
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    # Use the provided purchase bot token
    PURCHASE_BOT_TOKEN = "MTM4OTM1NjIyNjUyOTMyOTIwMg.GASLI8.9eorWl0lespLkv9A4ACzzw1kqOo1KFF9VmX8fI"
    
    print("🚀 Starting Guardian Purchase Bot...")
    print(f"📊 Payment Config: BTC {bot.btc_address}, PayPal {bot.paypal_email}")
    print(f"👑 Admin: {bot.owner_id}")
    
    try:
        bot.run(PURCHASE_BOT_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start purchase bot: {e}")
        print("Check bot token and permissions")