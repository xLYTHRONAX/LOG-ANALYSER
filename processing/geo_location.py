import requests
URL_IPINFO = 'https://ipinfo.io'
def get_location(ip):
    response=requests.get(URL_IPINFO+'/'+ip+'/json', params={'token': '6df056949e2139'})
    print(response.status_code, response.text) 
    if response.status_code==200:
        return response.json()
    
if __name__=='__main__':
    print(get_location('138.199.39.186'))