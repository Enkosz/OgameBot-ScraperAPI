import requests
import re
import json

from bs4 import BeautifulSoup
from lxml import etree
from util.scraper.ogame_official_api import OGAME_OFFICIAL_API


class OgameBot(object):
    def __init__(self, email, password, universe, domain):
        self.email = email
        self.password = password
        self.universe = universe
        self.server_url = None
        # Create a session object for save cookies and headers
        self.session = requests.session()
        self.session.headers.update(
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'})
        self.login()

    def login(self):
        # Payload to send for Authentication with Ogame Server
        payload = {
            'kid': '',
            'language': 'en',
            'autologin': 'false',
            'credentials[email]': self.email,
            'credentials[password]': self.password
        }

        # Make POST for get the PHPSESSIONID cookie
        response = self.session.post(
            OGAME_OFFICIAL_API['LOGIN'], data=payload)

        php_session_id = None

        # Scrap the SessionID from the cookies after login
        for cookie in response.cookies:
            if cookie.name == 'PHPSESSID':
                # This Dict it's gonna be used everywhere for make requests and mantain game session
                php_session_id = {'PHPSESSID': cookie.value}
                break

        servers = self.getUniverses()  # Retrive server dict for get the server id
        server_id = None

        # Scrap from the server list by searching the universe name equals to any server in the list
        for server in servers:
            name = server['name'].lower()
            if self.universe.lower() == name:
                server_id = server['number']
                break

        # Retrive all User info containing the servers where is registered
        account_info = self.getAccountInfo(php_session_id)
        server_number = None
        server_language = None

        # Scrap the language of the server and the number from the logged user info
        for info in account_info:
            info_server_number = info['server']['number']
            if info_server_number == server_id:
                server_number = info['id']
                server_language = info['server']['language']
            break

        # Au
        response = self.session.get(
            'https://lobby-api.ogame.gameforge.com/users/me/loginLink?id={}&server[language]={}&server[number]={}'
            .format(server_number, server_language, str(server_id)), cookies=php_session_id).json()
        server_url = response['url']
        stringUrl = re.search(
            'https://(.+\.ogame\.gameforge\.com)/game', server_url)
        self.server_url = stringUrl.group(1)

        response = self.session.get(server_url).content

    def getUniverses(self):
        response = requests.get(OGAME_OFFICIAL_API['SERVERS']).json()

        return response

    def getAccountInfo(self, cookie):
        response = self.session.get(
            OGAME_OFFICIAL_API['ACCOUNT'], cookies=cookie).json()

        return response

    def fetch_planets(self, response=None):
        if not response:
            response = self.session.get(self.get_url('overview')).content

        soup = BeautifulSoup(response, 'html.parser')
        planets = soup.findAll('div', {'class': 'smallplanet'})

        ids = [planet['id'].replace('planet-', '') for planet in planets]

        tree = etree.HTML(response)
        planetsName = tree.xpath(
            "//div[@id='planetList']//span[@class='planet-name ']/text()")
        planetsCoordinate = tree.xpath(
            "//div[@id='planetList']//span[@class='planet-koords ']/text()")

        result = []

        for planetName, planetCoordinate, id in zip(planetsName, planetsCoordinate, ids):
            result.append({'id': id, 'name': planetName,
                           'coordinates': planetCoordinate})
        return result

    def fetch_resources(self, planet_id):
        url = self.get_url('fetchResources', {'cp': planet_id})
        response = self.session.get(url).content.decode('utf8')

        return json.loads(response)

    def get_url(self, page, params=None):
        if params is None:
            params = {}
        if page == 'login':
            return 'https://{}/main/login'.format(self.domain)
        else:
            if self.server_url == '':
                self.server_url = self.get_universe_url(self.universe)
            url = 'https://{}/game/index.php?page={}'.format(
                self.server_url, page)
            if params:
                arr = []
                for key in params:
                    arr.append("{}={}".format(key, params[key]))
                url += '&' + '&'.join(arr)
            return url
