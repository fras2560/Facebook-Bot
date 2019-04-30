'''
@author: Dallas Fraser
@author: 2019-08-27
@organization: MLSB
@project: Facebook Bot
@summary: Action to determine the facebook user to someone in the legaue
'''
from api.actions import Action
from api.actions.welcome import WelcomeAction
from api.variables import PAGE_ACCESS_TOKEN, ASK_EMAIL_COMMENT,\
    EMAIL_NOT_FOUND, LOCKED_OUT_COMMENT
from api.logging import LOGGER
from api.message import Message
from api.errors import FacebookException, IdentityException
import requests
FACEBOOK_URL = "https://graph.facebook.com/v2.6/"


class IdentifyUser(Action):
    ACTION_IDENTIFIER = "Looking up the user"
    EMAIL_STATE = "Asking for email"
    UNKNOWN_STATE = "Cannot find the user, user should consult convenors"
    IMPOSTER_STATE = "Trying to steal someone's else email"
    LOCKED_OUT_STATE = " Locked out for trying 3 different emails"

    def process(self):
        """Process the facebook id"""
        facebook_id = self.message.get_sender_id()
        user = self.database.get_user(facebook_id)
        if user is None:
            LOGGER.debug(
                "Trying to identify facebook id {}".format(facebook_id))
            url = (FACEBOOK_URL +
                   "{}?fields=first_name,last_name&access_token={}".format(
                       facebook_id, PAGE_ACCESS_TOKEN))
            request_response = requests.get(url)
            if request_response.status_code != 200:
                LOGGER.critical("Facebook services not available")
                LOGGER.critical(str(request_response.json()))
                raise FacebookException("Facebook services not available")
            data = request_response.json()

            # now we know the person's facebook name
            name = data['first_name'] + " " + data['last_name']
            user = self.database.create_user(facebook_id, name)
            user["action"] = {"id": IdentifyUser.ACTION_IDENTIFIER}
            self.database.save_user(user)
        elif (user["action"]["state"] == IdentifyUser.IMPOSTER_STATE or
              user["action"]["state"] == IdentifyUser.LOCKED_OUT_STATE):
            # can ignore for now
            return
        # check if can find the user based upon their name
        player = self.database.lookup_player(name)
        if player is None:
            self.check_email(user)

    def check_email(self, user):
        tokens = self.message.split(" ")
        email = None
        for token in tokens:
            if "@" in token:
                email = token
                break
        if email is None:
            message = Message(user["facebook_id"], message=ASK_EMAIL_COMMENT)
            self.messenger.send_message(message)
            user["action"]["wrongGuesses"] = 0
            user["action"]["state"] = IdentifyUser.EMAIL_STATE
        else:
            try:
                player = self.database.lookup_player_email(email.lower())
                if self.database.already_in_league(player):
                    user["action"]["state"] = IdentifyUser.IMPOSTER_STATE
                else:
                    user["player"] = player
                    self.database.save_user(user)
                    self.successful(user)
            except IdentityException as e:
                LOGGER.error(str(e))
                LOGGER.error("Unable to find email: {}".format(email))
                wrongGuesses = user["action"]["wrongGuesses"] + 1
                user["action"]["wrongGuesses"] = wrongGuesses
                if wrongGuesses < 3:
                    message = Message(
                        user["facebook_id"], message=EMAIL_NOT_FOUND)
                    self.messenger.send_message(message)
                else:
                    user["action"]["state"] = IdentifyUser.LOCKED_OUT_STATE
                    message = Message(
                        user["facebook_id"], message=LOCKED_OUT_COMMENT)
                    self.messenger.send_message(message)
                self.database.save_user(user)

    def successful(self, user):
        """Upon being successful update the user to the next action"""
        user['action'] = {"id": WelcomeAction.ACTION_IDENTIFIER}
        self.database.save_user(user)
