=========
meetup2md
=========

meetup2md is a simple script that downloads events from a Meetup.com group and outputs them in Markdown format. It requires the html2text module. It was created to make it easy to create posts for static site generator websites that mirror information from Meetup.com. The script also adds metadata from the Meetup events that can be used by the site generator for displaying event date and location.

Installing
==========

This project uses git submodules. We need to be initialize and pull after cloning this repository.

.. sourcecode:: shell-session

    $ git submodule init && git submodule update

Setting Up OAuth
================

We need to set up OAuth so the script can access Meetup. Create a new consumer key and secret here:
https://secure.meetup.com/meetup_api/oauth_consumers/create

Set up authentication with the program:

.. sourcecode:: shell-session
    
    $ ./meetup2md.py --consumer <key_from_website> <secret_from_website>

Hit allow on the web page that is loaded by the script. Now pass the verification code to the script:

.. sourcecode:: shell-session

    $ ./meetup2md.py --verifier <verification_code>

Usage
=====

Retrieving all events from a group. The value specified to -g is the part of the Meetup group's URL after meetup.com

.. sourcecode:: shell-session

    $ ./meetup2md.py -g MyMeetupGroup

Filter by the event titles (regexp)

.. sourcecode:: shell-session

    $ ./meetup2md.py -g MyMeetupGroup -f "Monthly Brunch"

Specify a time range, for example within the next month:

.. sourcecode:: shell-session

    $ ./meetup2md.py -g MyMeetupGroup -t ,1m

Remove a string (regexp) from the titles saved to the markdown page:

.. sourcecode:: shell-session

    $ ./meetup2md.py -g MyMeetupGroup -c "Monthly"

Actually save the posts instead of just seeing a summary of the events. Directory must already exist:

.. sourcecode:: shell-session

    $ ./meetup2md.py -g MyMeetupGroup -o meetup_posts

Configuring
===========

If no config filename is specified on the command line with the --config option then meetup2md will look for a config at: $HOME/.meetup2md.cfg.

Edit the [events] section of the config using the long names of the various arguments supplied on the command line:

.. sourcecode:: shell-session

    [events]
    group_name = MyMeetupGroup
    name_filter = Filter On Events With This Regex
    title_cleanup = ^Remove This Regex from Title Placed into Markdown Files
