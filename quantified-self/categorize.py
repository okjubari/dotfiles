#!/usr/bin/env python3
import collections
import datetime
import dateutil.parser as dateutil
import json
import re

def default_parser(class_, instance, role, title):
    if class_:
        return [ class_ ]
    if instance:
        return [ instance ]
    if role:
        return [ role ]
    if title:
        return [ title ]

    return []

class_parsers = collections.defaultdict(lambda: default_parser)

def class_parser(class_):
    def w(f):
        class_parsers[class_] = f
        return f
    return w

### START PARSERS ###
# Add parsers for the class

@class_parser('Google-chrome')
def google_chrome(class_, instance, role, title):
    if role == 'browser':
        res = re.match(r'^(.*) \[(.*)\]\[(.*)\] - Google Chrome$', title)
        if res:
            page_title = res.group(1)
            website = res.group(2)
            path = res.group(3)
            if website == 'https://www.youtube.com' and path == 'watch':
                youtube_name = re.match('^(.*) - YouTube$', page_title).group(1)
                return [class_, website, youtube_name]
            if website == 'https://github.com':
                r = re.match('^([^/]*)(/([^/]*))?.*$', path)
                if r:
                    github_owner = r.group(1)
                    github_repo = r.group(3)
                    if github_repo:
                        return [class_, website, github_owner, github_repo]
                    else:
                        return [class_, website, github_owner]
            return [class_, website, path]
    return [class_]

@class_parser('Skype')
def skype_title_to_category(class_, instance, role, title):
    res = re.match(r'^(\[\d+\])?(.*) - Skype™$', title)

    if res:
        name = res.group(2)

        # Handle renames and aliases
        if name == 'Svitlana Boiko (Sveta)':
            name = 'Svitlana Boiko'

        return [class_, name]
    return [class_]

@class_parser('Emacs')
def emacs_title_to_category(class_, instance, role, title):
    # Emacs title is "[mode] projectile-project-name
    if title:
        res = re.match(r'^\[(.*)\] (.*)$', title)
        if res:
            return [class_, res.group(2), res.group(1)]
    return [class_]

@class_parser('Vlc')
def vlc_title_to_category(class_, instance, role, title):
    if title:
        res = re.match(r'^(.*) - VLC media player$', title)
        if res:
            return [class_, res.group(1)]
    return [class_]

@class_parser('smplayer')
def smplayer_title_to_category(class_, instance, role, title):
    if title:
        res = re.match(r'^(.*) - SMPlayer$', title)
        if res:
            return [class_, res.group(1)]
    return [class_]

@class_parser('sun-applet-PluginMain')
def java_applet(class_, instance, role, title):
    return ['Java applet']

@class_parser('Thunderbird')
def thunderbird(class_, instance, role, title):
    return [class_, instance]

@class_parser('Wine')
def wine(class_, instance, role, title):
    return [class_, instance]

### END OF PARSERS ###

def category(x):
    """Given a log entry, returns it's category"""
    instance = x.get('instance')
    class_ = x.get('class')
    title = x.get('title')
    role = x.get('role')

    return class_parsers[class_](class_, instance, role, title)

def category_to_string(c):
    return ' > '.join(c)

# category -> timedelta
totals = collections.defaultdict(datetime.timedelta)
by_day = collections.defaultdict(lambda: collections.defaultdict(datetime.timedelta))

def add_time(c, start, end, delta):
    for i in range(len(c) + 1):
        s = category_to_string(c[:i])
        totals[s] += delta
        by_day[start.date()][s] += delta

current = None

# print('dataRaw = [')
cur_id = 1
with open('/home/rasen/log.txt', 'r') as f:
    for line in f.readlines():
        x = json.loads(line)
        c = category(x)
        # print(x, c)

        if ((x['activity'] == 'title' and current[1] != c) or
            (x['activity'] == 'unfocus')):

            # handle poweroffs
            if current:
                start = dateutil.parse(current[0]['time'])
                end = dateutil.parse(x['time'])

                # if start < dateutil.parse('2017-02-06T00:00:00+02:00'):
                #     continue

                delta = end - start
                if delta.total_seconds() != 0:
                    print(json.dumps({
                        "id": cur_id,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                        "content": category_to_string(c),
                        "group": c[0],
                    }), ",", sep='')
                    print(current[0]['time'], end - start, current[1])
                    add_time(c, start, end, delta)
                    cur_id += 1

            if x['activity'] == 'unfocus':
                current = None
            else:
                current = (x, c)
        elif x['activity'] == 'focus':
            current = (x, c)
# print('];')
print()

# print('taskNames = [')
# results = sorted(list(totals.items()), key=lambda x: x[1].total_seconds(), reverse=True)
# for (k, v) in results:
#     print(json.dumps(k), ",", sep='')
#     # print(v, k)
# print('];')

def print_totals(totals):
    results = sorted(list(totals.items()), key=lambda x: x[1].total_seconds(), reverse=True)
    # results = sorted(list(totals.items()), key=lambda x: x[0])
    for (k, v) in results:
        print(v, k)

print_totals(totals)

for (day, totals) in sorted(list(by_day.items()), key=lambda x: x[0]):
    print()
    print('Totals for', day.isoformat())
    print_totals(totals)
