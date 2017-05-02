from datetime import datetime
import flask
from flask import Blueprint, render_template, request, jsonify, g
import simplejson as json

from .util import smart_repr


bp = Blueprint('views', __name__)


@bp.route('/')
def index():
    return flask.redirect('/dashboard/')


@bp.route('/dashboard/')
def dashboard():
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
