"""
Excel Help Discord Bot
Analyzes screenshots and Excel files to provide step-by-step instructions
"""

import discord
from discord.ext import commands
import os
import io
import asyncio
import aiohttp
import pytesseract
from PIL import Image
import pandas as pd
import openpyxl
from openai import OpenAI
import tempfile
import traceback

# Initialize SambaNova API client (OpenAI-compatible)
openai_client = OpenAI(
    api_key="c760333c-cb33-4827-9311-3f07df9eacfc",
    base_url="https://api.sambanova.ai/v1"
)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class ExcelHelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutes timeout
    
    @discord.ui.button(label="📸 Analyze Screenshot", style=discord.ButtonStyle.primary, emoji="📸")
    async def analyze_screenshot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please upload a screenshot of your Excel question. I'll analyze it and provide step-by-step instructions!",
            ephemeral=True
        )
    
    @discord.ui.button(label="📊 Analyze Excel File", style=discord.ButtonStyle.secondary, emoji="📊")
    async def analyze_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please upload your Excel file (.xlsx, .xls, .csv). I'll analyze it and help you with your task!",
            ephemeral=True
        )

async def analyze_image_with_ocr(image_data):
    """Extract text from image using OCR"""
    try:
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # Enhance image for better OCR
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Use pytesseract to extract text
        extracted_text = pytesseract.image_to_string(image, config='--psm 6')
        
        return extracted_text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return None

async def analyze_excel_file(file_data, filename):
    """Analyze Excel file content"""
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(file_data)
            tmp_file_path = tmp_file.name
        
        # Read Excel file
        if filename.endswith('.csv'):
            df = pd.read_csv(tmp_file_path)
        else:
            df = pd.read_excel(tmp_file_path, sheet_name=None)  # Read all sheets
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        # Prepare analysis
        analysis = {}
        
        if isinstance(df, dict):  # Multiple sheets
            analysis['sheets'] = list(df.keys())
            analysis['data'] = {}
            for sheet_name, sheet_data in df.items():
                analysis['data'][sheet_name] = {
                    'shape': sheet_data.shape,
                    'columns': list(sheet_data.columns),
                    'sample_data': sheet_data.head(5).to_string(),
                    'data_types': sheet_data.dtypes.to_string()
                }
        else:  # Single sheet/CSV
            analysis['shape'] = df.shape
            analysis['columns'] = list(df.columns)
            analysis['sample_data'] = df.head(10).to_string()
            analysis['data_types'] = df.dtypes.to_string()
        
        return analysis
    except Exception as e:
        print(f"Excel Analysis Error: {e}")
        return None

async def generate_instructions(content, content_type, user_question=None):
    """Generate step-by-step instructions using OpenAI"""
    try:
        # Using SambaNova's free Llama model for cost efficiency
        
        if content_type == "screenshot":
            prompt = f"""
You are an Excel expert helping a student. I've extracted this text from a screenshot of an Excel question:

"{content}"

Please provide clear, step-by-step instructions on how to complete this Excel task. Format your response as:

1. **Step 1:** [Action to take]
2. **Step 2:** [Next action]
3. **Step 3:** [And so on...]

Be specific about:
- Which cells to select
- Which formulas to use (with exact syntax)
- Which buttons or menu items to click
- Expected results

Keep it beginner-friendly and practical.
"""
        else:  # Excel file
            prompt = f"""
You are an Excel expert helping a student. I've analyzed their Excel file and here's the structure:

{content}

User's question: {user_question or "Please help me understand this data and suggest common Excel tasks I could perform."}

Please provide clear, step-by-step instructions. Format your response as:

1. **Step 1:** [Action to take]
2. **Step 2:** [Next action]
3. **Step 3:** [And so on...]

Be specific about:
- Which cells to select
- Which formulas to use (with exact syntax)
- Which buttons or menu items to click
- Expected results

Suggest relevant Excel operations based on the data structure.
"""

        response = openai_client.chat.completions.create(
            model="Llama-4-Maverick-17B-128E-Instruct",
            messages=[
                {"role": "system", "content": "You are a helpful Excel tutor who provides clear, step-by-step instructions for Excel tasks."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.1,
            top_p=0.1
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return None

@bot.event
async def on_ready():
    print(f"📊 Excel Help Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@bot.tree.command(name="excelhelp", description="Get help with Excel tasks - upload screenshots or files")
async def excel_help(interaction: discord.Interaction):
    """Main Excel help command"""
    embed = discord.Embed(
        title="📊 Excel Help Assistant",
        description="I can help you with Excel tasks in two ways:",
        color=discord.Color.green()
    )
    embed.add_field(
        name="📸 Screenshot Analysis",
        value="Upload a screenshot of your Excel question and I'll read it using OCR and provide step-by-step instructions.",
        inline=False
    )
    embed.add_field(
        name="📊 File Analysis", 
        value="Upload your Excel file (.xlsx, .xls, .csv) and I'll analyze the data structure and suggest helpful operations.",
        inline=False
    )
    embed.add_field(
        name="🔧 How to use",
        value="1. Click one of the buttons below\n2. Upload your screenshot or file\n3. Get detailed step-by-step instructions!",
        inline=False
    )
    embed.set_footer(text="Powered by SambaNova AI and OCR technology")
    
    view = ExcelHelpView()
    await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_message(message):
    """Handle file/image uploads"""
    if message.author.bot:
        return
    
    # Check if message has attachments
    if message.attachments:
        for attachment in message.attachments:
            # Check if it's an image (for OCR)
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']):
                await handle_image_upload(message, attachment)
            
            # Check if it's an Excel file
            elif any(attachment.filename.lower().endswith(ext) for ext in ['.xlsx', '.xls', '.csv']):
                await handle_excel_upload(message, attachment)
    
    await bot.process_commands(message)

async def handle_image_upload(message, attachment):
    """Handle image screenshot analysis"""
    try:
        # Send processing message
        processing_msg = await message.reply("📸 Analyzing your screenshot... This may take a moment!")
        
        # Download image
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                else:
                    await processing_msg.edit(content="❌ Failed to download image. Please try again.")
                    return
        
        # Extract text using OCR
        await processing_msg.edit(content="🔍 Extracting text from screenshot...")
        extracted_text = await analyze_image_with_ocr(image_data)
        
        if not extracted_text:
            await processing_msg.edit(content="❌ Could not extract text from image. Please ensure the image is clear and contains text.")
            return
        
        # Generate instructions
        await processing_msg.edit(content="🤖 Generating step-by-step instructions...")
        instructions = await generate_instructions(extracted_text, "screenshot")
        
        if not instructions:
            await processing_msg.edit(content="❌ Failed to generate instructions. Please try again.")
            return
        
        # Create response embed
        embed = discord.Embed(
            title="📸 Screenshot Analysis Complete",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔍 Extracted Text",
            value=f"```{extracted_text[:500]}{'...' if len(extracted_text) > 500 else ''}```",
            inline=False
        )
        embed.add_field(
            name="📋 Step-by-Step Instructions",
            value=instructions[:1000] + ("..." if len(instructions) > 1000 else ""),
            inline=False
        )
        
        # If instructions are too long, send as follow-up
        if len(instructions) > 1000:
            await processing_msg.edit(content="", embed=embed)
            await message.reply(f"**Complete Instructions:**\n{instructions}")
        else:
            await processing_msg.edit(content="", embed=embed)
            
    except Exception as e:
        print(f"Image handling error: {e}")
        await message.reply(f"❌ Error analyzing screenshot: {str(e)}")

async def handle_excel_upload(message, attachment):
    """Handle Excel file analysis"""
    try:
        # Send processing message
        processing_msg = await message.reply("📊 Analyzing your Excel file... This may take a moment!")
        
        # Download file
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    file_data = await resp.read()
                else:
                    await processing_msg.edit(content="❌ Failed to download file. Please try again.")
                    return
        
        # Analyze Excel file
        await processing_msg.edit(content="🔍 Analyzing file structure...")
        analysis = await analyze_excel_file(file_data, attachment.filename)
        
        if not analysis:
            await processing_msg.edit(content="❌ Could not analyze Excel file. Please ensure it's a valid Excel/CSV file.")
            return
        
        # Ask user for specific question
        await processing_msg.edit(content="📝 What would you like to do with this data? Please reply with your question!")
        
        def check(m):
            return m.author == message.author and m.channel == message.channel
        
        try:
            user_response = await bot.wait_for('message', check=check, timeout=120.0)
            user_question = user_response.content
        except asyncio.TimeoutError:
            user_question = "Please help me understand this data and suggest common Excel tasks."
        
        # Generate instructions
        await processing_msg.edit(content="🤖 Generating step-by-step instructions...")
        instructions = await generate_instructions(str(analysis), "excel_file", user_question)
        
        if not instructions:
            await processing_msg.edit(content="❌ Failed to generate instructions. Please try again.")
            return
        
        # Create response embed
        embed = discord.Embed(
            title="📊 Excel File Analysis Complete",
            color=discord.Color.green()
        )
        
        # Add file info
        if 'sheets' in analysis:
            embed.add_field(
                name="📑 Sheets Found",
                value=", ".join(analysis['sheets']),
                inline=False
            )
        else:
            embed.add_field(
                name="📊 Data Shape",
                value=f"{analysis['shape'][0]} rows × {analysis['shape'][1]} columns",
                inline=True
            )
        
        embed.add_field(
            name="❓ Your Question",
            value=user_question,
            inline=False
        )
        embed.add_field(
            name="📋 Step-by-Step Instructions",
            value=instructions[:1000] + ("..." if len(instructions) > 1000 else ""),
            inline=False
        )
        
        # If instructions are too long, send as follow-up
        if len(instructions) > 1000:
            await processing_msg.edit(content="", embed=embed)
            await message.reply(f"**Complete Instructions:**\n{instructions}")
        else:
            await processing_msg.edit(content="", embed=embed)
            
    except Exception as e:
        print(f"Excel handling error: {e}")
        print(traceback.format_exc())
        await message.reply(f"❌ Error analyzing Excel file: {str(e)}")

# Help command
@bot.tree.command(name="help", description="Get help with using the Excel Help Bot")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Excel Help Bot - User Guide",
        description="Learn how to use this bot to get Excel help!",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="🚀 Getting Started",
        value="Use `/excelhelp` to start getting assistance with your Excel tasks.",
        inline=False
    )
    embed.add_field(
        name="📸 Screenshot Analysis",
        value="• Take a screenshot of your Excel question\n• Upload it in any channel\n• Get instant OCR analysis and step-by-step instructions",
        inline=False
    )
    embed.add_field(
        name="📊 File Analysis",
        value="• Upload Excel files (.xlsx, .xls, .csv)\n• Tell me what you want to do\n• Get customized instructions for your data",
        inline=False
    )
    embed.add_field(
        name="💡 Tips for Best Results",
        value="• Use clear, high-quality screenshots\n• Be specific about what you want to accomplish\n• Include context about your assignment or goal",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    # Excel Help Bot token
    TOKEN = "MTM4OTM4NDM3ODM1ODE2OTcwMA.GBGAHH.8VxZgOCkUTgttXldQUbzemBTEGKbfhiI25qC_A"
    print("🚀 Starting Excel Help Bot...")
    bot.run(TOKEN)