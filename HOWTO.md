# howto

To run this, you need to download python-rtmbot 
https://github.com/slackhq/python-rtmbot and you need a Slack 
integration token (details at https://api.slack.com/bot-users)

Or, for the lazy:

* `git clone https://github.com/slackhq/python-rtmbot`

* `cd python-rtmbot`

* `echo "SLACK_TOKEN: xoxb-.......\nDEBUG: False" > rtmbot.conf`

* `cd plugins`

* `ln -s ../../slackrophobia/slackrophobia.py`

* `cd ..`

* `./rtmbot.py`

You should place your slack token in place of `xoxb-.......`

You should also edit slackrophobia.py and fill in the config details. In 
particular, `CONFIG['game_channel']` has to be set to the slack ID of 
the channel you want to use (get it from 
https://api.slack.com/methods/channels.list) and `CONFIG['slack_key']` 
has to be set to your API token (you can use the same one as for 
rtmbot.conf).  Ignored users is optional but if you have multiple bots 
on your team it might be helpful to have them ignore each other.

You'll have to explicitly invite the bot user to your game channel after 
creating the bot (and the channel). You can do this from inside the 
Slack client by clicking on the drop-down menu from the channel name.
