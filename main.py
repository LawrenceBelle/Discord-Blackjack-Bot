import discord
from discord.ext import commands
from blackjack import BlackJack
import personal_vars # Holds only bot token. You will need your own to run the bot


client = commands.Bot(command_prefix='!', help_command=None)

bjack_games = dict()  # Uses message ids as a key and blackjack objects as values


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('!blackjack'))
    print(f'Logged in as {client.user}\n')


# Sends an embed to the channel about how to use the bot
@client.command(aliases=['Help'])
async def help(context):
    embed = discord.Embed(title="!Help")
    embed.add_field(name="!Blackjack", 
                    value='Creates a game of blackjack you play using reactions as buttons.', 
                    inline=False)

    await context.send(embed=embed)


# Sends a message to the channel that you can play blackjack on
@client.command(aliases=['Blackjack'])
async def blackjack(context):
    bjack = BlackJack(client.user, context.author)

    bjack.message = await context.send(embed=bjack.embed)
    await bjack.start()

    if not bjack.gameover():
        bjack_games[bjack.message.id] = bjack

        await bjack.message.add_reaction(bjack.HIT_EMOJI)
        await bjack.message.add_reaction(bjack.STAND_EMOJI)
    

# Handles reactions, more specifically for playing blackjack
@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:
        return  # Ignores reactions made by the bot

    message = reaction.message
    if message.id in bjack_games:    # If reaction was on a blackjack message
        bjack = bjack_games[message.id]
        if user == bjack.message_author:

            r_emoji = str(reaction.emoji)
            if r_emoji == bjack.HIT_EMOJI or r_emoji == bjack.STAND_EMOJI:
                await message.remove_reaction(r_emoji, user)

            if r_emoji == bjack.HIT_EMOJI:
                await bjack.hit()

                if bjack.gameover():
                    del bjack_games[message.id]
                    await message.remove_reaction(bjack.STAND_EMOJI, client.user)
                    await message.remove_reaction(bjack.HIT_EMOJI, client.user)

            if r_emoji == bjack.STAND_EMOJI:
                del bjack_games[message.id]
                await bjack.stand()
                await message.remove_reaction(bjack.STAND_EMOJI, client.user)
                await message.remove_reaction(bjack.HIT_EMOJI, client.user)


if __name__ == '__main__':
    client.run(personal_vars.TOKEN)