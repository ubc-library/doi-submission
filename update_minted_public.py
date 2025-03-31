######################################################################################
##   This script uses the DataCite MDS API to submit DOIs. See DataCite
##   documentations at https://support.datacite.org/reference/mds
##
##   Metadata is put into a DataCite XML file for submission based on DataCite
##   metadata schema. See metadata schema documentations at
##   https://schema.datacite.org/meta/kernel-4.6/
######################################################################################

#### Usage:  python3 update_minted_public.py

import urllib.request, urllib.error, urllib.parse
import argparse
import json
import configparser
import os
import time
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from datetime import date
import httplib2, sys, base64
import codecs
import html
import language
import importlib

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

importlib.reload(sys)
#remove this line as this is set by default in python3 sys.setdefaultencoding("utf-8")

datacite_api = "https://mds.datacite.org"

base_resolve_url = '<<this variable is used in the submit function, but implement your own logic for constructing the URL that the DOI will resolve to>>'
list_path = "./output/list-%s.list" %date.today()
language_codes = {}

config = configparser.ConfigParser()
config.read('./config/config.ini')


#argCheck sets arguments into variables
def argCheck():
    parser = argparse.ArgumentParser(description='description!')
    parser.add_argument('--printtime', metavar='P', type=str, nargs='?', required=False, default="empty",
                        help='specify the project name')

    args = parser.parse_args()
    printtime = args.printtime

    if (printtime == 'empty'):
        printtime = False
    else:
        printtime = True

    if printtime is False:
        print('--printtime: No time printing with submissions.')
    else:
        print('--printtime: Print time with submissions.')

    return printtime

def get_items():
    with open('./example_files/items.json') as file:
        data = json.load(file)

    return data

# get the metadata for a specified collection item
def get_metadata(cid, doi):
    path = './example_files/item_info_%s_%s.json' % (cid, doi.replace('.', '_'))
    with open(path) as file:
        data = json.load(file)

    return data

def write_on_file(file_name, file_content):
    f = codecs.open(file_name, 'w', 'utf-8')
    f.write(file_content)
    f.close()

# Map OC item language to DataCite Language code
def get_language_code(languages):
    for lan in languages:
        ll = lan['value'].split(';')
        for l in ll:
            code = language.get(l.strip(), map=language_codes)
            if code == None:
                print('WARNING: No language code for %s at collections/%s/items/%s' % (l.strip(), collection, doi))
            return code

# Map OC resource type to DataCite Schema ResourceType
def get_resourceTypeGeneral(resourceType):
    resourceTypeGeneral = '(:null)'
    resourceType = resourceType.lower()
    if resourceType == 'MovingImage'.lower():
        resourceTypeGeneral = 'Audiovisual'
    elif resourceType == 'Collection'.lower():
        resourceTypeGeneral = 'Collection'
    elif resourceType == 'Dataset'.lower():
        resourceTypeGeneral = 'Dataset'
    elif resourceType == 'Event'.lower():
        resourceTypeGeneral = 'Event'
    elif resourceType == 'Image'.lower() or resourceType == 'StillImage'.lower():
        resourceTypeGeneral = 'Image'
    elif resourceType == 'InteractiveResource'.lower():
        resourceTypeGeneral = 'InteractiveResource'
    # if resourceType == 'N/A'.lower():
    #     resourceTypeGeneral = 'Model'
    elif resourceType == 'PhysicalObject'.lower():
        resourceTypeGeneral = 'PhysicalObject'
    elif resourceType == 'Service'.lower():
        resourceTypeGeneral = 'Service'
    elif resourceType == 'Software'.lower():
        resourceTypeGeneral = 'Software'
    elif resourceType == 'Sound'.lower():
        resourceTypeGeneral = 'Sound'
    elif resourceType == 'Text'.lower():
        resourceTypeGeneral = 'Text'
    # if resourceType == 'N/A'.lower():
    #     resourceTypeGeneral = 'Workflow'
    else:
        resourceTypeGeneral = 'Other'

    return resourceTypeGeneral

# take OC API output to generate data in XML format
def generate_xml(data):
    comment = '<?xml version="1.0" encoding="UTF-8"?>'
    xml = Element('resource')
    xml.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    xml.set('xmlns', 'http://datacite.org/schema/kernel-4')
    xml.set('xsi:schemaLocation',
            'http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4/metadata.xsd')

    data_all = data['data']['_source']
    data = data['data']['_source']['metadata']

    # identifier
    identifier = SubElement(xml, 'identifier')
    identifier.text = data['IsShownAt'][0]['value']
    identifier.set('identifierType', 'DOI')

    # <creators>
    creators = SubElement(xml, 'creators')
    if 'Creator' in list(data.keys()) and data['Creator'] is not None:
        for entry in data['Creator']:
            creator = SubElement(creators, 'creator')
            creatorName = SubElement(creator, 'creatorName')
            creatorName.text = html.escape(entry['value'], quote=True)
    else:
        creator = SubElement(creators, 'creator')
        creatorName = SubElement(creator, 'creatorName')
        creatorName.text = '(:null)'

    # <titles>
    titles = SubElement(xml, 'titles')
    if 'Title' in list(data.keys()) and data['Title'] is not None:
        for entry in data['Title']:
            title = SubElement(titles, 'title')
            title.text = html.escape(entry['value'], quote=True)
    else:
        title = SubElement(titles, 'title')
        title.text = '(:null)'

    # <publisher>
    if 'Publisher' in list(data.keys()) and data['Publisher'] is not None:
        publisher = SubElement(xml, 'publisher')
        publisher.text = html.escape(data['Publisher'][0]['value'], quote=True)
    else:
        publisher = SubElement(xml, 'publisher')
        publisher.text = config.get('all', 'default_publisher_name')

    # <publicationYear>
    dateIsSet = False
    # print 'Searching for DateAvailable Property\n'
    if 'DateAvailable' in list(data.keys()) and data['DateAvailable'] is not None:
        for entry in data['DateAvailable']:
            year = entry['value'].split('-')[0]
            publicationYear = SubElement(xml, 'publicationYear')
            publicationYear.text = year
            dateIsSet = True
            break
    if not dateIsSet:
        publicationYear = SubElement(xml, 'publicationYear')
        publicationYear.text = '(:null)'

    # if dateIsSet == False:
    #     if 'dateAvailable' in data_all.keys() and data_all['dateAvailable'] is not None:
    #         year = data_all['dateAvailable'].split('-')[0]
    #         publicationYear.text = year

    # <resourceType>
    resourceType = SubElement(xml, 'resourceType')
    if 'Type' in list(data.keys()) and data['Type'] is not None:
        resourceType.text = data['Type'][0]['value'].replace(' ', '')
        resourceType.set('resourceTypeGeneral', get_resourceTypeGeneral(resourceType.text))
    # elif 'type' in data_all.keys() and data_all['type'] is not None:
    #     resourceType.text = data_all['type'][0].replace(' ', '')
    #     resourceType.set('resourceTypeGeneral', get_resourceTypeGeneral(resourceType.text))
    else:
        resourceType.text = '(:null)'
        resourceType.set('resourceTypeGeneral', '(:null)')

    # <language>
    if 'Language' in list(data.keys()) and data['Language'] is not None:
        lan_code = get_language_code(data['Language'])
        if lan_code is not None:
            language = SubElement(xml, 'language')
            language.text = lan_code
    # $language = $xml->addChild('language',$data['Language'][0]['value']);
    # //        We don't want the resourceType for a while
    #         <resourceType>
    # //        $resourceType = $xml->addChild ('resourceType', $resourceTypeLabel);
    # //        $resourceType->addAttribute ('resourceTypeGeneral', $resourceTypeGeneralLabel);

    # <version>
    version = SubElement(xml, 'version')
    version.text = '1'

    # <descriptions>
    descriptions = SubElement(xml, 'descriptions')
    desc = ''
    if 'Description' in list(data.keys()) and data['Description'] is not None:
        desc = data['Description'][0]['value'].replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    description = SubElement(descriptions, 'description')
    description.text = html.escape(desc)
    description.set('descriptionType', 'Abstract')

    # <contributors (ROR)>
    contributors = SubElement(xml, 'contributors')
    contributor = SubElement(contributors, 'contributor')
    contributor.set('contributorType', 'HostingInstitution')
    contributorName = SubElement(contributor, 'contributorName')
    contributorName.text = config.get('all', 'hosting_institution_contributor_name')
    nameIdentifier = SubElement(contributor, 'nameIdentifier')
    nameIdentifier.set('nameIdentifierScheme', 'ROR')
    nameIdentifier.set('schemeURI', 'https://ror.org/')
    nameIdentifier.text = config.get('all', 'hosting_institution_ror_id')

    # <relatedIdentifiers>
    if 'PublisherDOI' in list(data.keys()) and data['PublisherDOI'] is not None:
        relatedIdentifiers = SubElement(xml, 'relatedIdentifiers')
        for entry in data['PublisherDOI']:
            relatedIdentifier = SubElement(relatedIdentifiers, 'relatedIdentifier')
            relatedIdentifier.set('relatedIdentifierType', 'DOI')
            relatedIdentifier.set('relationType', 'IsIdenticalTo')
            relatedIdentifier.text = entry['value']

    return comment + tostring(xml, 'unicode')

# function for posting to DataCite MDS API.
def post_to_mds(cmd, file, fileType):
    endpoint = '%s/%s' %(datacite_api, cmd)

    body_unicode = codecs.open(file, 'r', encoding='utf-8').read().strip()

    h = httplib2.Http()
    auth_string = base64.encodebytes(('%s:%s' %(datacite_user,datacite_pass)).encode()).decode()
    response, content = h.request(endpoint,
                                  'POST',
                                  body=body_unicode.encode('utf-8'),
                                  headers={'Content-Type': '%s;charset=UTF-8' %fileType,

                                           'Authorization': 'Basic ' + auth_string})
    return response, content

def submit(cid, doi):
    print_time_with_str('Get Metadata')

    metadata = get_metadata(cid, doi)

    success = False
    if metadata is None:
        write_on_file("./FAILED_DOI/NOT_FOUND_%s_%s.xml" %(cid, doi), "NONE")
        return

    full_doi = config.get('all', 'doi_prefix') + '/' + doi

    # Determine the correct resolve URL
    data = "doi=%s\nurl=%s/%s" %(full_doi, base_resolve_url, doi)
    write_on_file('./output/%s.txt' %doi, data)
    data = generate_xml(metadata)
    write_on_file('./output/%s.xml' %doi, data)

    try:
        # Post Metadata to DataCite
        print_time_with_str('Post to MDS Metadata')
        response, content = post_to_mds('metadata', './output/%s.xml' %doi, 'application/xml')
        if response.status != 201:
            print(' METADATA_FAILED - SEE OUTPUT - ./FAILED_DOI/FAILED_METADATA_SUBMIT_%s_%s.xml \n' % (cid, doi))
            write_on_file("./FAILED_DOI/FAILED_METADATA_SUBMIT_%s_%s.xml" % (cid, doi), data)
        else:

            # if metadata post was successful, post DOI to MDS API in order to resolve
            # https://dx.doi.org/10.14288/1.0445424 to our own item URL
            print_time_with_str('Post to MDS DOI')
            response, content= post_to_mds('doi', './output/%s.txt' %doi, 'text/plain')
            if response.status != 201:
                write_on_file("./FAILED_DOI/FAILED_DOI_SUBMIT_%s_%s.xml" % (cid, doi), data)
            else:
                print('submitted %s-%s' % (collection, doi))
                print_time_with_str()
                success = True
    except:
        write_on_file("./FAILED_DOI/FAILED_DOI_SUBMIT_%s_%s.xml" % (cid, doi), data)
    os.remove('./output/%s.xml' %doi)
    os.remove('./output/%s.txt' %doi)
    return success

def print_time_with_str(pre_str='', suf_str=''):
    time_now = time.time()
    if printtime:
        print ("%s %.2f %s" % (pre_str, time_now, suf_str))

if __name__ == "__main__":
    global printtime
    printtime = argCheck()
    time.sleep(3.0)
    language_codes = language.init()
    fff = open(list_path, 'a+')
    print_time_with_str('Submissions start')

    try:
        datacite_user=config.get('all', 'doi_username')
        datacite_pass=config.get('all', 'doi_password')
    except:
        print("Failed to get Datacite credentials")

    items = get_items()
    for item in items:
        doi = item['_id']
        collection = item['collection']

        # submit DOI
        success = submit(collection, doi)
        if not success:
            fff.write('FAILED_METADATA_SUBMIT_%s_%s.xml\n' % (collection, doi))

    sys.stdout.flush()

    fff.close()
