from datetime import datetime
import flask
from flask import Blueprint, render_template, request, jsonify, g, url_for
import logging
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
    events = list(g.model.c_events.find(limit=100, sort=[('_id', -1)]))
    return render_template('index.html',
        events=[event_template_data(ev) for ev in events])


def event_template_data(event):
    from jinja2 import Markup, escape
    *log_parts, log_filename = event['log_path'].split('/')
    log_dir = Markup('/<wbr>'.join(escape(p) for p in log_parts))
    return {
        'host': event['host'],
        'date': event['date'].strftime('%Y-%m-%d %H:%M:%S'),
        'date_date': event['date'].strftime('%Y-%m-%d'),
        'date_time': event['date'].strftime('%H:%M:%S'),
        'message': event['chunk'].rstrip(),
        'log_dir': log_dir,
        'log_filename': log_filename,
    }


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
