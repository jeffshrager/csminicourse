import requests, json, time, re

headers = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
}
# client param could be replaced with firefox or other browser

target=' is like '
ltarget = len(target)
f = open("gcomplete.out", "w")

def gscrape(key,depth):
    if depth > 0:
        response = requests.get('http://google.com/complete/search?client=chrome&q=a '+key+target,headers=headers)
        for result in json.loads(response.text)[1]:
            if target in result:
                newkey = result[2+ltarget+result.find(target):]
                # Get rid of leading "a " "an " or "the " because that
                # will screw the space test and limit the number of valid results
                newkey = re.sub(r'\b(?:a |an |the )\s+', '', newkey, count=1)
                print(newkey)
                if ' ' not in newkey:
                    output = '('+result+')'
                    print(output)
                    f.write(output+"\n")
                    gscrape(newkey,depth-1)

gscrape('car',4)
f.close()
