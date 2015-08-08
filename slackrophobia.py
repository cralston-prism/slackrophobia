"""
Slackrophobia - a bot for a chat service that implements a well-known acronym game
"""
from __future__ import absolute_import
from __future__ import print_function
import time
import random
import json
import string

from slackclient import SlackClient

crontable = list()
outputs = list()
CONFIG = dict()

###################################################################
#     Things to configure if you're into that sort of thing       #
###################################################################
CONFIG['ignorelist'] = ['U9871234H', 'U54321789', 'U09876543', ]
CONFIG['game_channel'] = 'C12349876'
CONFIG['min_players'] = 1
CONFIG['slack_key'] = 'xoxb-1234567890-zxczxczxczxczxczxczcxzcx'
CONFIG['secret_quit_command'] = 'hotel9juliet#'
###################################################################


class User(object):
    """
    I am a mapping between chat system user id and someone's easily-readable username. I also keep
    track of how to send a direct message to the person and some other game info, like whether or
    not they've played recently and their score.
    """

    def __init__(self, handle=None, realname=None):
        self.handle = handle
        self.realname = realname
        self.score = 0
        self.playing = False

        # slack only
        self.uid = None
        self.channel = None

    def reset(self):
        """
        Called at the end of each game to clear out game state.
        """
        self.score = 0
        self.playing = False

    def played(self):
        """
        Called when player interacts with the game by submitting a phrase or by voting. Makes them
        officially a player.
        """
        self.playing = True

    def points(self, score):
        """
        Adds some points to the player's score.
        """
        self.score += score


class PlayerManager(object):
    """
    This is a sloppy way to manage users but it also makes it super easy to get the scores at the
    end of the game.
    """

    def __init__(self):
        self.loaded = False
        self.all = list()

    def load(self):
        """
        Generic loader method, will be overridden in subclasses
        """
        self.loaded = True

    def get_by_id(self, uid):
        """
        :param uid: un-pronounceable chat ID of a player
        :return: player object pointer
        """
        if not self.loaded:
            self.load()
        for player in self.all:
            if player.uid == uid:
                return player
        return None

    def get_by_name(self, name):
        """
        :param name: username of a player
        :return: player object pointer
        """
        if not self.loaded:
            self.load()
        for player in self.all:
            if player.name == name:
                return player
        return None

    def name_from_id(self, uid):
        """
        :param uid: un-pronounceable chat ID of a player
        :return: username of a player
        """
        player = self.get_by_id(uid)
        if player is not None:
            return player.name
        return ''

    def id_from_name(self, name):
        """
        :param name: username of a player
        :return: un-pronounceable chat ID for a player
        """
        player = self.get_by_name(name)
        if player is not None:
            return player.uid
        return ''

    def reset_all(self):
        """
        Resets player scores and stuff for everyone present.
        :return:
        """
        for player in self.all:
            player.reset()

    def num_playing(self):
        """
        :return: number of players who are actively participating
        """
        count = 0
        for player in self.all:
            if player.playing:
                count += 1
        return count


class SlackPlayerManager(PlayerManager):
    """
    Stores all the players and fetches their data from chat system API
    """
    def load(self):
        """
        Hits chat system's web API to get the user list because for some reason you can't get it
        from the bot interface.
        """
        client = SlackClient(CONFIG['slack_key'])
        users_json = client.api_call('users.list')
        users = json.loads(users_json)
        if users['ok']:
            for user in users['members']:
                if user['deleted']:
                    continue
                uid = user['id']
                name = user['name']
                profile_name = user.get('profile', list()).get('real_name', None)
                player = User(handle=name, realname=profile_name)
                player.uid = uid
                self.all.append(player)
            self.loaded = True


class Pheidippides(object):
    """
    A famous messenger
    """
    CANNED_MESSAGES = {
        'welcome':
            [
                u'''It's your friendly neighborhood Slackrophobia bot''',
                u'''Who's ready for some Slackrophobia?''',
                u'''It's Slackrophobia time. Warm up your keyboards.''',
                u'''100% pure Slackrophobia. Just what the doctor ordered.''',
            ],
        'no-input':
            [
                u"I'm not accepting messages right now, but thanks anyway.",
                u"It's not the right time to message me.",
                u"Is this about the game? Because I'm busy in another window rigging it.",
                u"Oh gosh. AGAIN!? Can't you see it's not the right phase of the game?!",
            ],
        'not-a-vote':
            [
                u"That doesn't look like a vote. Just send the number.",
                u"I think you're trying to vote but I can't tell. Maybe you should focus on a "
                u"number.",
                u"All I need is the number, hon. Try again.",
                u"It's voting time! Vote with a number!",
            ],
        're-vote':
            [
                u"I *know* you're not trying to vote twice. So I'm going to assume that was a "
                u"Valentine.",
                u"tsk tsk tsk, trying to vote again? That's cheating.",
                u"I'm not the GOP. Each person gets only one vote.",
                u"Are you trying to vote twice? Tricky!\nExcept... not.",
                u"Nope.",
            ],
        'vote-self':
            [
                u"I don't let anyone vote for themselves.",
                u"Please don't try to vote for yourself.",
                u"Nice try, but you can't vote for yourself.",
                u"Vote for a response that isn't yours, meathead.",
                u"HA! I bet you thought that would work. Try again.",
            ],
        'good-submit':
            [
                u"That one looks pretty good.",
                u"Nice one. I bet it'll get a lot of votes.",
                u"That's an MVA. Minimum viable acronym.",
                u"With acronym skills like that you'll go far.",
                u"Awesome.",
                u"Got it.",
                u"You're pretty good at this.",
                u"Hey! That one's not half bad.",
                u"Hmm. I'll accept this one. Not sure if everyone else will get it, though.",
                u"All right. I can go with this one.",
                u"Are you sure? Well, you have to be sure, because I'm not letting you change it.",
                u"Looks good.",
                u"Well, they're not all winners.",
            ],
        'bad-num':
            [
                u"There's bad numbers and then there's BAD numbers. Guess which one you gave me.",
                u"Hey, that's not cool. I can do bounds checking.",
                u"Ha. Did you think you were going to \n\n  SEGMENTATION FAULT (core dumped)\n",
                u"That number's out of range and I don't find it funny.",
                u"You are the weakest link.",
                u"Do you feel lucky? I only ask because I caught you trying to break the vote.",
                u"That wasn't as sneaky as you thought it was.",
            ],
        'bad-submit':
            [
                u"That one doesn't quite meet the requirements.",
                u"Wanna try again after looking at the acronym?",
                u"Hahaha. Way to screw it up.",
                u"NOPE.",
                u"What did you think you were responding to?",
                u"That doesn't match the acronym.",
                u"Close. Well. No. Not even close. It was pretty far.",
            ],
        'good-vote':
            [
                u"Huh. I didn't think anyone would vote for that.",
                u"Yeah. we all know that one's probably going to win.",
                u"For $10 I'll let you re-cast that vote.",
                u"OK. But I think you got the number wrong.",
                u"You think THAT was the best?! There really is no accounting for taste.",
                u"I'm writing your vote down but judging you for it.",
                u"No one else voted for that.  Or maybe they did.",
                u"The votes don't really matter. I pick the results at random.",
                u"If you insist...",
            ],
        'multi-submit':
            [
                u"You can't submit more than one.",
                u"Nice try but only one per customer.",
                u"We only let each player enter once.",
                u"You can't change your answer.",
            ],
        'game-over':
            [
                u"*GAME OVER*",
            ],
        'ten-sec-warning':
            [
                u"(Ten seconds remain.)",
                u"psst.. there's ten seconds left",
                u"10s to go this round",
                u"Only ten sec left. Hurry up.",
            ],
        'message-now':
            [
                u"Message me with your idea of what it stands for. The /msg command helps.",
            ],
        'few-votes':
            [
                u"Not enough votes received. Skipping tabulation.",
            ],
        'few-submissions':
            [
                u"Not enough submissions received. I'll be back next round.",
            ],
        'vote-closed':
            [
                u"Voting is now closed.",
            ],
        'play-soon':
            [
                u"Another round will start soon.",
            ],
        'end-submit':
            [
                u"Submissions are now closed. Voting will begin momentarily.",
                u"I'm not accepting any more submissions unless you tip well. Voting will be soon.",
            ],
        'vote-time':
            [
                u"OK it's voting time. Here are your choices:",
                u"Below is the list of things you can vote on:",
                u"If you want to pick one of these it'd be great:",
            ],
        'vote-instructions':
            [
                u"Message me the number of your favorite.",
                u"Pick a favorite and /msg it to me!",
            ],
        'fastest':
            [
                u"It's a new record!",
                u"That one is faster than any before.",
                u"The fastest response yet!",
                u"No one has been that fast before now.",
                u"They got the fastest time ever.",
            ],
    }

    def __init__(self):
        self.queue = list()

    def _add_msg(self, recip, message):
        """
        Hidden method to insert a message.
        """
        self.queue.append([recip, message])

    def dump_queue(self):
        """
        Empty the entire queue to someone who asked for it
        """
        response = self.queue
        self.queue = list()
        return response

    def send_pub(self, message):
        """
        Announce something to the game channel
        """
        self._add_msg(CONFIG['game_channel'], message)

    def send_pvt(self, channel, message):
        """
        Send a single-user message
        """
        self._add_msg(channel, message)

    def greeting(self):
        """
        Lets the channel know the bot started up OK and a game will start soon.
        """
        self.pub_canned('welcome')

    def pub_canned(self, code):
        """
        Send a canned message to the whole channel
        """
        message = self.get_canned(code)
        self.send_pub(message)

    def pvt_canned(self, recip, code):
        """
        Send a canned message to a single user.
        """
        message = self.get_canned(code)
        self.send_pvt(recip, message)

    def get_canned(self, identifier):
        """
        Get a response by label. They're all up in that giant ugly dict.
        """
        if identifier in self.CANNED_MESSAGES:
            count = len(self.CANNED_MESSAGES[identifier])
            return self.CANNED_MESSAGES[identifier][random.randint(0, count - 1)]
        else:
            print(u'Failed to send message. Missing canned for: {}.'.format(identifier))


class SlackronymResponse(object):
    """
    Contains a player's response to the main game phase. Stores votes and other stuff as convenient.
    """

    def __init__(self, user, message):
        self.user = user
        self.message = message
        self.score = 0
        self.timestamp = time.time()


class Slackronym(object):
    """
    This is a single round of the game.
    """
    ALPHABET = u'AAAAAAAAABBCCDDDDEEEEEEEEEEEEFFGGGHHIIIIIIIIIJKLLLL' \
               u'MMNNNNNNOOOOOOOOPPQRRRRRRSSSSTTTTTTUUUUVVWWXYYZ'
    # I was really sad how few Google hits there were for this string

    def __init__(self, length=3):
        self.acro = ''.join(random.sample(self.ALPHABET, length))
        self.responses = list()
        self.voted = list()
        self.submitted = list()
        self.started_at = time.time()
        self.disable = False
        self.first = None

    def add_response(self, user, message):
        """
        Process an acronym submission. Tell the player if it was successful or if there's a problem.
         Or crash.
        """
        if self.disable:
            return
        if user in self.submitted:
            return 'multi-submit'
        if self.validate(message):
            resp = SlackronymResponse(user, message)
            if len(self.responses) == 0:
                self.first = resp
            self.responses.append(resp)
            self.submitted.append(user)
            return 'good-submit'
        else:
            return 'bad-submit'

    def add_vote(self, user, message):
        """
        Try to process a vote, if it's a number. If it's not, either tell the player to vote again
        or just crash.
        """
        if self.disable:
            return
        if user in self.voted:
            return 're-vote'
        if not message.isdecimal():
            return 'not-a-vote'
        num = int(message) - 1
        if num >= len(self.responses) or num < 0:
            return 'bad-num'
        if self.responses[num].user == user:
            return 'vote-self'
        self.responses[num].score += 1
        self.voted.append(user)
        return 'good-vote'

    def validate(self, sentence):
        """
        Make sure the submission matches the acronym and isn't going to hack our Gibson
        """
        i = 0
        attempt = sentence.strip(string.punctuation)
        for word in attempt.upper().split():
            if not word.startswith(self.acro[i]):
                return False
            i += 1
        return True

    def shuffle(self):
        """
        Ends the phase for players to submit acronym expansions.
        """
        if self.disable:
            return
        random.shuffle(self.responses)

    def list_responses(self):
        """
        Return tuples of each entry in in the round
        """
        response = list()
        for resp in self.responses:
            assert isinstance(resp, SlackronymResponse)
            first = False
            if self.first is resp:
                first = True
            response.append((resp.message, resp.score, resp.user, first))
        return response


class SlackGame(object):
    """
    Progresses through game phases. Keeps track of the ends of rounds and the ends of games.
    """
    MAX_ROUNDS = 5
    phases = [
        {
            'name': 'pause',
            'length': 45,
        },
        {
            'name': 'submit',
            'length': 160,
        },
        {
            'name': 'intermission',
            'length': 5,
        },
        {
            'name': 'vote',
            'length': 120,
        },
    ]

    def __init__(self):
        self.messenger = Pheidippides()
        self.players = SlackPlayerManager()
        self.slackronym = None
        self.warned = False
        self.disabled = False
        self.round = 0
        self.phase = 0  # replaces self.current
        self.started_at = time.time()
        self.fastest = 40000
        self.messenger.greeting()

    @property
    def finishes_at(self):
        """
        Quick and dirty math to figure out what time the current round is scheduled to finish.
        """
        return self.started_at + self.phases[self.phase]['length']

    @property
    def phase_name(self):
        """
        Easier way to access the current phase for comparisons.
        """
        return self.phases[self.phase]['name']

    @property
    def warning_time(self):
        """
        Is it warning time?
        :return: bool
        """
        return time.time() + 10 >= self.finishes_at

    @property
    def finished(self):
        """
        Is this round finished? Y/N
        :return: bool
        """
        return time.time() >= self.finishes_at

    def advance(self):
        """
        Moves to the next round, or if the round counter rolls over moves to the next game.
        Triggers events in other objects if it's time to do so.
        """
        if self.phase_name == 'submit':
            self.finish_submit()
        if self.phase_name == 'vote':
            self.finish_vote()
        self.phase += 1
        if self.phase >= len(self.phases):
            self.phase = 0
            self.round += 1
            if self.round >= self.MAX_ROUNDS:
                self.round = 0
                self.finish_game()
        self.started_at = time.time()
        self.warned = False
        if self.phase_name == 'submit':
            self.start_submit()
        if self.phase_name == 'vote':
            self.start_vote()

    def advance_if_needed(self):
        """
        Determines whether the current time is past the scheduled end time of a round and if so,
        calls the advance() method to handle the rest.
        """
        if not self.warned:
            if self.phase_name in ['submit', 'vote', ]:
                if self.warning_time:
                    if not self.slackronym.disable:
                        self.messenger.pub_canned('ten-sec-warning')
                    self.warned = True
                    # else:
                    #     if time.time() + 3 >= self.finishes_at:
                    #         self.messenger.send_pub("*** Get ready! Next phase in 3 seconds! ***")
                    #         self.warned = True
                    # I found this a little too chatty but you might like it
        if self.finished:
            self.advance()

    def start_submit(self):
        """
        Some cleanup at the beginning of the submit round.
        """
        self.slackronym = Slackronym(length=self.round + 3)
        self.messenger.send_pub(
            u'''>>> The next SLACKRONYM is: *{}*. \n'''.format(self.slackronym.acro))
        self.messenger.pub_canned('message-now')

    def finish_submit(self):
        """
        End of submission phase. not much to do.
        """
        self.slackronym.shuffle()
        self.messenger.pub_canned('end-submit')

    def start_vote(self):
        """
        Reset some stuff so we can accept votes, then show the things people can vote on.
        """
        if self.slackronym.disable:
            return
        if len(self.slackronym.responses) < CONFIG['min_players']:
            self.messenger.pub_canned('few-submissions')
            self.slackronym.disable = True
            if self.slackronym.responses > 0:
                abandoned_board = '>>> *Here Are The Submissions Anyway:*\n'
                ctr = 1
                for phrase in self.slackronym.list_responses():
                    player = self.players.get_by_id(phrase[2])
                    abandoned_board += u'''{}. {} (from {})\n'''.format(ctr, phrase[0],
                                                                        player.handle)
                    ctr += 1
                self.messenger.send_pub(abandoned_board)
            return
        self.messenger.pub_canned('vote-time')
        vote_board = '>>> *Submissions:*\n'
        ctr = 1
        for phrase in self.slackronym.list_responses():
            vote_board += u'''{}. {}\n'''.format(ctr, phrase[0])
            ctr += 1
        self.messenger.send_pub(vote_board)
        self.messenger.pub_canned('vote-instructions')

    def finish_vote(self):
        """
        End of voting phase, do cleanup
        """
        if self.slackronym.disable:
            return
        if len(self.slackronym.voted) < CONFIG['min_players']:
            self.messenger.pub_canned('few-votes')
            self.slackronym.disable = True
            return
        self.messenger.pub_canned('vote-closed')
        votes = self.slackronym.list_responses()
        # returns (message,score,user,firstYN) tuples
        votes.sort(key=lambda a: -a[1])
        scoreboard = '>>> *Votes:*\n'
        ctr = 1
        for result in votes:
            # 1. The Quick Fox (4 votes) - Jane gets N points!
            player = self.players.get_by_id(result[2])
            scoreboard += u'''{}. {} ({} votes) - {}'''.format(ctr, result[0], result[1],
                                                               player.handle)
            points = 4 - ctr
            if points > 0:
                if result[1] > 0:
                    scoreboard += u''' gets {} point'''.format(points)
                    player.points(points)
                    if points > 1:
                        scoreboard += 's'
            if result[3]:
                if result[1] > 0:
                    scoreboard += u' (Speed Bonus Point)'
                    player.points(1)
                else:
                    scoreboard += u' (No votes, no Speed Bonus)'
            ctr += 1
            scoreboard += '\n'
        self.messenger.send_pub(scoreboard)
        self.messenger.pub_canned('play-soon')

    def finish_game(self):
        """
        Some cleanup at the end of MAX_ROUNDS of play
        """
        self.messenger.pub_canned('game-over')
        if self.players.num_playing() < CONFIG['min_players']:
            return
        scores = list()
        for player in self.players.all:
            if player.playing:
                scores.append((player.name.title(), player.score))
        scores.sort(key=lambda s: -s[1])
        scoreboard = u'>>> *Scoreboard:*\n'
        ctr = 1
        for score in scores:
            scoreboard += u'''*{}.* {} ({})\n'''.format(ctr, score[0], score[1])
            ctr += 1
        self.messenger.send_pub(scoreboard)
        self.messenger.send_pub(u'''{} is our big winner'''.format(scores[0][0]))

    def process_dm(self, user, channel, message):
        """
        Handle incoming message
        """
        reply = 'no-input'
        player = self.players.get_by_id(user)
        player.played()
        if self.phase_name == 'submit':
            reply = self.slackronym.add_response(user, message)
            if self.slackronym.first is not None:
                if self.slackronym.first.message == message:
                    delta = self.slackronym.first.timestamp - self.slackronym.started_at
                    announce = u'Fastest-finger submission received in {0:.2f}s'.format(delta)
                    self.messenger.send_pub(announce)
                    if delta < self.fastest:
                        self.fastest = delta
                        self.messenger.pub_canned('fastest')
        if self.phase_name == 'vote':
            reply = self.slackronym.add_vote(user, message)
        self.messenger.pvt_canned(channel, reply)

    def dump_messages(self):
        """
        Empty message queue
        """
        return self.messenger.dump_queue()


def slack_cron():
    """
    Main game loop, without the loop. Relies on python-rtmbot's crontable scheduler to call it
    every second or two.
    :return:
    """
    game.advance_if_needed()
    for message in game.dump_messages():
        outputs.append(message)
    if game.disabled:
        for cron in crontable:
            crontable.remove(cron)


def process_message(data):
    """
    Receives messages from python-rtmbot and delivers them to the game logic, devoid of any
    RTMness

    :param data: message from rtmbot. dict containing unicode strings
    :return: nothing
    """
    if 'subtype' in data:
        # ignore messages with subtype. they're mostly edits/favorites
        return
    if game.disabled:
        return
    if not data['channel'].startswith('D'):
        return
    if data['user'] in CONFIG['ignorelist']:
        return
    user = data['user']
    command = data['text']
    channel = data['channel']
    game.process_dm(user, channel, command)


game = SlackGame()
crontable.append([1, 'slack_cron'])
print(u'Slackrophobia: Loaded.')
