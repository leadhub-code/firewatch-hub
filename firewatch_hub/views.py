from datetime import datetime, timedelta
import flask
from flask import Blueprint, render_template, request, jsonify, g, url_for
from jinja2 import Markup, escape
import logging
import os
import re
import simplejson as json

from .util import smart_repr


logger = logging.getLogger(__name__)


bp = Blueprint('views', __name__)


@bp.route('/')
def index():
    if flask.session.get('logged_in_user'):
        return flask.redirect('/dashboard/')
    else:
        return flask.redirect('/login/')


@bp.route('/logout')
def logout():
    flask.session['logged_in_user'] = None
    return flask.redirect('/')


@bp.route('/login/')
def login():
    google_login_url = None
    if g.conf.login.oauth2_google:
        google_login_url = url_for('.login_via_google')
    return render_template('login.html',
        google_login_url=google_login_url)


@bp.route('/login/via-google')
def login_via_google():
    flask.session['logged_in_user'] = None
    google = get_google_oauth2_session()
    authorization_url, state = google.authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth")
    flask.session['google_oauth2_state'] = state
    return flask.redirect(authorization_url)


def get_google_oauth2_session():
    from requests_oauthlib import OAuth2Session
    google = OAuth2Session(
        g.conf.login.oauth2_google.client_id,
        scope=["https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri=g.conf.login.oauth2_google.redirect_uri,
        state=flask.session.get('google_oauth2_state'))
    return google


@bp.route('/login/google/callback')
def login_google_callback():
    # Fetch the access token
    token_url = "https://www.googleapis.com/oauth2/v4/token"
    google = get_google_oauth2_session()
    try:
        token = google.fetch_token(token_url,
            client_secret=g.conf.login.oauth2_google.client_secret,
            authorization_response=flask.request.url)
        r = google.get('https://www.googleapis.com/oauth2/v1/userinfo')
        r.raise_for_status()
        rj = r.json()
        logger.debug('userinfo: %r', rj)
        if not rj.get('email'):
            raise Exception('No email received from userinfo')
        if not rj.get('verified_email'):
            raise Exception('E-mail {!r} is not verified'.format(rj['email']))
        user = {
            'email': rj['email'],
            'google_id': rj['id'],
            'google_token': token,
        }
    except Exception as e:
        logger.exception('Failed to fetch token or userinfo: %r', e)
        flask.flash('Error in Google auth callback: [{}] {}'.format(
            e.__class__.__name__, e))
        return flask.redirect('/login/')
    ok = False
    if user['email'] in g.conf.login.allowed_emails:
        ok = True
    flask.session.pop('google_oauth2_state', None)
    if ok:
        flask.session['logged_in_user'] = user
        return flask.redirect('/dashboard/')
    else:
        flask.flash('Access not yet allowed for {}'.format(user['email']))
        return flask.redirect('/login/')


@bp.route('/dashboard/')
def dashboard():
    if not flask.session.get('logged_in_user'):
        return flask.redirect('/login/')
    events = g.model.get_latest_events()
    hour_events, today_events, rest_events = split_events_htr(events)
    hour_groups = group_events(hour_events)
    today_groups = group_events(today_events)
    rest_groups = group_events(rest_events)
    return render_template('dashboard.html',
        mobile=is_mobile(),
        last_hour_groups=[group_template_data(ev) for ev in hour_groups],
        today_groups=[group_template_data(ev) for ev in today_groups],
        rest_groups=[group_template_data(ev) for ev in rest_groups])


# temporarily hardcoded; would be transformed into web admin
group_regexes = [
    re.compile(r'Message .* was already sent in campaign'),
    re.compile(r"Call failed: Exception\('Invalid type: None',\); metadata: .*getCampaigns"),
    re.compile(r"ERROR: Exception: TypeError\(.can't serialize datetime.datetime"),
    re.compile(r"ERROR: Call failed: Exception\('Invalid type: None',\); "),
    re.compile(r"ERROR: Exception: DeserializeError\(.Failed to deserialize b'\\+xc2': first byte 194 not recognized.,\)"),
    re.compile(r"got an unexpected keyword argument 'system'"),
    re.compile(r"ERROR: Call failed: AssertionError\(\); .*getAccount"),
]


def group_events(events):
    by_group = {gre: [] for gre in group_regexes}
    by_group[None] = []
    for event in events:
        matching_gre = None
        for gre in group_regexes:
            if gre.search(event['chunk']):
                matching_gre = gre
                break
        by_group[matching_gre].append(event)
    groups = [
        {
            'pattern': gre.pattern if gre else None,
            'events': matched_events,
        }
        for gre, matched_events in by_group.items()
        if matched_events]
    groups.sort(key=lambda g: g['pattern'] or '')
    groups.sort(key=lambda g: g['pattern'] is None)
    # but maybe it should be in the same order as group_regexes...
    return groups


def split_events_htr(events, now=None):
    '''
    htr = hour/today/rest ;)
    '''
    hour_events = []
    today_events = []
    rest_events = []
    now = now or datetime.utcnow()
    now_1h = now - timedelta(hours=1)
    today = min(now - timedelta(hours=3), datetime(now.year, now.month, now.day))
    for event in events:
        if event['date'] > now_1h:
            hour_events.append(event)
        elif event['date'] > today:
            today_events.append(event)
        else:
            rest_events.append(event)
    return (hour_events, today_events, rest_events)


def is_mobile():
    return request.user_agent.platform in ['iphone', 'android']


def group_template_data(group):
    if group['pattern']:
        events = group['events'][:3]
    else:
        events = group['events'][:100]
    return {
        'pattern': group['pattern'],
        'events': [event_template_data(ev) for ev in events],
        'event_count': len(group['events']),
    }


def event_template_data(event):
    *log_parts, log_filename = event['log_path'].split('/')
    log_dir = Markup('/<wbr>'.join(escape(p) for p in log_parts))
    return {
        'host': event['host'],
        'nice_date': nice_date(event['date']),
        'message': event['chunk'].rstrip(),
        'log_dir': log_dir,
        'log_filename': log_filename,
    }


def nice_date(dt, now=None):
    assert isinstance(dt, datetime)
    if now is None:
        now = datetime.utcnow()
    if dt < now:
        diff = now - dt
        diff_s = int(diff.total_seconds())
        pretty = None
        if diff_s < 60:
            pretty = '{s} s ago'.format(s=diff_s)
        elif diff_s < 3600:
            pretty = '{m} min<br>ago'.format(m=diff_s // 60)
        elif diff_s < 6 * 3600:
            pretty  ='{h} h {m} min ago'.format(
                h=diff_s // 3600, m=(diff_s % 3600) // 60)
        if pretty:
            return Markup('<span title="{full}">{pretty}</span>'.format(
                pretty=pretty,
                full=dt.strftime('%Y-%m-%d %H:%M:%S')))
    return Markup('<small>{date}</small><br>{time}'.format(
        date=dt.strftime('%Y-%m-%d'),
        time=dt.strftime('%H:%M:%S')))


@bp.route('/firewatch-hub/report', methods=['POST'])
def report():
    now = datetime.utcnow()
    data = json.loads(request.data)
    if flask.current_app.debug:
        print('Request data:', smart_repr(data))
    report = data['firewatch_report']
    g.model.update_agent_last_seen(report['agent_id'], now)
    if report.get('events'):
        g.model.insert_events(
            host=report['host'],
            agent_id=report['agent_id'],
            events=report['events'])
    return jsonify({'ok': True})


@bp.route('/_info')
def debug_info():
    if not os.environ.get('DEBUG_INFO'):
        flask.abort(403)
    return jsonify({
        'request': {
            'url': request.url,
            'remote_addr': request.remote_addr,
            'headers': list(request.headers.items()),
        },
    })
