import random
import discord
import asyncio
from colours import *


class Card:
    def __init__(self, value, suit):
        self.value = value
        self.suit = suit
        self.number = self.get_number()
        self.string = f" {self.value}{self.suit}"
        
    def get_number(self):
        if self.value == 'J' or self.value == 'Q' or self.value == 'K':
            return 10
        elif self.value == 'A':
            return 1
        else:
            return int(self.value)


class Player:
    def __init__(self):
        self.hand = []  # List of card objects
        self.total = 0

    def get_numbers(self):
        numbers = []
        for card in self.hand:
            numbers.append(card.number)
        return numbers

    def is_bust(self):
        if self.total > 21:
            return True
        return False

    def has_ace(self):
        numbers = self.get_numbers()
        if 1 in numbers:
            return True
        return False


class Dealer(Player):
    def __init__(self):
        super().__init__()

    def still_dealing(self):
        # ensures dealer's value is above 16 before the dealer stops getting cards
        # since ace high can only be on one card before going bust, this method of adding 10 is fine
        if self.has_ace() and self.total <= 11 and self.total + 10 >= 17:
            return False
        if self.total >= 17:
            return False
        return True


class BlackJack:
    def __init__(self, bot_name, message_author):

        self.message_author = message_author
        self.message = None # The message the bot sends with the blackjack embed on

        self._dealer_name = str(bot_name).split('#')[0]
        self._player_name = str(message_author).split('#')[0]
        self.player = Player()
        self.dealer = Dealer()

        self.SUITS = [':spades:', ':diamonds:', ':hearts:', ':clubs:']
        self.CARD_VALUES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        self.deck = self.create_deck()  # list of all the cards

        self.hide_card = True   # Determines whether the dealer's second card should be face down
        self._PAUSE_TIME = 0.4

        self.CARD_EMOJI = ':black_joker:'
        self.HIT_EMOJI = '\U0001F0CF'
        self.STAND_EMOJI = '\U0001F91A'

        self.footer_message = f'{self.HIT_EMOJI} = Hit, {self.STAND_EMOJI} = Stand'
        self.embed_title = self.CARD_EMOJI + ' Blackjack ' + self.CARD_EMOJI
        self.embed = self.create_embed()

    def gameover(self):
        return not self.hide_card

    def create_deck(self):
        deck = []
        for suit in self.SUITS:
            for value in self.CARD_VALUES:
                card = Card(value, suit)
                deck.append(card)  
        return deck      

    def create_embed(self):
        embed = discord.Embed(title=self.embed_title, colour=light_grey)
        embed.add_field(name=f"{self._dealer_name}  (?)", value=':', inline=False)
        embed.add_field(name=f"{self._player_name}  (0)", value=':', inline=False)
        embed.color = light_grey
        return embed

    # Used to give specific players a card
    def give_card(self, person):
        card = random.choice(self.deck)
        self.deck.remove(card)
        person.hand.append(card)
        person.total += card.number

    def has_blackjack(self, person):
        # Only used at beginning when each person has only 2 cards
        if person.has_ace() and person.total == 11:
            return True
        return False

    def get_hands_as_strings(self):
        # Converts both the player's and dealer's hand into string to be used in the embed
        dealer_string = ':'
        player_string = ':'

        for i in range(len(self.dealer.hand)):
            card = self.dealer.hand[i]            
            if self.hide_card and i == 1:   # Ensures second card of the dealer is hidden if necessary
                dealer_string += f" {self.CARD_EMOJI}"
            else:
                dealer_string += card.string
        
        for i in range(len(self.player.hand)):
            card = self.player.hand[i]
            player_string += card.string

        return dealer_string, player_string

    def update_embed(self):
        # Brings the embed to the current state of the game
        dealer_string, player_string = self.get_hands_as_strings()

        if self.hide_card:
            d_embed_name = f"{self._dealer_name}  (?)"
        else:
            d_current_total = self.dealer.total + 10 if (self.dealer.has_ace() and self.dealer.total <= 11) else self.dealer.total
            d_embed_name = f"{self._dealer_name}  ({d_current_total})"

        p_current_total = self.player.total + 10 if (self.player.has_ace() and self.player.total <= 11) else self.player.total
        p_embed_name = f"{self._player_name}  ({p_current_total})"

        self.embed.set_field_at(index=0, name=d_embed_name, value=dealer_string, inline=False)
        self.embed.set_field_at(index=1, name=p_embed_name, value=player_string, inline=False)

    async def start(self):
        # draw first cards for the player and dealer in correct order
        for _ in range(2):
            self.give_card(self.dealer)
            self.update_embed()
            await asyncio.sleep(self._PAUSE_TIME)
            await self.message.edit(embed=self.embed)

            self.give_card(self.player)
            self.update_embed()
            await asyncio.sleep(self._PAUSE_TIME)
            await self.message.edit(embed=self.embed)

        # Blackjack checks
        if self.has_blackjack(self.dealer) or self.has_blackjack(self.player):
            self.hide_card = False
            self.update_embed()

            if self.has_blackjack(self.dealer) and self.has_blackjack(self.player):
                self.embed.color = yellow
                self.footer_message = "Push"

            elif self.has_blackjack(self.dealer):
                self.embed.color = red
                self.footer_message = "Dealer Blackjack"

            elif self.has_blackjack(self.player):
                self.embed.color = green
                self.footer_message = "Blackjack"

        self.embed.set_footer(text=self.footer_message)
        await asyncio.sleep(self._PAUSE_TIME)
        await self.message.edit(embed=self.embed)

    # Adds a card ot the player and updates the game
    async def hit(self):
        self.give_card(self.player)

        if self.player.is_bust():
            self.hide_card = False
            self.embed.color = red
            self.footer_message = f"Bust. You Lose"
            self.embed.set_footer(text=self.footer_message)

        self.update_embed()
        await self.message.edit(embed=self.embed)

    # Ends the game with the player's current total
    async def stand(self):
        self.hide_card = False

        # Turns over face down card
        self.update_embed()
        await asyncio.sleep(self._PAUSE_TIME)
        await self.message.edit(embed=self.embed)

        while self.dealer.still_dealing():
            self.give_card(self.dealer)
            self.update_embed()
            await asyncio.sleep(self._PAUSE_TIME)
            await self.message.edit(embed=self.embed)

        # accounts for ace high
        for player in [self.player, self.dealer]:
            if player.has_ace() and player.total <= 11:
                player.total += 10 

        if self.dealer.is_bust():
            self.embed.color = green
            self.footer_message = f"Dealer Bust. You Win!"

        elif self.player.total == self.dealer.total:
            self.embed.color = yellow
            self.footer_message = f"Push"

        elif self.player.total > self.dealer.total:
            self.embed.color = green
            self.footer_message = "You Win!"

        else:
            self.embed.color = red
            self.footer_message = "You Lose"

        self.embed.set_footer(text=self.footer_message)
        self.update_embed()
        await asyncio.sleep(self._PAUSE_TIME)
        await self.message.edit(embed=self.embed)