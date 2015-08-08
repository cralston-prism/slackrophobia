# rules

In this game, players try to create an expansion of a 
randomly-generated acronym and then vote on which one was the best.

The bot will start a round by generating an acronym and announcing it 
to the channel. Players may then use the direct message feature of 
their chat program (or the /msg command) to send their ideas to the 
bot.

After roughly 60 seconds, the submission phase will end. The bot will 
gather the responses, shuffle them up, and display them without the 
names of who wrote them. Players may then vote on which one was the 
best by sending the bot a direct message with the number of their 
favorite.

About 60 seconds after that, the bot will show the results of voting, 
along with who wrote each submission. The highest-voted response gets 
3 points, the next place gets 2 points, and the third highest gets 1 
point.

There's also a bonus point for the fastest response in each round.

By default, the game has five rounds. It starts with a 3-letter 
acronym and adds a letter each time. After the 7-letter acronym round 
ends, the scores are added up from all the rounds to determine the 
champion of the match.

The bot then resets and starts again.

(Note: The duration of rounds, the number of rounds, and the 
starting/ending number of letters may have been changed by the person 
running your bot. The values in this document just describe the 
default settings.)
