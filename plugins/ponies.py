# -*- coding: utf-8 -*-

import operator
import os
import re
from stdPlugin import stdPlugin, PluginError


class ponies(stdPlugin):
    u'''Surveille la popularité de chaque personnage de My Little Pony:
    Friendship Is Magic.
    '''

    events = {'pubmsg': {'exclusive': False, 'command_namespace': 'ponies'},
              'action': {'exclusive': False},
              # 'join': {'exclusive': False},
              }

    def __init__(self, bot, conf):
        return_val = super(ponies, self).__init__(bot, conf)
        try:
            file = open(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'ponies')).readlines()
            ponies_list = [tuple(line.replace('\n', '').split(':', 1)) for
                           line in file]
            self.ponies = {}
            self.exps = {}
            for pony in ponies_list:
                self.ponies[pony[0]] = pony[1]
                self.exps[pony[0]] = re.compile(r'\b%s\b' % pony[0], re.U |
                                                re.I)
            chans = self.bot.conf['chans'] if not self.bot.channels else\
                self.bot.channels
            self.stats = {}
            for chan in chans:

                self.stats[chan] = self.bot.\
                    get_config(self, chan, dict.fromkeys(self.ponies, 0))
        except Exception, e:
            raise PluginError('No ponies found: %s.' % e)
        self.users = self.bot.get_config(self, 'users', [])
        return return_val

    def on_pubmsg(self, serv, ev, helper):
        for pony in self.ponies.keys():
            if self.exps[pony].search(helper['message']):
                try:
                    self.stats[helper['target']][pony] += 1
                except KeyError:
                    self.stats[helper['target']][pony] = 1
                self.bot.write_config(self, helper['target'],
                                      self.stats[helper['target']])
        return False

    def on_action(self, serv, ev, helper):
        return self.on_pubmsg(serv, ev, helper)

    def on_cmd(self, serv, ev, command, args, helper):
        u'''%(namespace)s best : indique qui est le meilleur poney.
        %(namespace)s stats : indique la liste des 5 meilleurs poneys.
        %(namespace)s score <pony> : indique le score du poney indiqué
            (sensible à la casse).
        '''
        if command == 'best':
                best_pony = self.get_stats(helper['target'])[0]
                serv.privmsg(helper['target'], u'%s est le meilleur '
                             u'poney ! %s' %
                             (best_pony['name'], best_pony['url']))
                return True
        elif command == 'stats':
            stats = self.get_stats(helper['target'])[0:5]
            serv.privmsg(helper['target'], u'Classement des poneys :')
            for pony in enumerate(stats):
                serv.privmsg(helper['target'], u'    %d. %s: %d' %
                             ((pony[0]+1), pony[1]['name'],
                              pony[1]['score']))
            return True
        elif command == 'score':
            pony_name = ' '.join(args)
            if pony_name not in self.ponies.keys():
                serv.privmsg(helper['target'], u'Ce poney n’existe pas.')
                return True
            else:
                serv.privmsg(helper['target'], u'%s : %s points' % (pony_name,
                             self.stats[helper['target']][pony_name]))
        else:
            serv.privmsg(helper['target'], u'Je ne connais pas cette '
                         'commande.')
            return True

    def on_join(self, serv, ev, helper):
        if helper['sender'] not in self.users and \
                helper['sender'] != serv.username:  # NOUVEAU
            serv.privmsg(helper['target'], (u'Bonjour %s, quel est ton poney '
                                            + u'préféré ?') % helper['sender'])
            self.users.append(helper['sender'])
            self.bot.write_config(self, 'users', self.users)
            return True

    def get_stats(self, chan):
        stats = sorted(self.stats[chan].iteritems(),
                       key=operator.itemgetter(1))
        ponies_stats = []
        for stat in stats:
            pony = {'name': stat[0],
                    'url': self.ponies[stat[0]],
                    'score': stat[1]}
            ponies_stats.append(pony)
        ponies_stats.reverse()
        return ponies_stats
