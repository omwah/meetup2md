#!/usr/bin/env python

"""
    Downloads meetup event(s) into markdown format which can be used by a
    static web generator such as Pelican.

    Obtains an access token for the given consumer credentials. The 
    authorized application will appear on this page:
    http://www.meetup.com/account/oauth_apps/
"""

from argparse import ArgumentParser
from html2text import html2text
from datetime import datetime

import webbrowser
import logging
import sys
import os
import re

import ConfigParser

from meetup import meetup_api_client as mac

def config_client(config_name=None):
    return get_client(get_config(config_name)[1])

def get_config(filename=None):
    # Use a config in the user's home directory if one is not
    # specified on the command line
    filename = filename or os.path.join(os.path.expanduser("~"), '.meetup2md.cfg')

    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(filename)
    
    if config.has_section('internal'):
        # you probably don't need to worry about this!
        mac.__dict__.update(config.items('internal'))

    return filename, config
    
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
        if args.consumer and len(args.consumer) is 2:
            consumer_key, consumer_secret = args.consumer
            set_token(config, 'consumer', consumer_key, consumer_secret)
        else: 
            print >>sys.stderr, 'Please pass in consumer-key and consumer-secret with --consumer option'
            print >>sys.stderr, 'Set up a key and secret here:'
            print >>sys.stderr, 'https://secure.meetup.com/meetup_api/oauth_consumers/'
            sys.exit()

    mucli = get_client(config)
    
    def access_granted():
        logging.debug("""\
    access-key:     %s
    access-secret:  %s
    
    Congratulations, you've got an access token! Try it out in an interpreter.
              """ % get_token(config, 'access'))

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
            return None
        else:
            oauth_session = mucli.new_session()
            oauth_session.fetch_request_token()
        
            set_token(config, 'request', oauth_session.request_token.key, oauth_session.request_token.secret)

            url = oauth_session.get_authorize_url()
            logging.info("Opening a browser on the authorization page: %s" % url)
            webbrowser.open(url)
            return None
    
    return mucli

def get_option(option_name, config, args, config_section='events', default=None):
    if hasattr(args, option_name) and getattr(args, option_name):
        return getattr(args, option_name)
    elif config.has_option(config_section, option_name):
        return config.get(config_section, option_name)
    else:
        return default

def event_datetime(event):
    return datetime.fromtimestamp(event.time/1000)

def event_oneline_venue(event):
    v = event.venue
    vlist = [ v['name'] ] 
    for acount in range(1,4):
        aname = 'address_%d' % acount
        if v.has_key(aname):
            vlist.append(v[aname])
    for opt_item in ['city', 'state', 'zip']:
        if not v.has_key(opt_item):
            break
        vlist.append(v[opt_item])
    return ', '.join(vlist)

def print_event_summary(event):
    dt = event_datetime(event)
    print 'Name:', event.name
    print 'Title:', event.title
    print 'Time:', dt.strftime('%A %B %d, %Y %I:%M %p')
    print 'Venue:', event_oneline_venue(event)

def get_title(event, title_cleanup=None):
    title = event.name
    if title_cleanup:
        title = re.sub(title_cleanup, '', title).strip()
    return title

def get_clean_description(event):
    text = html2text(event.description)

    # Convert bullet unicode symbols to asterisks
    text = text.replace(u'\u2022', '*')
    # Convert no-break space to space
    text = text.replace(u'\xA0', ' ')

    # Make this a dash
    text = text.replace(u'\u2014', '-')

    # Convert elipses to three periods
    text = text.replace(u'\u2026', '...')

    return text

def write_event_page(event, stream, datetime_format='%Y-%m-%d %H:%M'):
    print >>stream, 'Title: %s' % event.title
    print >>stream, 'Date: %s' % datetime.now().strftime(datetime_format)
    print >>stream, 'event_date: %s' % event_datetime(event).strftime(datetime_format)
    print >>stream, 'event_location: %s' % event_oneline_venue(event)
    print >>stream, 'event_updated: %d' % event.updated
    print >>stream, ''
    print >>stream, get_clean_description(event)

def slugify(title):
    return re.sub('[^-a-z0-9]', '', re.sub('[\s]+', '-', title.lower().strip()))

def event_output_filename(event, output_dir):
    dt = event_datetime(event)
    output_fn = dt.strftime('%Y-%m-%d') + '-%s' % slugify(event.title) + '.md'
    return os.path.join(output_dir, output_fn).encode()

def process_event(event, output_dir=None, overwrite=False, title_cleanup=None):
    event.title = get_title(event, title_cleanup)

    print_event_summary(event)

    if output_dir:
        output_fn = event_output_filename(event, output_dir)
        print ' -> %s' % output_fn
        if not os.path.exists(output_fn) or overwrite:
            with open(output_fn, 'w') as out_obj:
                write_event_page(event, out_obj)
        else:
            logging.error('will not overwrite existing file: %s' % output_fn)

    print '----'

if __name__ == '__main__':
    parser = ArgumentParser(description='Downloads meetup events into text/markdown format for use in static web blogs')

    parser.add_argument('--config', dest='config', 
        help='read & write settings to CONFIG, default is app.cfg')

    # The values here get writtent to the config file
    parser.add_argument('--consumer', dest='consumer', nargs=2,
        help='set the consumer key and secret')
    parser.add_argument('--verifier', dest='verifier', 
        help='verify authorization with code from browser')

    # These options also can be specified in the config file events section
    parser.add_argument('-g', '--group-name', dest='group_name',
        help='group_urlname of the group to retrieve events from')
    parser.add_argument('-f', '--name-filter', dest='name_filter', 
        help='filter out events that match the supplied regular expression')
    parser.add_argument('-t', '--time-range', dest='time_range',
        help='return events scheduled within the given time range, defined by two times separated with a single comma.')
    parser.add_argument('-s', '--status', dest='event_status',
        help='status may be "upcoming", "past", "proposed", "suggested", "cancelled", "draft" or multiple separated by a comma.')
    parser.add_argument('-c', '--cleanup', dest='title_cleanup', 
        help='removes text matching the supplied regular expression from the title')

    parser.add_argument('-o', '--output-dir', dest='output_dir',
        help='directory where to output posts, otherwise only a summary is shown')
    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
        help='overwrite existing files')

    parser.add_argument('-v', '-verbose', dest='verbose', action='store_true',
        help='enable verbose debugging')

    args = parser.parse_args()
   
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    config_name, config = get_config(args.config)
   
    # Do the work of logging in and passing through tokens to get the interface
    mucli = get_interface(config, args)

    # Add a config section for configuring event retrieval if not already existing
    if not config.has_section('events'):
        config.add_section('events')
    
    # Write config with any changes modifications made so far
    with open(config_name, 'wb') as c:
        config.write(c)

    # We have not yet finished setting up keys
    if not mucli:
        sys.exit()

    # Make sure output_dir exists if defined
    if args.output_dir and not os.path.exists(args.output_dir):
        parser.error('output directory must already exist')

    group_name = get_option('group_name', config, args)
    if not group_name:
        parser.error('Must specify name of group to retireve from')

    name_filter = get_option('name_filter', config, args, default='')
    time_range = get_option('time_range', config, args, default='0,1m')
    event_status = get_option('event_status', config, args, default='upcoming')
    title_cleanup = get_option('title_cleanup', config, args)
    output_dir = get_option('output_dir', config, args)

    events = mucli.get_events(group_urlname=group_name, time=time_range, status=event_status)

    for event in events.results:
        if re.search(name_filter, event.name):
            process_event(event, output_dir=output_dir, overwrite=args.overwrite, title_cleanup=title_cleanup)
