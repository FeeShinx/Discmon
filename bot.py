import discord
from stuff import TOKEN
from discord.ext import commands
import os
import pokebase as pb
from PIL import Image, ImageSequence
import io
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
import nest_asyncio
nest_asyncio.apply()

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
async def setup_hook():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"loaded {filename}")
            
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

def add_pokemon_helper(user_id, species_id, pokemon_name):
    data = load_data()
    if user_id in data:
        user_data = data[user_id]
        pokemon_id = len(user_data["pokemons"]) + 1

        new_pokemon = {
            "species_id": species_id,
            "pokemon_id": pokemon_id,
            "pokemon_name": pokemon_name.capitalize()
        }
        print("New Pokémon data:", new_pokemon)
        user_data["pokemons"].append(new_pokemon)
        save_data(data)
        return True
    return False
    
@commands.command(name="inventory", aliases=['inv', 'pokemons', 'p'])
async def inventory(ctx):
    user_id = str(ctx.author.id)
    user_data = get_user(user_id)
    if user_data:
        embed = discord.Embed(title=f"`{ctx.author.name}'s Pokémon`", color=discord.Color.blue())
        for pokemon in user_data["pokemons"]:
            species_id = pokemon["species_id"]
            name = pokemon['pokemon_name']
            orig_name = name
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
            pokemon_name = p.name.capitalize()
            url = p.sprites.versions.generation_viii.icons.front_default
            embed.add_field(name=f"`{pokemon['pokemon_id']}` - {pokemon_name}", value=f"", inline=False)
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
async def add_pokemon(ctx, user_id, *, name: str):
    orig_name = name
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
    try:
        species_id = p.id
    except AttributeError:
        await ctx.send(f"Couldn't find Pokemon called {orig_name.capitalize()}")
        return
    if add_pokemon_helper(user_id, species_id, orig_name.capitalize()):
        await ctx.send(f'Added Pokémon {orig_name.capitalize()} to user <@{user_id}>.')
    else:
        await ctx.send(f'Failed to add Pokémon. User <@{user_id}> not found.')

@commands.command()
@is_admin()
async def add_coins(ctx, user_id: str, amount: int):
     if await add_coins(user_id, amount):
        await ctx.send(f'Added {amount} coins to user {user_id}.')
     else:
         await ctx.send(f'Failed to add coins. User {user_id} not found.')
                    
     

bot.add_command(ping)
bot.add_command(balance)
bot.add_command(create_account)
bot.add_command(add_pokemon)
bot.add_command(inventory)
bot.add_command(add_coins)
bot.run(TOKEN)