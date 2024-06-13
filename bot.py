import discord
from stuff import TOKEN
from discord.ext import commands
import os
import pokebase as pb
from PIL import Image, ImageSequence
from io import BytesIO
import requests
import nltk
from pprint import pprint
import re
import math
import functools
import typing
import asyncio
import pickle
from nltk.tokenize import sent_tokenize

nltk.download('punkt')
 #formating texts function thingy
def format_text(text):
    sentences = sent_tokenize(text)
    sentences[0] = sentences[0].capitalize()
    for i in range(1, len(sentences)):
        if sentences[i][0].islower():
            sentences[i] = sentences[i-1] + " " + sentences[i].capitalize()
    formatted_text = ' '.join(sentences)
    return formatted_text

# main bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='p!', intents=intents)

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.watching, name="Development")
    await bot.change_presence(status=discord.Status.idle, activity=activity)
    print(f"stupid bot logged in as {bot.user}")
    print("---------------------------------------")
    
#is admin decorator
def is_admin():
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)
    
@commands.command()
async def ping(ctx):
    await ctx.send('Pong! {0}'.format(round(bot.latency, 1)))
    
@commands.command(name="dex")
async def dex(ctx, *, arg):
    forms = ['', '-mega', '-mega-x', '-mega-y', '-gmax']
    name = arg
    Orig_name = name
    name = name.lower()
    name = name.replace(" ", "-")
    form = False
    if name.startswith('mega'):
        name = name[4:].strip()
        name = name.strip()
        name = name.replace("-", "")
        p = await asyncio.to_thread(pb.pokemon, name + '-mega')
        form = True
        if name.endswith('x'):
            name = name[:-1].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + '-mega-x')
            form = True
        if name.endswith('y'):
            name = name[:-1].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + '-mega-y')
            form = True
    elif name.startswith('gigantamax'):
            name = name[10:].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + '-gmax')
            form = True
    else:
        p = await asyncio.to_thread(pb.pokemon, name)
        form = False
    try:
        p.stats[0].base_stat
    except AttributeError:
        await ctx.send(f"Couldn't find pokemon `{Orig_name}`")
        return
    	
    
    #Stats things idk tbh
    baseStat =f"{str(p.stats[0].stat)} -  **{p.stats[0].base_stat}**\n{str(p.stats[1].stat)} -  **{p.stats[1].base_stat}**\n{str(p.stats[2].stat)} - **{p.stats[2].base_stat}**\n{str(p.stats[3].stat)} - **{p.stats[3].base_stat}**\n{str(p.stats[4].stat)} - **{p.stats[4].base_stat}**\n{str(p.stats[5].stat)} - **{p.stats[5].base_stat}**\nTotal - **{p.stats[0].base_stat + p.stats[1].base_stat + p.stats[2].base_stat + p.stats[3].base_stat + p.stats[4].base_stat + p.stats[5].base_stat}**"
#flavor_text/pokemon descriptions

    def get_flavor_text(name):
        flavor_text_entries = [entry for entry in p.species.flavor_text_entries if entry.language.name == 'en']
        if flavor_text_entries:
            return flavor_text_entries[0].flavor_text  # Select the first English flavor text entry
        else:
            return "Flavor text not available for this Pokémon."                                                                              
    raw_desc = get_flavor_text(name)
    pName = Orig_name
    cleaned_desc = re.sub(r'\n+', ' ', raw_desc)
    Desc = re.sub(r'(?<=[.,!?])', ' ', cleaned_desc)
    Desc = format_text(Desc)
    Desc = Desc.capitalize()
    Desc = re.sub(r'/(?<![-\w])\n|\n(?!\w)', '', Desc)
    Desc = Desc.replace('\n', " ")
    Desc = Desc.replace('\u000c', " ")
    Desc = str(Desc)

#evolution chains

    def get_evolution_chain_description(pokemon_id):
     try:
        # Fetch the Pokémon species and evolution chain
        pokemon_species = pb.pokemon_species(pokemon_id)
        evolution_chain_data = pb.evolution_chain(pokemon_species.evolution_chain.id)
        evolution_chain = evolution_chain_data.chain
        description = []

        # Recursive function to process evolution chain
        def process_evolution_chain(chain):
            nonlocal description
            if chain:
                current_species = chain.species.name.capitalize()
                for evolution in chain.evolves_to:
                    evolved_species = evolution.species.name.capitalize()
                    evolution_details = evolution.evolution_details[0]
                    trigger = evolution_details.trigger.name
                    evolution_method = ""

                    if trigger == 'level-up':
                        if evolution_details.held_item:
                            held_item = evolution_details.held_item.name.replace('-', ' ').capitalize()
                            evolution_method = f" Evolves by leveling up while holding **{held_item}**"
                        elif evolution_details.known_move:
                            move = evolution_details.known_move.name.replace('-', ' ').capitalize()
                            evolution_method = f" Evolves by leveling up while knowing **{move}**"
                        elif evolution_details.known_move_type:
                            move_type = evolution_details.known_move_type.name.capitalize()
                            evolution_method = f" Evolves by leveling up while knowing a **{move_type}** type move"
                        elif evolution_details.time_of_day:
                            time_of_day = evolution_details.time_of_day.capitalize()
                            evolution_method = f" Evolves by leveling up during the **{time_of_day}**"
                        else:
                            min_level = evolution_details.min_level
                            evolution_method = f" Evolves from level {min_level}" if min_level else " Evolves by leveling up"
                    elif trigger == 'use-item':
                        item = evolution_details.item.name.replace('-', ' ').capitalize()
                        evolution_method = f" Evolves using **{item}**"
                    elif trigger == 'trade':
                        evolution_method = " Evolves by trading"

                    description.append(f"**{current_species}** > {evolution_method} > {evolved_species}")
                    process_evolution_chain(evolution)  # Recursively process the next evolution

        process_evolution_chain(evolution_chain)
        return '\n'.join(description)

     except Exception as e:
        return f"Error: {str(e)}"

    evolution_chain = get_evolution_chain_description(p.id)

#pokemon types
    
    pType = ([type.type.name for type in p.types])
    pType1 = [element.replace("'", "").replace("[", "").replace("]", "") for element in pType]
    pType = [i.title() for i in pType1]
    pType = ["**" + type.type.name.title() + "**" for type in p.types]

#physical attributes 
    def round_up_to_decimal(number, decimals=1):
        factor = 10 ** decimals
        return math.ceil(number * factor) / factor

    def custom_round(number):
            # Determine the number of decimal places
                decimal_places = len(str(number).split('.')[-1])
                    
                if decimal_places > 2:
                    return round_up_to_decimal(number, 1)
                return number
    pHeight = p.height
    pHeight = pHeight * 0.1
    pHeight = custom_round(pHeight)
    pWeight = p.weight
    pWeight = pWeight * 0.1
    pWeight = custom_round(pWeight)
    
    #custom dex image fr fr
    def create_dex_image_gif(pokemon_sprite_url, dex_image_path):
        dex_image = Image.open(dex_image_path).convert("RGBA")
        response = requests.get(pokemon_sprite_url)
        sprite_image = Image.open(BytesIO(response.content))
        sprite_size = (250, 250)

        dex_width, dex_height = dex_image.size
        sprite_width, sprite_height = sprite_image.size

    # Calculate the position to center the sprite on the Dex image
       
        
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(sprite_image):
            frame = frame.convert("RGBA")
            frame = frame.resize(sprite_size, Image.LANCZOS)
            sprite_width, sprite_height = frame.size

            x = (dex_width - sprite_width) // 2
            y = (dex_height - sprite_height) // 2
    # Create a copy of the background to paste the frame onto
            background = dex_image.copy()
    # Paste the sprite image at the calculated position
            background.paste(frame, (x, y), frame)
            frames.append(background)
            durations.append(sprite_image.info.get('duration', 100))  # Use duration from the original sprite frame
 
    # Save the result to a BytesIO object
        dex_image_bytes = BytesIO()
        frames[0].save(
           dex_image_bytes,
           format='GIF',
           save_all=True,
           append_images=frames[1:],
           loop=0,
           duration=durations,
           transparency=0,
           disposal=2
)
        dex_image_bytes.seek(0)

        return dex_image_bytes

    
    
    async def create_dex_image_gif_async(pokemon_sprite_url, dex_image_path):
        return await asyncio.to_thread(create_dex_image_gif, pokemon_sprite_url, dex_image_path)



#main embed    
    dexembed = discord.Embed(title=f"``#{p.id}-{pName.title()}``", description=f"{Desc}")
    if form is True:
        dexembed.add_field(name="`Evolutions`", value="None", inline=False)
    else:
        dexembed.add_field(name="`Evolutions`", value=f"{evolution_chain}", inline=False)
    dexembed.add_field(name="`Type`", value=", ".join(pType), inline=True) 
    dexembed.add_field(name="`Physical Attributes`", value=f"Height - **{pHeight} m**\nWeight - **{pWeight} kg**", inline=True)
    dexembed.add_field(name="`Stats`", value=f"{baseStat.title()}", inline=False)
    image = p.sprites.versions.generation_v.black_white.animated.front_default
    dexembed.set_image(url= image)
    id = p.species.id
    if image == None:
        image = p.sprites.versions.generation_v.black_white.front_default
        if image == None:
            image = p.sprites.other.showdown.front_default
            if image == None:
                image = p.sprites.other.official_artwork.front_default
                if image == None:
                    image = pb.pokemon_form(id).sprites.front_default
    dex_image_path = "dex_background.png"
    dex_image_bytes = await create_dex_image_gif_async(image, dex_image_path)

    file = discord.File(fp=dex_image_bytes, filename="dex_image.gif")
    dexembed.set_image(url="attachment://dex_image.gif")
    await ctx.send(file=file, embed=dexembed)

#User Data system?
data_file = 'user_data.pkl'

def save_data(data):
    with open(data_file, 'wb') as f:
        pickle.dump(data, f)

def load_data():
    if os.path.exists(data_file):
        with open(data_file, 'rb') as f:
            return pickle.load(f)
    return {}

def create_user_profile(user_id, username):
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "username": username,
            "pokemons": [],
            "coins": 0
        }
        save_data(data)
        return True
    return False
     
def get_user(user_id):
    data = load_data()
    return data.get(user_id)

def update_user(user_id, data):
    data = load_data()
    if user_id in data:
        data[user_id].update(data)
        save_data(data)
        return True
    return False
    
def delete_user(user_id):
    data = load_data()
    if user_id in data:
        del data[user_id]
        save_data(data)
        return True
    return False


    
def add_coins(user_id, amount):
    data = load_data()
    if user_id in data:
        data[user_id]["coins"] += amount
        save_data(data)
        return True
    return False

def add_pokemon_helper(user_id, species_id):
    data = load_data()
    if user_id in data:
        user_data = data[user_id]
        pokemon_id = len(user_data["pokemons"]) + 1

        new_pokemon = {
            "species_id": species_id,
            "pokemon_id": pokemon_id,
            "same_pokemon_count": sum(1 for pok in user_data["pokemons"] if pok["species_id"] == species_id) + 1
        }
        user_data["pokemons"].append(new_pokemon)
        save_data(data)
        return True
    return False
    
@commands.command(name="inventory", aliases=['inv', 'pokemons', 'p'])
async def inventory(ctx):
    user_id = str(ctx.author.id)
    user_data = get_user(user_id)
    if user_data:
        embed = discord.Embed(title=f"{ctx.author.name}'s Pokémon", color=discord.Color.blue())
        for pokemon in user_data["pokemons"]:
            pokemon_id = pokemon["pokemon_id"]
            same_pokemon_count = pokemon["same_pokemon_count"]
            poke_info = f"Count: {same_pokemon_count}"
            embed.add_field(name=f"Pokémon ID: {pokemon_id}", value=poke_info, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send('You need to create an account first.')
        
@commands.command(name="create-account", aliases=['create-acc'])
async def create_account(ctx):
    user_id = str(ctx.author.id)
    username = str(ctx.author)
    if create_user_profile(user_id, username):
        await ctx.send(f'Account created for @<{user_id}>')
    else:
        await ctx.send('You already have an account.')

@commands.command(name="balance", aliases=["bal"])
async def balance(ctx):
    user_id = str(ctx.author.id)
    user_data = get_user(user_id)
    if user_data:
        await ctx.send(f'Your balance is {user_data["coins"]} coins.')
    else:
        await ctx.send('You need to create an account first.')
        
@commands.command(name="add-pokemon", aliases=['add-p', 'add_poke', 'add-poke',])
@is_admin()
async def add_pokemon(ctx, user_id, name: str):
    name = name.lower()
    if name.startswith('mega'):
        name = name[4:].strip()
        name = name.strip()
        name = name.replace("-", "")
        p = await asyncio.to_thread(pb.pokemon, name + '-mega')
        if name.endswith('x'):
            name = name[:-1].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + '-mega-x')
        if name.endswith('y'):
            name = name[:-1].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + '-mega-y')
    elif name.startswith('gigantamax'):
            name = name[10:].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + '-gmax')
    else:
        p = await asyncio.to_thread(pb.pokemon, name)
    species_id = p.id
    if add_pokemon_helper(user_id, species_id):
        await ctx.send(f'Added Pokémon {name} to user <@{user_id}>.')
    else:
        await ctx.send(f'Failed to add Pokémon. User <@{user_id}> not found.')

@commands.command()
@is_admin()
async def add_coins(ctx, user_id: str, amount: int):
     if await add_coins(user_id, amount):
        await ctx.send(f'Added {amount} coins to user {user_id}.')
     else:
         await ctx.send(f'Failed to add coins. User {user_id} not found.')
                    
     
bot.add_command(dex)
bot.add_command(ping)
bot.add_command(balance)
bot.add_command(create_account)
bot.add_command(add_pokemon)
bot.add_command(inventory)
bot.add_command(add_coins)
bot.run(TOKEN)