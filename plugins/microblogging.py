# -*- coding: utf-8 -*-

import datetime
import re
from datetime import datetime
import HTMLParser
import twitter
from stdPlugin import stdPlugin, PluginError

class microblogging(stdPlugin):
    u'''Permet d’interagir avec un compte de microblogging (statusnet/twitter)'''

    events = {'pubmsg': {'exclusive': True, 'command_namespace': 'truite'},
              'run': {'frequency': 300}}

    status_length = 140

    def __init__(self, bot, conf):
        return_val = super(microblogging, self).__init__(bot, conf)
        self.api = twitter.Twitter(auth=twitter.OAuth(**conf['credentials']))
        if not self.api.account.verify_credentials():
            raise PluginError('Invalid microblogging credentials!')
        # storing microblogging settings locally
        self.settings = self.api.account.settings()
        self.last_fetch = self.bot.get_config(self, 'last_fetch', {})
        self.parser = HTMLParser.HTMLParser()

    def send_status(self, message, reply=None):
        params = {'status': message}
        if reply:
            params['in_reply_to_status_id'] = reply
        result = self.api.statuses.update(**params)
        return result['id']

    def repeat_status(self, id):
        result = self.api.statuses.retweet(id=id)
        return result['id']

    def del_status(self, id):
        result = self.api.statuses.destroy(id=id)
        return result['id']

    def get_date(self, date):
        dt = datetime.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')
        return dt.strftime('%d/%m/%y %H:%M:%S')

    def on_pubmsg(self,serv, ev, helper):
        ids = re.findall(r'https?://(?:www.)?twitter.com/(?:#!/)?(?:[a-zA-Z0-9_]+)/status(?:es)?/([0-9]+)', helper['message'])
        answered = False
        if ids:
            for id in ids:
                try:
                    status = self.api.statuses.show(id=id)
                    serv.privmsg(helper['target'], u'[@%s] %s (%s)' %
                                 (status['user']['screen_name'],
                                  self.parser.unescape(status['text']),
                                  self.get_date(status['created_at'])))
                    answered = True
                except Exception as e:
                    serv.privmsg(helper['target'], u'Erreur de récupération')
        if answered:
            return True
        return False

    def on_cmd(self, serv, ev, command, args, helper):
        u'''%(namespace)s <message> : Publie un message de microblogging
        %(namespace)s ?<ID> <message> : Publie un message en réponse à un message donné
        %(namespace)s +<ID> : Répète le message donné
        %(namespace)s !<ID> : Supprime le message donné (réservé aux admins)
        '''
        if self.conf['mode'] != 'rw':
            serv.privms(helper['target'], u'Accès en lecture seule uniquement.')
            return True

        if not command:
            return False
        elif command.startswith('?'):
            message = ' '.join(args)
            try:
                id = self.send_status(message, command[1:])
                serv.privmsg(helper['target'], u'c’est envoyé (%d) !' % id)
                return True
            except Exception, e:
                serv.privmsg(helper['target'], u'erreur lors de '\
                                               +u'l’envoi : %s' % e.message)
            except:
                serv.privmsg(helper['target'], u'Fail.')
        elif command.startswith('+'):
            try:
                self.repeat_status(command[1:])
                serv.privmsg(helper['target'], u'Message répété.')
            except:
                serv.privmsg(helper['target'], u'Fail.')
        elif command.startswith('!'):
            if 'admin' in self.bot.registered_plugins:
                try:
                    if self.bot.registered_plugins['admin'].is_admin(ev.source()):
                        self.del_status(command[1:])
                        serv.privmsg(helper['target'], u'Message supprimé.')
                    else:
                        serv.privmsg(helper['target'], u'Nope.')
                except:
                    serv.privmsg(helper['target'], u'Fail.')
        else:
            args.insert(0, command)
            message = ' '.join(args)
            try:
                id = self.send_status(message)
                serv.privmsg(helper['target'], u'c’est envoyé (%d) !' % id)
                return True
            except Exception, e:
                serv.privmsg(helper['target'], u'erreur lors de '\
                                               +u'l’envoi : %s' % e.message)
        return False

    def on_run(self, serv, helper):
        """ fetches specified timelines in settings. The conf dict may contain a
        list of timeline types, like “mentions”, “home”, “self” or
        “user:screen_name” where screen_name is an existing user.
        """
        #params = {}
        #if self.last_fetch:
        #    params['since_id'] = self.last_fetch
        #mentions = self.api.statuses.mentions_timeline(**params)
        #self.last_fetch = mentions[0]['id']
        #mentions.reverse()
        statuses = {}
        for fetch_type in self.conf['fetch']:
            statuses.update(self.fetch(fetch_type))
        for status_id in sorted(statuses.iterkeys()):
            status = statuses[status_id]
            serv.privmsg(helper['target'], u'[@%s] %s (%s) — %s' %
                         (status['user']['screen_name'],
                          self.parser.unescape(status['text']),
                          self.get_date(status['created_at']),
                          status['id']))
            #serv.privmsg(helper['target'], u'@%s : %s (%d)' % \
            #        (mention['user']['screen_name'], self.parser.unescape(mention['text']), mention['id']))
        self.bot.write_config(self, 'last_fetch', self.last_fetch)

    def fetch(self, fetch_type):
        params = {}
        if fetch_type in ['mentions', 'home']:
            method = '%s_timeline' % fetch_type
        elif fetch_type == 'retweets':
            method = 'retweets_of_me'
        elif fetch_type == 'self':
            method = 'user_timeline'
            params['screen_name'] = self.settings['screen_name']
        elif fetch_type.startswith('user:'):
            method = 'user_timeline'
            params['screen_name'] = fetch_type[5,]
        else:
            raise PluginError('Invalid fetch type: %s' % fetch_type)
        if fetch_type in self.last_fetch:
            params['since_id'] = self.last_fetch[fetch_type]

        statuses = getattr(self.api.statuses, method)(**params)
        status_dict = {}
        if len(statuses) > 0:
            self.last_fetch[fetch_type] = statuses[0]['id']
            for status in statuses:
                status_dict[int(status['id'])] = status
        return status_dict


