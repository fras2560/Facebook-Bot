'''
@author: Dallas Fraser
@author: 2019-05-23
@organization: MLSB
@project: Facebook Bot
@summary: Action for when a captain/convenor submits a score
'''
from api.actions import ActionInterface


class SubmitScoreAction(ActionInterface):

    def process(self, message, action_map):
        self.action_map = action_map
        self.message = message
