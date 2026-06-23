from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'projectproof_secret_2024'

USERS = {
    'macseogoon': {
        'password': 'macseogoon',
        'role': 'teacher',
        'display': 'Teacher'
    },
    'kenneth': {
        'password': 'kenneth',
        'role': 'leader',
        'display': 'Kenneth',
        'group': 'Group Alpha'
    },
    'peter': {
        'password': 'peter',
        'role': 'leader',
        'display': 'Peter',
        'group': 'Group Beta'
    },
    'zarneth': {
        'password': 'zarneth',
        'role': 'member',
        'display': 'Zarneth',
        'group': 'Group Alpha'
    },
    'thirdy': {
        'password': 'thirdy',
        'role': 'member',
        'display': 'Thirdy',
        'group': 'Group Alpha'
    },
    'michael': {
        'password': 'michael',
        'role': 'member',
        'display': 'Michael',
        'group': 'Group Alpha'
    },
    'meg': {
        'password': 'meg',
        'role': 'member',
        'display': 'Meg',
        'group': 'Group Beta'
    },
    'lois': {
        'password': 'lois',
        'role': 'member',
        'display': 'Lois',
        'group': 'Group Beta'
    },
    'tba': {
        'password': 'tba',
        'role': 'member',
        'display': 'TBA',
        'group': 'Group Beta'
    },
}

GROUPS = {
    'Group Alpha': ['zarneth', 'thirdy', 'michael'],
    'Group Beta':  ['meg', 'lois', 'tba'],
}

CONTRIBUTIONS = {
    username: {'total': 0, 'logs': [], 'streak': 0, 'last_date': None}
    for username, data in USERS.items()
    if data['role'] == 'member'
}

PROGRESS = {
    'Group Alpha': [],
    'Group Beta':  [],
}


def current_user():
    return USERS.get(session.get('username'))


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            if role and current_user()['role'] != role:
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_group_members(group_name):
    return GROUPS.get(group_name, [])


def get_group_summary(group_name):
    members = get_group_members(group_name)
    summary = []
    for uname in members:
        if uname not in USERS:
            continue
        user = USERS[uname]
        contrib = CONTRIBUTIONS.get(uname, {'total': 0, 'logs': [], 'streak': 0, 'last_date': None})
        summary.append({
            'username': uname,
            'display': user['display'],
            'total': contrib['total'],
            'logs': contrib['logs'],
            'streak': contrib.get('streak', 0),
            'last_date': contrib.get('last_date'),
        })
    return summary


def timestamp_now():
    return datetime.now().strftime('%b %d, %Y · %I:%M %p')


def date_today():
    return datetime.now().strftime('%Y-%m-%d')


def get_all_groups():
    return list(GROUPS.keys())


def get_last_activity(group_name):
    members = GROUPS.get(group_name, [])
    latest = None
    for uname in members:
        contrib = CONTRIBUTIONS.get(uname, {})
        for log in contrib.get('logs', []):
            ts = log.get('raw_ts', 0)
            if latest is None or ts > latest:
                latest = ts
    for p in PROGRESS.get(group_name, []):
        ts = p.get('raw_ts', 0)
        if latest is None or ts > latest:
            latest = ts
    if latest:
        return datetime.fromtimestamp(latest).strftime('%b %d')
    return None


def update_streak(uname):
    contrib = CONTRIBUTIONS.get(uname)
    if not contrib:
        return
    today = date_today()
    if contrib['last_date'] == today:
        return
    contrib['streak'] = contrib.get('streak', 0) + 1
    contrib['last_date'] = today


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = USERS.get(username)
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        error = 'Wrong username or password.'
    return render_template('login.html', error=error)


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    role = current_user()['role']
    if role == 'teacher':
        return redirect(url_for('teacher'))
    elif role == 'leader':
        return redirect(url_for('leader'))
    elif role == 'member':
        return redirect(url_for('member'))
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/teacher')
@login_required(role='teacher')
def teacher():
    user = current_user()
    all_groups = {}
    group_meta = {}
    for group_name in GROUPS:
        all_groups[group_name] = get_group_summary(group_name)
        group_meta[group_name] = {
            'last_activity': get_last_activity(group_name),
            'leader': next(
                (u['display'] for u in USERS.values()
                 if u.get('role') == 'leader' and u.get('group') == group_name),
                '—'
            )
        }

    all_logs = []
    for uname, data in CONTRIBUTIONS.items():
        if uname not in USERS:
            continue
        for log in data['logs']:
            all_logs.append({
                'member': USERS[uname]['display'],
                'group': USERS[uname]['group'],
                **log
            })
    all_logs.sort(key=lambda x: x['raw_ts'], reverse=True)

    all_accounts = []
    for uname, data in USERS.items():
        if data['role'] != 'teacher':
            all_accounts.append({
                'username': uname,
                'display': data['display'],
                'role': data['role'],
                'group': data.get('group', '—'),
            })

    return render_template('teacher.html',
                           user=user,
                           all_groups=all_groups,
                           group_meta=group_meta,
                           all_logs=all_logs,
                           all_accounts=all_accounts,
                           all_group_names=get_all_groups(),
                           progress=PROGRESS)


@app.route('/create-account', methods=['POST'])
@login_required(role='teacher')
def create_account():
    display   = request.form.get('display', '').strip()
    username  = request.form.get('username', '').strip()
    password  = request.form.get('password', '').strip()
    role      = request.form.get('role', '').strip()
    group     = request.form.get('group', '').strip()
    new_group = request.form.get('new_group', '').strip()

    if new_group:
        group = new_group

    if not all([display, username, password, role, group]):
        return redirect(url_for('teacher'))
    if username in USERS:
        return redirect(url_for('teacher'))

    USERS[username] = {
        'password': password,
        'role': role,
        'display': display,
        'group': group,
    }

    if role == 'member':
        CONTRIBUTIONS[username] = {'total': 0, 'logs': [], 'streak': 0, 'last_date': None}
        if group not in GROUPS:
            GROUPS[group] = []
            PROGRESS[group] = []
        if username not in GROUPS[group]:
            GROUPS[group].append(username)

    if role == 'leader':
        if group not in GROUPS:
            GROUPS[group] = []
            PROGRESS[group] = []

    return redirect(url_for('teacher'))


@app.route('/delete-account/<username>', methods=['POST'])
@login_required(role='teacher')
def delete_account(username):
    if username in USERS and USERS[username]['role'] != 'teacher':
        user_data = USERS[username]
        group = user_data.get('group')
        if group and group in GROUPS:
            if username in GROUPS[group]:
                GROUPS[group].remove(username)
        if username in CONTRIBUTIONS:
            del CONTRIBUTIONS[username]
        del USERS[username]
    return redirect(url_for('teacher'))


@app.route('/delete-group/<group_name>', methods=['POST'])
@login_required(role='teacher')
def delete_group(group_name):
    if group_name in GROUPS:
        members = GROUPS[group_name].copy()
        for uname in members:
            if uname in USERS and USERS[uname]['role'] == 'member':
                del USERS[uname]
            if uname in CONTRIBUTIONS:
                del CONTRIBUTIONS[uname]
        leaders_to_remove = [
            uname for uname, data in USERS.items()
            if data.get('role') == 'leader' and data.get('group') == group_name
        ]
        for uname in leaders_to_remove:
            del USERS[uname]
        del GROUPS[group_name]
        if group_name in PROGRESS:
            del PROGRESS[group_name]
    return redirect(url_for('teacher'))


@app.route('/log-progress', methods=['POST'])
@login_required(role='leader')
def log_progress():
    user = current_user()
    group_name = user['group']
    entry = request.form.get('entry', '').strip()
    is_milestone = request.form.get('milestone') == 'on'

    if entry and group_name in PROGRESS:
        PROGRESS[group_name].append({
            'entry': entry,
            'by': user['display'],
            'timestamp': timestamp_now(),
            'raw_ts': datetime.now().timestamp(),
            'milestone': is_milestone,
        })
    return redirect(url_for('leader'))


@app.route('/leader', methods=['GET', 'POST'])
@login_required(role='leader')
def leader():
    user = current_user()
    group_name = user['group']
    members = get_group_summary(group_name)
    progress_logs = PROGRESS.get(group_name, [])
    success = None
    error = None

    if request.method == 'POST':
        member_uname = request.form.get('member')
        points_raw   = request.form.get('points', '0')
        comment      = request.form.get('comment', '').strip()

        if member_uname not in get_group_members(group_name):
            error = 'Invalid member selected.'
        elif not comment:
            error = 'A comment is required.'
        else:
            try:
                points = int(points_raw)
                if not (0 <= points <= 5):
                    raise ValueError
            except ValueError:
                error = 'Points must be 0 to 5.'

        if not error:
            raw_ts = datetime.now().timestamp()
            update_streak(member_uname)
            CONTRIBUTIONS[member_uname]['total'] += points
            CONTRIBUTIONS[member_uname]['logs'].append({
                'points': points,
                'comment': comment,
                'by': user['display'],
                'timestamp': timestamp_now(),
                'raw_ts': raw_ts,
            })
            success = f"+{points} logged for {USERS[member_uname]['display']}."
            members = get_group_summary(group_name)

    return render_template('leader.html',
                           user=user,
                           group_name=group_name,
                           members=members,
                           success=success,
                           error=error,
                           progress_logs=progress_logs)


@app.route('/member')
@login_required(role='member')
def member():
    user     = current_user()
    username = session['username']
    contrib  = CONTRIBUTIONS.get(username, {'total': 0, 'logs': [], 'streak': 0})
    logs     = list(reversed(contrib['logs']))
    group_progress = PROGRESS.get(user.get('group', ''), [])
    return render_template('member.html',
                           user=user,
                           total=contrib['total'],
                           streak=contrib.get('streak', 0),
                           logs=logs,
                           group_progress=group_progress)


if __name__ == '__main__':
    app.run(debug=True)