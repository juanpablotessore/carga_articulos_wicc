import sys
import os.path
import pickle
import pandas as pd
import googleapiclient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import robobrowser
import getpass

############################################################
#                                                          #
#       Google Drive authentication and resources          #
#                                                          #
############################################################

SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets.readonly',
          'https://mail.google.com/']

# Carpetas de drive con los archivos de cada workshop WICC 2023
WICC_FOLDERS_DICTIONARY = {
    'ARSO': {'posters': '1efrTNI4z1QtJqbKfVhBvku62kQFBkKC1',
             'audio_video': '1hP7Gih6lgSEUTe9SE4_D9MbUtRkZsYeH'},
    'ASI': {'posters': '1P7aVRWAwyxkhRQD06w9_QvW30Zgv_c7d',
            'audio_video': '13rTgvyhGF74AzmkqchQ4DGLqh-RyNV7f'},
    'BDMD': {'posters': '1sMYHJuJW7-DqNXZLQxBOliYoZMKmo0V3',
             'audio_video': '1UgHyciFhu0uAxRsDQRfCgV4pXlYXz13h'},
    'CGIV': {'posters': '1XikF7n9rr5pkIF5aQXl3L5cxqauIyBIT',
             'audio_video': '1_Ofg_5VqbrMYJ37dHNgtKP7rh3ruxOsr'},
    'IEI': {'posters': '1EnbMHgCVpPIAFzUU28CZ6TBUq-AdjfRl',
            'audio_video': '1-IcCCtXbWHmAolrIi3D3bwQSjXYPSDuj'},
    'IS': {'posters': '1yd6P0aMejVsAZcCa4yh_U02L0rsJo8AK',
           'audio_video': '13hFiaSbaStIr5kzMpvsZ4RTWQMMJ3XB5'},
    'ISS': {'posters': '1g-ETkjTUTa-rXwb1RBvSDi0vvhd--Apc',
            'audio_video': '1ExZzNbcQT4aS75oMji2IQm7OLX92Ytow'},
    'PDP': {'posters': '1U6vEFd_6pakNasu2_UH4EWlHWtC3unXt',
            'audio_video': '1o-Kmfz8xMBhLTxy2h4XbGUHbGlmDdClR'},
    'PSSTR': {'posters': '1YkTeAOoQNKHOJDU4DTh2UVbGeepaM83R',
              'audio_video': '1URcWgKS0JwuKz6DWnv1s6JBTWRDLElvG'},
    'RCCI': {'posters': '11zfZLuXiJWlnrNWYfm9Go6lR3_l_1ihg',
             'audio_video': '11gN-09E8M6ykJ2mY9ESmjyq4oSDDRQXE'},
    'SI': {'posters': '1oRvyKoINMFS6UGnkqrXKjbFoCbRfIpQt',
           'audio_video': '1pAfcrsQLyJHWzutzXIgKTpPz-gf1ojxy'},
    'TD': {'posters': '1PCRyLNmkxv8XMpURuteix0cqWo7hJ0Qd',
           'audio_video': '1W6ppOkGIbrJKdo4IvNO33c5rB18ovDeG'},
    'TIAE': {'posters': '1f20MRPEVvX2xddaFxrtSZ1U9ERrupP54',
             'audio_video': '1vs0KlkZA5-ZyfTpysqi6biFxtbEqx4wk'}
}

# Spreadsheet con los datos de los artículos
INDEX_FILE_ID = '1hOE9pKmfSTRQGrQXNS1O785YWmm2LvZBrUZHK8Tmjm4'
# Rango de celdas que quieres obtener
INDEX_FILE_RANGE = 'Sheet1!B1:H174'
# Pickle con la lista de archivos subidos
PICKLE_FILE_ID = {'t': '1H96Z5OQauTEk7Ya5F0xE7qABM0NWHU1A', 'p': '1tXzKqjsz1qy-y5rpIhvKEu33GZDT7PfB'}

############################################################
#                                                          #
#                  WICC system resources                   #
#                                                          #
############################################################

ENVIRONMENT = None

WICC_URL = {'t': 'https://wicc2023.test.unnoba.edu.ar/',
            'p': 'https://wicc2023.unnoba.edu.ar/'}

WICC_WORKSHOPS_DESCRIPTION = {
    'ARSO': 'Arquitectura, Redes y Sistemas Operativos',
    'ASI': 'Agentes y Sistemas Inteligentes',
    'BDMD': 'Bases de Datos y Minería de Datos',
    'CGIV': 'Computación Gráfica, Imágenes y Visualización',
    'IEI': 'Innovación en Educación en Informática',
    'IS': 'Ingeniería de Software',
    'ISS': 'Innovación en Sistemas de Software',
    'PDP': 'Procesamiento Distribuido y Paralelo',
    'PSSTR': 'Procesamiento de Señales y Sistemas de Tiempo Real',
    'RCCI': 'Redes de Cooperación Científica Internacionales',
    'SI': 'Seguridad Informática',
    'TD': 'Tesis Doctorales',
    'TIAE': 'Tecnología Informática Aplicada en Educación'
}

WICC_WORKSHOPS_DIRECTORIES = {
    'ARSO': 'arquitectura-redes-y-sistemas-operativos/',
    'ASI': 'agentes-y-sistemas-inteligentes/',
    'BDMD': 'bases-de-datos-y-mineria-de-datos/',
    'CGIV': 'computacion-grafica-imagenes-y-visualizacion/',
    'IEI': 'innovacion-en-educacion-en-informatica/',
    'IS': 'ingenieria-de-software/',
    'ISS': 'innovacion-en-sistemas-de-software/',
    'PDP': 'procesamiento-distribuido-y-paralelo/',
    'PSSTR': 'procesamiento-de-senales-y-sistemas-de-tiempo-real/',
    'RCCI': 'redes-de-cooperacion-cientifica-internacionales/',
    'SI': 'seguridad-informatica/',
    'TD': 'tesis-doctorales/',
    'TIAE': 'tecnologia-informatica-aplicada-en-educacion/'
}

############################################################
#                                                          #
#                  Local files and folders                 #
#                                                          #
############################################################

RESOURCES_FOLDER = 'resources/'
LOCAL_ARTICLES_FOLDER = f'{RESOURCES_FOLDER}papers/'
LOCAL_AUTH_FOLDER = f'{RESOURCES_FOLDER}auth/'
HTML_TEMPLATE = 'html_template.txt'
CSS_TEMPLATE = 'css_template.txt'
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
FILELIST_PICKLE_FILE_NAME = {'t': 'uploaded_files_test.pickle', 'p': 'uploaded_files_prod.pickle'}


############################################################
#                                                          #
#                     Script Code                          #
#                                                          #
############################################################

def get_credentials(scopes=None):
    if scopes is None:
        scopes = SCOPES
    creds = None
    path_token = os.path.join(LOCAL_AUTH_FOLDER, TOKEN_FILE)
    path_credentials = os.path.join(LOCAL_AUTH_FOLDER, CREDENTIALS_FILE)
    if os.path.exists(path_token):
        creds = Credentials.from_authorized_user_file(path_token, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(path_credentials, scopes)
            creds = flow.run_local_server(port=0)
        with open(path_token, 'w') as token:
            token.write(creds.to_json())
    return creds


def get_all_files_metadata_in_folders(service, folder_dictionary):
    folder_id_list = [value for folder in folder_dictionary.values() for value in folder.values()]
    files_query = "mimeType!='application/vnd.google-apps.folder' and trashed = false and ('{}' in parents".format(
        folder_id_list[0])
    for folder_id in folder_id_list[1:]:
        files_query += " or '{}' in parents".format(folder_id)
    files_query += ")"
    results = service.files().list(q=files_query, fields="nextPageToken, files(id, name)").execute()
    files = results.get('files', [])
    files_metadata = {}
    for file in files:
        if int(file['name'].split('.')[0]) in files_metadata.keys():
            files_metadata[int(file['name'].split('.')[0])].append(file)
        else:
            files_metadata[int(file['name'].split('.')[0])] = [file]
    return files_metadata


def load_spreadsheet_data(service):
    result = service.spreadsheets().values().get(spreadsheetId=INDEX_FILE_ID, range=INDEX_FILE_RANGE).execute()
    values = result.get('values', [])
    # Convertir los datos en un DataFrame de pandas
    df = pd.DataFrame(values[1:], columns=values[0])
    df['Id'] = df['Id'].astype(int)
    return df


def get_folder_id(service, folder_name):
    query = "mimeType='application/vnd.google-apps.folder' and trashed = false and name='{}'".format(folder_name)
    results = service.files().list(q=query, fields="nextPageToken, files(id)").execute()
    items = results.get('files', [])
    if not items:
        print('No se encontró el directorio')
        return -1
    else:
        folder_id = items[0]['id']
        print('La ID del directorio es: {}'.format(folder_id))
    return folder_id


def get_uploaded_files_indexes(service):
    request = service.files().get_media(fileId=PICKLE_FILE_ID[ENVIRONMENT])
    content = request.execute()
    with open(os.path.join(RESOURCES_FOLDER, FILELIST_PICKLE_FILE_NAME[ENVIRONMENT]), 'wb') as file:
        file.write(content)
    file = open(os.path.join(RESOURCES_FOLDER, FILELIST_PICKLE_FILE_NAME[ENVIRONMENT]), 'rb')
    uploaded_files = pickle.load(file)
    file.close()
    return uploaded_files


def update_uploaded_files_indexes(service, file_list):
    file = open(os.path.join(RESOURCES_FOLDER, FILELIST_PICKLE_FILE_NAME[ENVIRONMENT]), 'wb')
    pickle.dump(file_list, file)
    file.close()
    file_metadata = {
        'name': FILELIST_PICKLE_FILE_NAME[ENVIRONMENT]
    }
    # Subir el archivo al directorio de destino en Drive
    media = googleapiclient.http.MediaFileUpload(os.path.join(RESOURCES_FOLDER, FILELIST_PICKLE_FILE_NAME[ENVIRONMENT]),
                                                 resumable=True)
    service.files().update(fileId=PICKLE_FILE_ID[ENVIRONMENT], body=file_metadata,
                           media_body=media, fields='id').execute()


def download_articles(service, indexes, list_metadata):
    for index in indexes:
        for metadata in list_metadata[index]:
            request = service.files().get_media(fileId=metadata['id'])
            content = request.execute()
            with open(os.path.join(LOCAL_ARTICLES_FOLDER, metadata['name']), 'wb') as file:
                file.write(content)


def generate_html(title, workshop, class_, link, subtitle, pdf, audio, preview):
    path = os.path.join(RESOURCES_FOLDER, HTML_TEMPLATE)
    html = get_template(path).format(title=title, workshop_class=class_, workshop_link=link,
                                     workshop=workshop, subtitle=subtitle, pdf=pdf, audio=audio,
                                     preview=preview)
    return html


def has_required_files(element, files_metadata):
    list_files = files_metadata[element[0]]
    filetypes = [file['name'].split('.')[-1].lower() for file in list_files]
    return 'mp3' in filetypes and 'jpg' in filetypes and 'pdf' in filetypes


def get_required_files(element, files_metadata):
    pdf = [file['id'] for file in files_metadata[element[0]] if file['name'].split('.')[-1].lower() == 'pdf'][0]
    mp3 = [file['id'] for file in files_metadata[element[0]] if file['name'].split('.')[-1].lower() == 'mp3'][0]
    return pdf, mp3


def get_template(path):
    with open(path, 'r') as file:
        content = file.read()
    return content


def create_browser():
    ua = ''
    if sys.platform == 'win32':
        ua = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) ' \
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
    if sys.platform == 'linux':
        ua = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0'

    browser = robobrowser.RoboBrowser(
        history=True,
        user_agent=ua,
        parser='html.parser'
    )
    browser.parser.encode(encoding='utf-8')
    return browser


def login(browser):
    browser.open(f'{WICC_URL[ENVIRONMENT]}wp-admin')
    form = browser.get_form(id='loginform')
    user = input(f"Ingrese su usuario para {WICC_URL[ENVIRONMENT]}wp-admin: ")
    pass_ = getpass.getpass(f"Ingrese su contraseña para {WICC_URL[ENVIRONMENT]}wp-admin: ")
    form['log'].value = user
    form['pwd'].value = pass_
    browser.submit_form(form)
    if browser.response.status_code != 200:
        raise "Error al obtener la página"


def get_categories(browser):
    checkboxes = browser.find_all("input", {"type": "checkbox"})
    categories = {}
    for checkbox in checkboxes:
        if 'name' in checkbox.attrs and \
                'value' in checkbox.attrs and \
                checkbox.attrs['name'] == 'post_category[]':
            categories[checkbox.next.strip()] = checkbox.attrs['value']
    return categories


def process_authors(authors):
    html = '<a href = "mailto:{mail}"<span class ="dashicons dashicons-email-alt mailto"></span></a>, '
    processed = ''
    for author in authors.split(',\n'):
        name = author[:author.rfind(' ')].strip()
        mail = author[author.rfind(' '):]
        processed += f'{name}{html.format(mail=mail)}'
    return processed[:-2]


def publish_in_wicc(browser, element, pdf, mp3):
    title = element[1].upper()
    workshop = element[2]
    authors = process_authors(element[4])
    browser.open(f'{WICC_URL[ENVIRONMENT]}wp-admin/post-new.php')
    form = browser.get_form(id='post')
    form['post_title'].value = title
    form['content'].value = generate_html(title, WICC_WORKSHOPS_DESCRIPTION[workshop], workshop,
                                          f'{WICC_URL[ENVIRONMENT]}{WICC_WORKSHOPS_DIRECTORIES[workshop]}',
                                          authors, pdf, mp3, pdf)
    form['single_custom_css'].value = get_template(os.path.join(RESOURCES_FOLDER, CSS_TEMPLATE))
    form['post_category[]'].value = get_categories(browser)[workshop]
    submit = form.submit_fields['publish']
    browser.submit_form(form, submit)
    if browser.response.status_code != 200:
        raise "Error al obtener la página"


def main():
    global ENVIRONMENT
    while ENVIRONMENT is None:
        selected = input("Ingrese el ambiente (p:producción / t:test): ")
        ENVIRONMENT = selected if selected == 'p' or selected == 't' else None
    try:
        # Me autentico a Google Cloud y obtengo el spreadsheet con los metadatos de los artículos
        creds = get_credentials()
        service_drive = build('drive', 'v3', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)
        document_data = load_spreadsheet_data(sheets_service)

        # Obtengo los ids y nombres de los archivos subidos a directorios específicos de Drive
        files_metadata = get_all_files_metadata_in_folders(service_drive, WICC_FOLDERS_DICTIONARY)

        # Obtengo una lista con los índices de los archivos previamente subidos al sistema de WICC
        uploaded_files_indexes = get_uploaded_files_indexes(service_drive)

        # Filtro de los archivos leídos de Drive los archivos previamente subidos al sistema de WICC
        files_to_upload_indexes = [file for file in files_metadata.keys() if file not in uploaded_files_indexes]

        # Filtro de los metadatos y me quedo solamente con los de los archivos a subir al sistema de WICC
        elements = document_data[document_data['Id'].isin(files_to_upload_indexes)]

        # Este código publica los posters en el sistema de WICC
        browser = create_browser()
        login(browser)
        for element in elements.values:
            if has_required_files(element, files_metadata):
                pdf, mp3 = get_required_files(element, files_metadata)
                publish_in_wicc(browser, element, pdf, mp3)
                uploaded_files_indexes.append(element[0])
                print(f'Se subió el artículo {element[0]} al sistema')
            else:
                print(f'{element[0]} no tiene todos los archivos requeridos')

        # Actualizo la lista de archivos previamente subidos al sistema de WICC
        update_uploaded_files_indexes(service_drive, uploaded_files_indexes)
    except HttpError as error:
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()
