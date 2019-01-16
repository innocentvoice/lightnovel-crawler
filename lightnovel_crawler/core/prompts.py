import re
import os
import sys
import shutil

from PyInquirer import prompt

from .icons import Icons
from .arguments import get_args


def get_novel_url():
    args = get_args()
    if args.query and len(args.query) > 1:
        return args.query
    # end if

    url = args.novel_page
    if url and url.startswith('http'):
        return url
    # end if

    try:
        if args.suppress:
            raise Exception()
        # end if

        answer = prompt([
            {
                'type': 'input',
                'name': 'novel',
                'message': 'Enter novel page url or query novel:',
                'validate': lambda val: 'Input should not be empty'
                if len(val) == 0 else True,
            },
        ])
        return answer['novel'].strip()
    except:
        raise Exception('Novel page url or query was not given')
    # end try
# end def


def get_crawlers_to_search(links):
    args = get_args()
    if not links or len(links) <= 1:
        return links or []
    # end if

    if args.suppress:
        return links
    # end if

    answer = prompt([
        {
            'type': 'checkbox',
            'name': 'sites',
            'message': 'Where to search?',
            'choices': [{'name': x} for x in links],
        }
    ])
    return answer['sites'] if len(answer['sites']) else links
# end def


def choose_a_novel(search_results):
    args = get_args()

    if len(search_results) == 0:
        return ''
    elif len(search_results) == 1:
        return search_results[0][1]
    # end if

    if args.suppress:
        return search_results[0][1]
    # end if

    answer = prompt([
        {
            'type': 'list',
            'name': 'novel_url',
            'message': 'Which one is your novel?',
            'choices': [
                {'name': '%s (%s)' % (x[0], x[1])}
                for x in sorted(search_results)
            ],
        }
    ])
    selected = answer['novel_url']
    selected = re.search('(https?://.*)', selected)
    url = selected.group(1).strip('()')
    return url
# end def


def get_output_path(suggested_path):
    args = get_args()
    output_path = args.output_path

    if args.suppress:
        output_path = output_path or suggested_path or 'Unknown Novel'
    # end if

    if not output_path:
        answer = prompt([
            {
                'type': 'input',
                'name': 'output',
                'message': 'Enter output direcotry:',
                'default': os.path.abspath(suggested_path),
            },
        ])
        output_path = answer['output']
    # end if

    output_path = os.path.abspath(output_path)
    if os.path.exists(output_path):
        if force_replace_old():
            shutil.rmtree(output_path, ignore_errors=True)
        # end if
    # end if
    os.makedirs(output_path, exist_ok=True)

    return output_path
# end def


def force_replace_old():
    args = get_args()

    if args.force:
        return True
    elif args.ignore:
        return False
    # end if

    if args.suppress:
        return False
    # end if

    answer = prompt([
        {
            'type': 'confirm',
            'name': 'force',
            'message': 'Detected existing folder. Replace it?',
            'default': False,
        },
    ])
    return answer['force']
# end def


def login_info():
    args = get_args()

    if args.login:
        return args.login
    # end if

    if args.suppress:
        return False
    # end if

    answer = prompt([
        {
            'type': 'confirm',
            'name': 'login',
            'message': 'Do you want to log in?',
            'default': False
        },
    ])

    if answer['login']:
        answer = prompt([
            {
                'type': 'input',
                'name': 'email',
                'message': 'Email:',
                'validate': lambda val: True if len(val)
                else 'Email address should be not be empty'
            },
            {
                'type': 'password',
                'name': 'password',
                'message': 'Password:',
                'validate': lambda val: True if len(val)
                else 'Password should be not be empty'
            },
        ])
        return answer['email'], answer['password']
    # end if

    return None
# end if


def download_selection(chapter_count, volume_count):
    keys = ['all', 'last', 'first', 'page', 'range', 'volumes', 'chapters']

    args = get_args()
    for key in keys:
        if args.__getattribute__(key):
            return key
        # end if
    # end if

    if args.suppress:
        return keys[0]
    # end if

    big_list_warn = '(warn: very big list)' if chapter_count > 50 else ''

    choices = [
        'Everything! (%d chapters)' % chapter_count,
        'Last 10 chapters',
        'First 10 chapters',
        'Custom range using URL',
        'Custom range using index',
        'Select specific volumes (%d volumes)' % volume_count,
        'Select specific chapters ' + big_list_warn,
    ]
    if chapter_count <= 20:
        choices.pop(1)
        choices.pop(1)
    # end if

    answer = prompt([
        {
            'type': 'list',
            'name': 'choice',
            'message': 'Which chapters to download?',
            'choices': choices,
        },
    ])

    return keys[choices.index(answer['choice'])]
# end def


def range_using_urls(crawler):
    args = get_args()
    start_url, stop_url = args.page or (None, None)

    if args.suppress:
        return (0, len(crawler.chapters) - 1)
    # end if

    if not (start_url and stop_url):
        def validator(val):
            try:
                if crawler.get_chapter_index_of(val) > 0:
                    return True
            except:
                pass
            return 'No such chapter found given the url'
        # end def
        answer = prompt([
            {
                'type': 'input',
                'name': 'start_url',
                'message': 'Enter start url:',
                'validate': validator,
            },
            {
                'type': 'input',
                'name': 'stop_url',
                'message': 'Enter final url:',
                'validate': validator,
            },
        ])
        start_url = answer['start_url']
        stop_url = answer['stop_url']
    # end if

    start = crawler.get_chapter_index_of(start_url) - 1
    stop = crawler.get_chapter_index_of(stop_url) - 1

    return (start, stop) if start < stop else (stop, start)
# end def


def range_using_index(chapter_count):
    args = get_args()
    start, stop = args.range or (None, None)

    if args.suppress:
        return (0, chapter_count - 1)
    # end if

    if not (start and stop):
        def validator(val):
            try:
                if 1 <= int(val) <= chapter_count:
                    return True
            except:
                pass
            return 'Please enter an integer between 1 and %d' % chapter_count
        # end def
        answer = prompt([
            {
                'type': 'input',
                'name': 'start',
                'message': 'Enter start index (1 to %d):' % chapter_count,
                'validate': validator,
                'filter': lambda val: int(val),
            },
            {
                'type': 'input',
                'name': 'stop',
                'message': 'Enter final index (1 to %d):' % chapter_count,
                'validate': validator,
                'filter': lambda val: int(val),
            },
        ])
        start = answer['start'] - 1
        stop = answer['stop'] - 1
    else:
        start = start - 1
        stop = stop - 1
    # end if

    return (start, stop) if start < stop else (stop, start)
# end def


def range_from_volumes(volumes, times=0):
    selected = None
    args = get_args()

    if args.suppress:
        selected = [x['id'] for x in volumes]
    # end if

    if times == 0 and not selected:
        selected = args.volumes
    # end if

    if not selected:
        answer = prompt([
            {
                'type': 'checkbox',
                'name': 'volumes',
                'message': 'Choose volumes to download:',
                'choices': [
                    {
                        'name': '%d - %s [%d chapters]' % (
                            vol['id'], vol['title'], vol['chapter_count'])
                    }
                    for vol in volumes
                ],
                'validate': lambda ans: True if len(ans) > 0
                else 'You must choose at least one volume.'
            }
        ])
        selected = [
            int(val.split(' ')[0])
            for val in answer['volumes']
        ]
    # end if

    if times < 3 and len(selected) == 0:
        return range_from_volumes(volumes, times + 1)
    # end if

    return selected
# end def


def range_from_chapters(crawler, times=0):
    selected = None
    args = get_args()

    if args.suppress:
        selected = crawler.chapters
    # end if

    if times == 0 and not selected:
        selected = get_args().chapters
    # end if

    if not selected:
        answer = prompt([
            {
                'type': 'checkbox',
                'name': 'chapters',
                'message': 'Choose chapters to download:',
                'choices': [
                    {'name': '%d - %s' % (chap['id'], chap['title'])}
                    for chap in crawler.chapters
                ],
                'validate': lambda ans: True if len(ans) > 0
                else 'You must choose at least one chapter.',
            }
        ])
        selected = [
            int(val.split(' ')[0])
            for val in answer['chapters']
        ]
    else:
        selected = [
            crawler.get_chapter_index_of(x)
            for x in selected if x
        ]
    # end if

    if times < 3 and len(selected) == 0:
        return range_from_chapters(crawler, times + 1)
    # end if

    selected = [
        x for x in selected
        if 1 <= x <= len(crawler.chapters)
    ]

    return selected
# end def


def pack_by_volume():
    args = get_args()

    if len(sys.argv) > 1:
        return args.byvol
    # end if

    if args.suppress:
        return False
    # end if

    answer = prompt([
        {
            'type': 'confirm',
            'name': 'volume',
            'message': 'Generate separate files for each volumes?',
            'default': False,
        },
    ])
    return answer['volume']
# end def
