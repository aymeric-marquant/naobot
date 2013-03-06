# -*- coding: utf-8 -*-

import os
from datetime import datetime
from stdPlugin import stdPlugin, PluginError

class logger(stdPlugin):
    u'''Enregistre tout ce qui se passe sur un chan, et génère un fichier texte'''

    events = {'pubmsg': {'exclusive': False, 'command_namespace': 'log'},
              'action': {'exclusive': False},
             }

    url = 'https://log.naohack.org/%(chan)s/%(log)s'
    file_format = '%(year)s-%(month)s-%(day)s.log'

    def __init__(self, bot, conf):
        return_val = super(logger, self).__init__(bot, conf)
        try:
            chans = self.bot.conf['chans'] if not self.bot.channels else self.bot.channels
            self.combined_file = {}
            for chan in chans:
                path = os.path.join(os.getcwd, 'output', chan.replace('#', ''))
                if not os.path.isdir(path)
                    os.makedirs(path)
                self.combined_file[chan] = open(os.path.join(path,
                                                'combined.log'), 'aw')
        except Exception, e:
            pass
        return return_val

    def on_pubmsg(self, serv, ev, helper):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = '[%s] <%s> %s\n' % (now, helper['sender'], helper['message'])
        self.combined_file[helper['target']].write(line)
        return False

    def on_action(self, serv, ev, helper):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = '[%s] * %s %s\n' % (now, helper['sender'], helper['message'])
        self.combined_file[helper['target']].write(line)

    def on_cmd(self, serv, ev, command, args, helper):
        u'''%(namespace)s : indique l’URL du log.'''
        serv.privmsg(helper['target'], u'Les logs sont disponibles sur %s.' % \
                     (self.url % helper['target'], 'combined.log'))
        return True

