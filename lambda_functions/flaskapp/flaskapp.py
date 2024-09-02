import json
from flask import Flask, request, render_template
from flask_lambda import FlaskLambda
import requests
from bs4 import BeautifulSoup
from collections import Counter,OrderedDict,defaultdict
import os
import glob
import json
import re
import time
from datetime import datetime
from pytz import timezone, utc

app = FlaskLambda(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('master.html')
    
@app.route('/go')
def go():
    query = request.args.get('query', '')
    my_word_list = query.lower().split(' ')
    my_word_list = sorted(list(set([word.lower() for word in my_word_list])))
    word_match_list, summary_string, puzzle, my_words_by_length = get_nytbee_word_list(my_word_list)
    return render_template(
        'go.html',
        query=word_match_list,
        summary=summary_string,
        puzzle=puzzle,
        my_words_by_length=my_words_by_length
    )

# @app.route('/')
# def index():
#     pst_time = get_pst_time()
#     data = {
#         'pst_time': pst_time,
#     }
#     return render_template('go.html', data=data)

def get_pst_time():
    date_format='%Y-%m-%d'
    date = datetime.now(tz=utc)
    date = date.astimezone(timezone('US/Pacific'))
    pstDateTime=date.strftime(date_format)
    return pstDateTime

def word_point(word,center_tile,puzz_tiles):
    w = word.lower()
    if center_tile not in w:
        return(0)
    elif len(w)<4:
        return(0)
    elif set(w) != set(puzz_tiles).intersection(set(w)):
        return(0)
    elif set(w) == set(puzz_tiles):
        return(len(w)+7)
    else:
        if len(w) == 4:
            return(1)
        else:
            return(len(w))

def alphagram(word):
    return(''.join(sorted(list(set(word.lower())))))

def my_words_to_dict_list_by_length(words):
    just_a_dict = {}
    for word in words:
        l = len(word)
        if l in just_a_dict.keys():
            just_a_dict[l].append(word)
        else:
            just_a_dict[l] = [word]
    my_words_by_length = []
    for k,wordlist in sorted(just_a_dict.items()):
        d = {'k':k,'words':' '.join(sorted(wordlist))}
        my_words_by_length.append(d)
    return(my_words_by_length)

def get_nytbee_word_list(words):
#+++++++++++++
    todays_date = get_pst_time()
    todays_solution_file = f'./todays_solution_{todays_date}.txt'
    # initialize outputs in case of errors we return something
    output_dicts = []
    summary_string = ''
    center_tile = ''
    puzz_tiles = []
    puzzle = ''
    my_words_by_length = []

    url = 'https://nytbee.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    nytbee_solution_date = ', '.join(soup.find("div", { "id" : "date-and-pic" }).find('h2').text.split(', ')[1:])
    nytbee_solution_date = datetime.strptime(nytbee_solution_date, '%B %d, %Y').strftime('%Y-%m-%d')

    if (not todays_date==nytbee_solution_date):
        summary_string = f'The solution is not yet posted: today: {todays_date} nytbee: {nytbee_solution_date}'
        return(output_dicts,summary_string,puzzle,my_words_by_length)

    x = soup.find('script', type='text/javascript')

    regex = 'var docs_json = \'(.+?)\';'
    y = json.loads(re.findall(regex,str(x))[0])
    keys = [k for k in y.keys()]
    key = keys[0]

    for item in y[key]['roots']['references']:
        if ('data' in item['attributes'].keys()):
            todays_lists = item['attributes']['data']['words']
    nytbee = {}
    all_words = []
    for list_nletters in todays_lists:
        if len(list_nletters)>0:
            nletters = len(list_nletters[0])
            nwords   = len(list_nletters)
            for word in list_nletters:
                all_words.append(word.strip())
            nytbee[nletters]=nwords

    x1 = soup.find_all('script', type='text/javascript')[7]
    regex = 'var docs_json = \'(.+?)\';'
    y1 = json.loads(re.findall(regex,str(x1))[0])
    key = [k for k in y1.keys()][0]
    for item in y1[key]['roots']['references']:
        if 'data' in item['attributes'].keys():
            center_tile = (chr(item['attributes']['data']['color'].index('firebrick')+ord('a')))

    x2 = soup.find_all('script', type='text/javascript')[8]
    y2 = json.loads(re.findall(regex,str(x2))[0])
    key = [k for k in y2.keys()][0]
    for item in y2[key]['roots']['references']:
        if 'data' in item['attributes'].keys():
            colors = item['attributes']['data']['color']
            puzz_tiles = [chr(idx+ord('a')) for idx,color in enumerate(colors) if color=='firebrick']
            # center_tile = (chr(item['attributes']['data']['color'].index('firebrick')+ord('a')))
    puzz_tiles.remove(center_tile)
    puzz_tiles.sort()
    puzz_tiles.insert(0,center_tile)
    
    puzz_tiles2 = list(set(''.join(all_words))-set(center_tile))
    puzz_tiles2.sort()
    puzz_tiles2.insert(0,center_tile)
    if (puzz_tiles!=puzz_tiles2):
        summary_string = f'Error finding puzzle tiles {puzz_tiles} {puzz_tiles2}'
        return(output_dicts,summary_string,puzzle,my_words_by_length)
    # write out to today's file after deleting any old solution files
    for f in glob.glob('todays_solution_*.txt'):
        os.remove(f)

    invalid_words = [word for word in words if word not in all_words] # NUBO
    words = [word for word in words if word in all_words] # NUBO
    # if (len(invalid_words)>0): # NUBO
    #     print(f'Your words list includes words not in the solution:{invalid_words}') # NUBO


    # Here is where you need to do scores for the words
    word_lengths = [len(item) for item in words]
    length_counter = OrderedDict(sorted(Counter(word_lengths).items()))

    word_pts = [(len(item),word_point(item,center_tile,puzz_tiles)) for item in words]
    nytbee_pts = [(len(item),word_point(item,center_tile,puzz_tiles)) for item in all_words]

    word_pt_sum = defaultdict(int)
    for item in word_pts:
        word_pt_sum[item[0]] += item[1]

    nytbee_pt_sum = defaultdict(int)
    for item in nytbee_pts:
        nytbee_pt_sum[item[0]] += item[1]

    n_found = 0
    n_total = 0
    points_needed = 0
    points_found = sum([v for k,v in word_pt_sum.items()])
    points_total = sum([v for k,v in nytbee_pt_sum.items()])
    points_needed = points_total - points_found
    output_dicts = []
    for k,v in sorted(nytbee.items()):
        n_total += v
        if k in length_counter.keys():
            n_found += length_counter[k]
            if length_counter[k]!=v:
                d = {'k':str(k),'wdavail':v,'wdfound':length_counter[k],'wdneeded':v-length_counter[k],\
                    'ptavail':nytbee_pt_sum[k],'ptfound':word_pt_sum[k],'ptneeded':nytbee_pt_sum[k]-word_pt_sum[k]}
                output_dicts.append(d)
        else:
            d = {'k':str(k),'wdavail':v,'wdfound':0,'wdneeded':v,\
                'ptavail':nytbee_pt_sum[k],'ptfound':0,'ptneeded':nytbee_pt_sum[k]}
            output_dicts.append(d)
    d = {'k':'all','wdavail':n_total,'wdfound':n_found,'wdneeded':n_total-n_found,\
                'ptavail':points_total,'ptfound':points_found,'ptneeded':points_needed}
    output_dicts.append(d)
#        summary_string = f'total words {n_total}; found words {n_found}; words needed {n_total-n_found}; pointsavail {points_total}; pointsfound {points_found}; points needed {points_needed}'
    if (len(invalid_words))>0:
        summary_string += 'Warning invalid words: ' + ','.join(invalid_words)
    puzzle = {'center_tile':center_tile.upper(),'petal_tiles':''.join(sorted(list(set(puzz_tiles) - set(center_tile))))}
    my_words_by_length = my_words_to_dict_list_by_length(words)
    return(output_dicts,summary_string,puzzle,my_words_by_length)


# def lambda_handler(event, context):
#     word_list = event['word_list']
#     return_dict = get_nytbee_word_list(word_list)
#     print(return_dict)
#     with app.test_request_context('/'):
#         response = index()
#         return {
#             'statusCode': 200,
#             'body': response.get_data(as_text=True),
#             'headers': {'Content-Type': 'text/html'}
#         }

def lambda_handler(event, context):
    # Extract the word list from the payload
    payload = json.loads(event['body'])
    word_list = payload.get('word_list', [])


    # Process the word list
    my_word_list = [word.lower() for word in word_list]
    my_word_list = sorted(list(set([word.lower() for word in my_word_list])))
    word_match_list, summary_string, puzzle, my_words_by_length = get_nytbee_word_list(my_word_list)

    print(my_words_by_length)
    # Ensure the Flask application context is pushed
    with app.app_context():
        # Render the template
        rendered_html = render_template(
            'go.html',
            query=word_match_list,
            summary=summary_string,
            puzzle=puzzle,
            my_words_by_length=my_words_by_length
        )


    # Return the response
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html'
        },
        'body': rendered_html
    }

    
if __name__ == "__main__":
    app.run(debug=True)