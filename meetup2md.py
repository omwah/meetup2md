#!/usr/bin/env python

"""
    Downloads meetup event(s) into markdown format which can be used by a
    static web generator such as Pelican.

    Obtains an access token for the given consumer credentials. The 
    authorized application will appear on this page:
    http://www.meetup.com/account/oauth_apps/
"""

from argparse import ArgumentParser
import webbrowser
import html2text
import logging
import sys

import ConfigParser

from meetup import meetup_api_client as mac

def config_client(config_name=None):
    return get_client(get_config(config_name)[1])

def get_config(name=None):
    name = name or 'app.cfg'

    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(name)
    
    if config.has_section('internal'):
        # you probably don't need to worry about this!
        mac.__dict__.update(config.items('internal'))

    return name, config
    
def get_client(config):
    consumer_key, consumer_secret = get_token(config, 'consumer')
    if config.has_section('access'):
        access_key, access_secret = get_token(config, 'access')
        return mac.MeetupOAuth(consumer_key, consumer_secret, access_key=access_key, access_secret=access_secret)
    else:
        return mac.MeetupOAuth(consumer_key, consumer_secret)

def get_token(config, name):
    return config.get(name, 'key'), config.get(name, 'secret')

def set_token(config, name, key, secret):
    config.add_section(name)
    config.set(name, 'key', key)
    config.set(name, 'secret', secret)

def get_interface(config, args):
    if not config.has_section('consumer'):
        if len(args) is 2:
            consumer_key, consumer_secret = args
            set_token(config, 'consumer', consumer_key, consumer_secret)
        else: option.error('please pass in consumer-key and consumer-secret')

    mucli = get_client(config)
    
    def access_granted():
        print """\
    access-key:     %s
    access-secret:  %s
    
    Congratulations, you've got an access token! Try it out in an interpreter.
              """ % get_token(config, 'access')

    if config.has_section('access'):
        access_granted()
    else:
        if config.has_section('request'):
            if not args.verifier:
                sys.exit("To complete the process you must supply a --verifier")
            request_key, request_secret = get_token(config, 'request')
            oauth_session = mucli.new_session(request_key=request_key, request_secret=request_secret)
            print "    member_id:      %s" % oauth_session.fetch_access_token(args.verifier)
            set_token(config, 'access', oauth_session.access_token.key, oauth_session.access_token.secret)
            access_granted()
        else:
            oauth_session = mucli.new_session()
            oauth_session.fetch_request_token(callback=args.callback)
        
            set_token(config, 'request', oauth_session.request_token.key, oauth_session.request_token.secret)

            if (args.authenticate):
                url = oauth_session.get_authenticate_url()
            else:
                url = oauth_session.get_authorize_url()
            print "Opening a browser on the authorization page: %s" % url
            webbrowser.open(url)
    
    return mucli

if __name__ == '__main__':
    parser = ArgumentParser(description='Downloads meetup events into text/markdown format for use in static web blogs')
    parser.add_argument('--config', dest='config', 
        help='read & write settings to CONFIG, default is app.cfg')
    parser.add_argument('--verifier', dest='verifier', 
        help='oauth_callback for request-token request, defaults to oob')
    parser.add_argument('--callback', dest='callback', default='oob',
        help='oauth_verifier, required to gain access token')
    parser.add_argument('--authenticate', dest='authenticate', action='store_true',
        help='pass in to use authentication end point')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG)
    
    config_name, config = get_config(args.config)
   
    mucli = get_interface(config, args)
    
    with open(config_name, 'wb') as c:
        config.write(c)

    events = mucli.get_events(group_urlname="SGVTech")

    import IPython
    IPython.embed()
