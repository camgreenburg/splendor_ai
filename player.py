from __future__ import print_function
from constants import * 
from itertools import combinations

import numpy as np 

"""
uncommon strategies not supported:

* using gold instead of a regular color in order to prevent a player from grabbing one or two gems of a particular color
on their turn (fairly uncommon)

* telling a player what your hidden card is so that it is more obvious to them that you can
purchase something/are more likely to purchase something that may further their interests in some way (very rare)

* take 1 gem each from 2 separate piles to allow another player to take a certain color or to allow yourself to take 3 next turn (never seen it)

"""

class Player(object):
	def __init__(self, game, id, order, ai=None):
		self.game = game 
		self.id = id
		self.order = order 
		if ai is not None:
			self.ai = ai
		else:
			self.ai = SplendorAI()

		self.points = 0
		#cards that contribute to cost reduction and points
		self.owned_cards = []
		#cards that can be purchased only by player
		self.reserved_cards = []
		#faster way of keeping track of cards
		self.n_cards = 0
		self.n_reserved_cards = 0
		self.n_reserved_cards_tiers = [{i:0 for i in range(3)}]
		self.gems = {color:0 for color in COLOR_ORDER}
		self.n_gems = 0
		self.discounts = {color:0 for color in COST_COLOR_ORDER}
		self.objectives = []
		self.win = False
		#self.draw = False#will allow multiple victories in rare instances

		#describes the history for the current game
		#this should be in [[data], ...] format, where [data] is a numpy vector of the game state
		# from the perspective of the player
		self.history = []
		#describes history for all games; this will be used to train the neural network
		#this should be in [[data, win, game_id], ...] format
		self.extended_history = []

	def take_turn(self):
		"""
		TODO: record player state at end of turn after action is made

		the player takes a turn

		"""
		self.make_turn_action()

		self.objective_check()
		if not self.game.last_turn:
			self.victory_check()

	def make_turn_action(self):
		"""
		
		"""
		purchase_options = self.simulate_purchasing_options()
		reserving_options = self.simulate_reserving_options()
		gem_taking_options = self.simulate_gem_taking_options()

		all_options = purchase_options + reserving_options + gem_taking_options 
		option = self.determine_best_option(all_options)
		if option is None:
			#really shouldn't happen
			print("PLAYER CANNOT TAKE ACTION")
			return 1
		#option[2] is action type
		if option[2]=='purchase_available_card':
			self.purchase_available_card(**option[1])
		elif option[2]=='purchase_reserved_card':
			self.purchase_reserved_card(**option[1])
		elif option[2]=='reserve_card_on_top':
			self.reserve_card_on_top(**option[1])
		elif option[2]=='reserve_card_on_board':
			self.reserve_card_on_board(**option[1])
		elif option[2]=='take_gems':
			self.take_gems(**option[1])
		return 0

	"""
	BELOW ARE SIMULATION FUNCTIONS
	for each of these functions, the following should be done:
		1. all possible moves should be determined
		2. for each possible move, a semi-simulation should be made of the resulting board state. 
		   I recommend implementing & using save_state()/load_state() for both the Player and Game classes
		   so that you can directly modify these; I have put a "move_cards" argument to some functions so that they won't 
		   shift around cards if you want to avoid that; you should use copy/deepcopy to copy lists/nested objects 
		   when creating these states
		3. for each state, there should be a serialization of the entire game from that player's point of view. For example,
		   a game of texas hold 'em would have a binary (1s and 0s) vector of length 52 describing  your hand, a binary vector
		   describing the state of the cards in the center, and perhaps some other vectors describing betting/folding of 
		   the other players (since you can't see their cards). In this game, you may be able to use integer values for gem costs.
		4. the SplendorAI class needs to be further developed, but it will take in these serializations and output the probabilities;
		   With these probabilities, a decision should be made by processing them through determine_best_option(). Initially I want the
		   actual probability to have less impact on the chosen decision in order to increase randomness, but as the network becomes
		   trained, I want the better probabilities to have a much higher chance of being chosen
		5. The chosen action will be taken with the keyword arguments provided in the option, and the turn will continue.


	"""

	def simulate_purchasing_options(self):
		"""
		creates all possible purchasing options and returns corresponding probabilities and action types

		FORMAT:
		 list of
		  [prob, action_kwargs, action_type]
		"""

	def simulate_reserving_options(self):
		"""
		creates all possible reserving options and returns corresponding probabilities and action types

		FORMAT:
		 list of
		  [prob, action_kwargs, action_type]
		"""

	def simulate_gem_taking_options(self):
		"""
		creates all possible gem-taking options and returns corresponding probabilities and action types

		FORMAT:
		 list of
		  [prob, action_kwargs, action_type]
		"""

	def determine_best_option(self, all_options):
		"""
		will use game-based hyperparameters to decide on best options
		namely, a "fuzziness" parameter will select a choice based on the probabilities, and 
		earlier in the training process, there will be more leeway in determining 

		
		"""
		if len(all_options) == 0:
			return None

	def serialize(self, attribute_modification_list=None):
		"""
		args:
		 attribute_modification_list - [ {attribute_name:change, ...}, ... ]
		 this should be a list of dictionaries that describe changes to be made to a theoretical 

		this should return a numpy-matrix with a number of rows equal to the length of the outer list,
		for each possible change
		"""

	def save_state(self):
		"""
		I recommend using this for storing a few attributes when simulating so you 
		can directly modify some of the player attribute variables;
		you can also have game.save_state() called from here
		"""

	def load_state(self):
		"""
		loads previous state after self.save_state() has been called;
		you can alsoe have game.load_state() called from here
		"""

	#GENERAL CHECKING AND ACTION FUNCTIONS
	def get_available_cards(self, tier):
		"""
		does not include reserved cards
		"""
		if tier==1:
			cards = self.game.available_tier_1_cards
		elif tier==2:
			cards = self.game.available_tier_2_cards
		else:
			cards = self.game.available_tier_3_cards
		return cards 

	def card_in_position_purchasing_cost(self, tier, position):
		card = self.get_available_cards(tier)[position]
		return self.card_purchasing_cost(card)

	def card_purchasing_cost(self, card):
		"""
		this doubles as a boolean check
		"""
		cost = card['cost']
		#calculates the surplus of each color for each part of the cost
		differences = {color:self.gems[color]+self.discounts[color]-cost[color]
		for color in COLOR_ORDER}
		#takes the total amount of gems one is short by
		net_difference = -sum([max(0, difference) for difference in differences.values()])
		#checks to see if extra gold is enough to purchase 
		if net_difference < self.gems['gold']:
			return None
		elif net_difference==0:
			base_cost = {color:cost[color] - self.discounts[color] for color in COST_COLOR_ORDER}
			base_cost['gold'] = 0
			return base_cost
		else:
			base_cost = {color:cost[color] - self.discounts[color] for color in COST_COLOR_ORDER}
			working_gold = min(self.gems['gold'], net_difference)
			base_cost['gold'] = working_gold
			return base_cost

	def purchase_available_card(self, tier, position, move_cards=True):
		card = self.get_available_cards(tier).pop(position)
		card_cost = self.card_purchasing_cost(card)
		#add points
		self.points+= card['points']
		#add color
		self.discounts[card['color']] += 1
		#subtract gems
		for color, amount in card_cost.iteritems():
			self.gems[color] -= amount 
			self.n_gems -= amount
		#add card to inventory
		self.n_cards += 1
		if move_cards:
			self.owned_cards.append(card)
			#add new card, display warning if deck is empty
			new_card_added = self.game.add_top_card_to_available(tier)
			if not new_card_added:
				print("WARNING: tier %s deck ran empty!" % tier)

	def purchase_reserved_card(self,  position):
		if move_cards:
			card = self.reserved_cards.pop(position)
		else:
			card = self.reserved_cards.[position]
		card_cost = self.card_purchasing_cost(card)
		#add points
		self.points+= card['points']
		#add color
		self.discounts[card['color']] += 1
		#subtract gems
		for color, amount in card_cost.iteritems():
			self.gems[color] -= amount 
			self.n_gems -= amount
		#add card to inventory
		self.n_cards += 1
		if move_cards:
			self.owned_cards.append(card)
		self.n_reserved_cards -=1
		self.n_reserved_cards_tiers[card['tier']] -= 1

	def reserve_card_on_top(self, tier, move_cards=True):
		self.n_reserved_cards += 1
		if move_cards:
			self.reserved_cards.append(self.game.get_deck(tier).pop())
		self.n_reserved_cards_tiers[tier] += 1
		if self.n_gems < 10 and game.gems['gold'] > 0:
			self.take_gems({'gold':1})
		return 0

	def reserve_card_on_board(self. tier, position):
		self.n_reserved_cards += 1
		self.reserved_cards.append(self.game.get_available_cards(tier).pop(position))
		self.game.add_top_card_to_available(tier)
		self.n_reserved_cards_tiers[tier] += 1
		if self.n_gems < 10 and game.gems['gold'] > 0:
			self.take_gems({'gold':1})
		return 0 

	def objective_check(self):
		"""
		at end of turn, checks to see if any objectives are met
		if no, then returns 0
		if only one, then it adds that and returns a 1
		if more than one, decides which one, then adds it, then returns 1
		"""
		possible_objectives = []
		for i, objective in self.game.objectives:
			can_get = True
			for color, value in objective.iteritems():
				if self.discounts[color] < value:
					can_get = False
					break
			if can_get:
				possible_objectives.append(i)
		if len(possible_objectives) == 0:
			return 0
		elif len(possible_objectives) == 1:
			self.points+=3 
			self.objectives.append(self.game.objectives.pop(possible_objectives[0]))
		else:
			objective = self.decide_on_objective(possible_objectives)
			self.points+=3
			self.objectives.append(self.game.objectives.pop(objective))	
		return 1

	#TODO
	def decide_on_objective(self, possible_objectives):
		"""
		MEH METHOD: randomly choose an objective
		AI METHOD: forecast all possibilities (3 at most, but most likely 2) and choose the one that most likely results in winning
		DERIVED METHOD: check to see if any other players are within a turn of getting the other card; not 100% exact bc of reserved cards, and might be tedious
		"""

	def victory_check(self):
		"""
		if premature, will not compare number of cards and will 
		"""
		if self.score >= 15:
			self.game.last_turn = True

	def take_gems(self, gems):
		"""
		adds gems to inventory
		"""
		for color, amount in gems.iteritems():
			self.gems[color] += amount
			self.game.gems[color] -= amount
			self.n_gems +=1
		return 0

	def take_gems_options(self):
		possibilities = []
		if self.n_gems == 10:
			return []
		elif self.n_gems == 9:
			#check all piles that have at least one
			#can only take 1
			for color in COST_COLOR_ORDER:
				if self.game.gems[color] > 0:
					possibilities.append({color:1})
			return possibilities

		#check all piles that have at least one and all piles with at least 4
		#can only take 2 from >=4 or 1 from any 2 if player has 8 gems
		#otherwise no additional restrictions
		single_colors = set()
		double_colors = set()
		for color in COST_COLOR_ORDER:
			if self.game.gems[color] > 0:
				if self.game.gems[color] > 3:
					double_colors.add(color)
				single_colors.add(color)
		for color in double_colors:
				possibilities.append({color:2})
		if self.n_gems == 8:
			if len(single_colors)==1:
				color = list(single_colors)[0]
				possibilities.append({color:1})
			else:
				possibilities += color_combinations(single_colors, 2)
		else:
			if len(single_colors)==1:
				color = list(single_colors)[0]
				possibilities.append({color:1})
			elif len(single_colors)==2:
				possibilities += color_combinations(single_colors, 2)
			else:
				possibilities += color_combinations(single_colors, 3)
		return possibilities

	def reset(self, reset_extended_history=False):
		"""
		used when you want to keep the same players (saves some AI loading, possibly) 
		and start a new game; extended history is kept unless the flag is set to true to
		reset it
		"""
		self.points = 0
		#cards that contribute to cost reduction and points
		self.owned_cards = []
		#cards that can be purchased only by player
		self.reserved_cards = []
		#faster way of keeping track of cards
		self.n_cards = 0
		self.n_reserved_cards = 0
		self.n_reserved_cards_tiers = [{i:0 for i in range(3)}]
		self.gems = {color:0 for color in COLOR_ORDER}
		self.n_gems = 0
		self.discounts = {color:0 for color in COST_COLOR_ORDER}
		self.objectives = []
		self.win = False
		#self.draw = False#will allow multiple victories in rare instances

		#describes the history for the current game
		self.history = []
		if reset_extended_history:
			self.extended_history = []


def color_combinations(colors, n):
	"""
	returns the cost in the form of a dictionary 
	"""
	combos = combinations(colors, n)
	return [{color:1 for color in combo} for combo in combinations]
