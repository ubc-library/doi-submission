import codecs

map = {}


def init():
    files = ['doi/lan/languages-3.data', 'doi/lan/languages-2.data', 'doi/lan/languages-3to2.data']
    load_MARC('doi/lan/MARC-Code-List-for-Languages_-Name-Sequence-(Library-of-Congress).html')
    for f in files:
        # print f
        file = codecs.open(f, 'r', 'utf-8')
        for line in file:
            splited = line.split("','")
            code = splited[0].replace("'", '')
            labels = splited[1].replace("'", '').split(';')
            for l in labels:
                map[l.strip().lower()] = code

    return map


def load_MARC(file_name):
    file = codecs.open(file_name, 'r', 'utf-8')
    start = False
    language = ''
    code = ''
    is_collectivename = False
    has_UF = False
    for line in file:
        if '<!-- starts here -->' in line:
            start = True
        if not start:
            continue
        if 'class="authorizedname"' in line:
            language = line.replace('<span class="authorizedname">', '').replace('</span>', '').strip()
        elif 'class="code"' in line:
            code = line.replace('<span class="code">', '').replace('</span>', '').strip()
            code = code.replace('[', '').replace(']', '').strip()
            map[language.lower()] = code
        elif '<div class="collectivename">' in line:
            if '</div>' in line:
                collectivename = line.replace('<div class="collectivename">', '').replace('</div>', '').strip()
                map[collectivename.lower()] = code
            else:
                is_collectivename = True
        elif '<div class="useforref' in line:
            has_UF = True
        elif has_UF:
            if '<span class="uflabel">UF</span>' in line:
                continue
            has_UF = False
            UF = line.replace('</div>', '').replace('&nbsp;', '').strip()
            map[UF.lower()] = code


def get(language, map):
    language = language.strip().lower()
    if language in list(map.keys()):
        return map[language]
    elif len(language) == 3:
            return language
    else:
        return None

