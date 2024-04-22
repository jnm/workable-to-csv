import csv
import datetime
import math
import os
import requests
import time
from zoneinfo import ZoneInfo

# Get a token from https://www.workable.com/backend/account/integrations
WORKABLE_API_TOKEN = os.environ['WORKABLE_API_TOKEN']
OUTPUT_FILENAME = 'candidates.csv'
DESIRED_CANDIDATE_ATTRIBUTES = {
    # each key is the attribute name
    # each value is a callable whose return value is used to `update()` the
    # dictionary for the candidate
    'id': lambda x: {'id': x},
    'answers': lambda answers: {
        x['question']['body']: next(iter(x['answer'].values())) for x in answers
    },
    'profile_url': lambda x: {'profile_url': x},
}

WORKABLE_TIMESTAMP_TIME_ZONE = ZoneInfo('America/New_York')  # WTF, mate?
HEADERS = {'Authorization': f'Bearer {WORKABLE_API_TOKEN}'}
JOBS_URL = 'https://kobotoolbox.workable.com/spi/v3/jobs'
LIST_URL_TEMPLATE = (
    'https://kobotoolbox.workable.com/spi/v3/candidates?shortcode={shortcode}'
)
DETAIL_URL_TEMPLATE = 'https://kobotoolbox.workable.com/spi/v3/candidates/{id}'


def w_req(method, *args, **kwargs):
    """
    Workable API has rate limiting but returns a header specifying when to try
    again
    """

    m = getattr(requests, method)
    kwargs['headers'] = HEADERS
    response = m(*args, **kwargs)
    if response.status_code != 429:
        return response
    now = datetime.datetime.now(WORKABLE_TIMESTAMP_TIME_ZONE)
    next_allowed = datetime.datetime.fromtimestamp(
        int(response.headers['x-rate-limit-reset']),
        WORKABLE_TIMESTAMP_TIME_ZONE,
    )
    wait = max(0, math.ceil((next_allowed - now).seconds))
    print('Rate limited; waiting for', wait, 'seconds…')
    time.sleep(wait)
    return w_req(method, *args, **kwargs)


def prompt_for_job():
    jobs = w_req('get', JOBS_URL).json()['jobs']
    for idx, job in enumerate(jobs):
        print(f'{idx}: {job["title"]}')

    job_idx = int(input('Which job? '))
    return jobs[job_idx]['shortcode']


def get_candidates_for_job(shortcode):
    candidate_ids = []
    url = LIST_URL_TEMPLATE.format(shortcode=shortcode)
    while True:
        response = w_req('get', url).json()
        for c in response['candidates']:
            candidate_ids.append(c['id'])
        try:
            url = response['paging']['next']
        except KeyError:
            break
    print('Retrieved', len(candidate_ids), 'candidates')
    return candidate_ids


def get_candidate_details(candidate_id, desired_attributes):
    url = DETAIL_URL_TEMPLATE.format(id=candidate_id)
    response = w_req('get', url).json()
    candidate = {}
    for attribute, processor in DESIRED_CANDIDATE_ATTRIBUTES.items():
        candidate.update(processor(response['candidate'][attribute]))
    return candidate


job_shortcode = prompt_for_job()
candidate_ids = get_candidates_for_job(job_shortcode)
candidates = []

print('Loading candidate details (slow)', end='', flush=True)
headers = set()
for candidate_id in candidate_ids:
    c = get_candidate_details(candidate_id, DESIRED_CANDIDATE_ATTRIBUTES)
    headers.update(c.keys())
    candidates.append(c)
    print('.', end='', flush=True)

with open(OUTPUT_FILENAME, 'w') as f:
    dw = csv.DictWriter(f, headers)
    dw.writeheader()
    dw.writerows(candidates)

print('Finished writing to', OUTPUT_FILENAME)
