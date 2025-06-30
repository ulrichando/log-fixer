import os
from googleapiclient.discovery import build

google_key = os.getenv('GOOGLE_API_KEY')
google_cx = os.getenv('GOOGLE_CX')
TRUSTED = ['stackoverflow.com', 'serverfault.com', 'askubuntu.com']


def find_error_solution(err):
    if not google_key or not google_cx:
        raise ValueError('Set GOOGLE_API_KEY & GOOGLE_CX')
    svc = build('customsearch', 'v1', developerKey=google_key)
    res = svc.cse().list(q=err, cx=google_cx, num=5).execute()
    items = res.get('items', [])
    top = [i for i in items if any(d in i['link'] for d in TRUSTED)] or items
    return '\n'.join(f"- {it['snippet']} ({it['link']})" for it in top[:3])
