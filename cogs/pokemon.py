import discord
from discord.ext import commands
import pokebase as pb
import asyncio
import os
import functools
import re
import math
import requests
import io
from io import BytesIO
from PIL import Image, ImageSequence
import nltk
from nltk.tokenize import sent_tokenize
import nest_asyncio
nest_asyncio.apply()

nltk.download('punkt')
def format_text(text):
    sentences = sent_tokenize(text)
    sentences[0] = sentences[0].capitalize()
    for i in range(1, len(sentences)):
        if sentences[i][0].islower():
            sentences[i] = sentences[i-1] + " " + sentences[i].capitalize()
    formatted_text = ' '.join(sentences)
    return formatted_text

class Pokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def dex(self, ctx, *, arg):
        forms = ["", "-mega", "-mega-x", "-mega-y", "-gmax"]
        name = arg
        Orig_name = name
        name = name.lower()
        name = name.replace(" ", "-")
        form = False
        if name.startswith("mega"):
            name = name[4:].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + "-mega")
            form = True
            if name.endswith("x"):
                name = name[:-1].strip()
                name = name.strip()
                name = name.replace("-", "")
                p = await asyncio.to_thread(pb.pokemon, name + "-mega-x")
                form = True
            if name.endswith("y"):
                name = name[:-1].strip()
                name = name.strip()
                name = name.replace("-", "")
                p = await asyncio.to_thread(pb.pokemon, name + "-mega-y")
                form = True
        elif name.startswith("gigantamax"):
            name = name[10:].strip()
            name = name.strip()
            name = name.replace("-", "")
            p = await asyncio.to_thread(pb.pokemon, name + "-gmax")
            form = True
        else:
            p = await asyncio.to_thread(pb.pokemon, name)
            form = False
        try:
             p.stats[0].base_stat
        except AttributeError:
            await ctx.send(f"Couldn't find pokemon `{Orig_name}`")
            return

    # Stats things idk tbh
        baseStat = f"{str(p.stats[0].stat)} -  **{p.stats[0].base_stat}**\n{str(p.stats[1].stat)} -  **{p.stats[1].base_stat}**\n{str(p.stats[2].stat)} - **{p.stats[2].base_stat}**\n{str(p.stats[3].stat)} - **{p.stats[3].base_stat}**\n{str(p.stats[4].stat)} - **{p.stats[4].base_stat}**\n{str(p.stats[5].stat)} - **{p.stats[5].base_stat}**\nTotal - **{p.stats[0].base_stat + p.stats[1].base_stat + p.stats[2].base_stat + p.stats[3].base_stat + p.stats[4].base_stat + p.stats[5].base_stat}**"
    # flavor_text/pokemon descriptions

        def get_flavor_text(name):
            flavor_text_entries = [
                entry
                for entry in p.species.flavor_text_entries
                if entry.language.name == "en"
        ]
            if flavor_text_entries:
                return flavor_text_entries[
                0
                 ].flavor_text  # Select the first English flavor text entry
            else:
                 return "Flavor text not available for this Pokémon."

        raw_desc = get_flavor_text(name)
        pName = Orig_name
        cleaned_desc = re.sub(r"\n+", " ", raw_desc)
        Desc = re.sub(r"(?<=[.,!?])", " ", cleaned_desc)
        Desc = format_text(Desc)
        Desc = Desc.capitalize()
        Desc = re.sub(r"/(?<![-\w])\n|\n(?!\w)", "", Desc)
        Desc = Desc.replace("\n", " ")
        Desc = Desc.replace("\u000c", " ")
        Desc = str(Desc)

    # evolution chains

        def get_evolution_chain_description(pokemon_id):
            try:
            # Fetch the Pokémon species and evolution chain
                pokemon_species = pb.pokemon_species(pokemon_id)
                evolution_chain_data = pb.evolution_chain(
                    pokemon_species.evolution_chain.id
            )
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

                                if trigger == "level-up":
                                    if evolution_details.held_item:
                                        held_item = evolution_details.held_item.name.replace(
                                        "-", " "
                                     ).capitalize()
                                        evolution_method = f"Evolves by leveling up while holding **{held_item}**"
                                    elif evolution_details.known_move:
                                        move = evolution_details.known_move.name.replace(
                                        "-", " "
                                     ).capitalize()
                                        evolution_method = (
                                        f" Evolves by leveling up while knowing **{move}**"
                                )
                                    elif evolution_details.known_move_type:
                                        move_type = (
                                        evolution_details.known_move_type.name.capitalize()
                                )
                                        evolution_method = f" Evolves by leveling up while knowing a **{move_type}** type move"
                                    elif evolution_details.time_of_day:
                                        time_of_day = evolution_details.time_of_day.capitalize()
                                        evolution_method = f" Evolves by leveling up during the **{time_of_day}**"
                                    else:
                                        min_level = evolution_details.min_level
                                        evolution_method = f" Evolves from level {min_level}" if min_level else " Evolves by leveling up"
                                elif trigger == 'use-item':
                                    item = evolution_details.item.name.replace(
                                "-", " "
                            ).capitalize()
                                    evolution_method = f" Evolves using **{item}**"
                                elif trigger == "trade":
                                    evolution_method = " Evolves by trading"

                            description.append(
                                 f"**{current_species}** > {evolution_method} > {evolved_species}"
                        )
                            process_evolution_chain(
                                evolution
                        )  # Recursively process the next evolution

                process_evolution_chain(evolution_chain)
                return "\n".join(description)

            except Exception as e:
                 return f"Error: {str(e)}"

        evolution_chain = get_evolution_chain_description(p.id)
    # pokemon types

        pType = [type.type.name for type in p.types]
        pType1 = [
             element.replace("'", "").replace("[", "").replace("]", "") for element in pType
    ]
        pType = [i.title() for i in pType1]
        pType = ["**" + type.type.name.title() + "**" for type in p.types]

    # physical attributes
        def round_up_to_decimal(number, decimals=1):
            factor = 10**decimals
            return math.ceil(number * factor) / factor

        def custom_round(number):
        # Determine the number of decimal places
            decimal_places = len(str(number).split(".")[-1])

            if decimal_places > 2:
                return round_up_to_decimal(number, 1)
            return number

        pHeight = p.height
        pHeight = pHeight * 0.1
        pHeight = custom_round(pHeight)
        pWeight = p.weight
        pWeight = pWeight * 0.1
        pWeight = custom_round(pWeight)

    # custom dex image fr fr
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
                durations.append(
                    sprite_image.info.get("duration", 100)
            )  # Use duration from the original sprite frame

        # Save the result to a BytesIO object
            dex_image_bytes = BytesIO()
            frames[0].save(
                dex_image_bytes,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                loop=0,
               duration=durations,
               transparency=0,
              disposal=2,
        )
            dex_image_bytes.seek(0)

            return dex_image_bytes

        async def create_dex_image_gif_async(pokemon_sprite_url, dex_image_path):
             return await asyncio.to_thread(
                 create_dex_image_gif, pokemon_sprite_url, dex_image_path
        )

    # main embed
        dexembed = discord.Embed(
            title=f"``#{p.id}-{pName.title()}``", description=f"{Desc}"
    )
        if form is True:
             dexembed.add_field(name="`Evolutions`", value="None", inline=False)
        else:
            dexembed.add_field(
                name="`Evolutions`", value=f"{evolution_chain}", inline=False
        )
        dexembed.add_field(name="`Type`", value=", ".join(pType), inline=True)
        dexembed.add_field(
            name="`Physical Attributes`",
            value=f"Height - **{pHeight} m**\nWeight - **{pWeight} kg**",
            inline=True,
    )
        dexembed.add_field(name="`Stats`", value=f"{baseStat.title()}", inline=False)
        image = p.sprites.versions.generation_v.black_white.animated.front_default
        dexembed.set_image(url=image)
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

async def setup(bot):
    await bot.add_cog(Pokemon(bot))