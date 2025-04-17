# Script is modified from https://github.com/generalizable-neural-performer/gnr of Wei Cheng from HKUST

from ast import arg
import json, os, sys, pip, copy
from re import sub
def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])
import_or_install("urllib")
import_or_install("requests")
import_or_install("quickxorhash")
import_or_install("asyncio")
import_or_install("pyppeteer")
import urllib, requests, quickxorhash, asyncio
import urllib.request
from urllib import parse
from pyppeteer import launch
from tqdm import tqdm
from requests.models import codes
from requests.adapters import HTTPAdapter, Retry
import base64
import numpy as np
import argparse
import chardet

# simulate browser
header = {
    'sec-ch-ua-mobile': '?0',
    'upgrade-insecure-requests': '1',
    'dnt': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'service-worker-navigation-preload': 'true',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-dest': 'iframe',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}

urls = {
    "mvimgnet" : "https://cuhko365.sharepoint.com/:f:/s/GAP_Lab_MVImgNet/End5E56f5x1IgPiUZ8U5n0kBFedIKvizIy1xnW-yKMtr1w?e=bFySrp"
}

def parse_args():
    """
    Args:
        download_root: path to store download data.
        force: wheather force to download data, 
            we set default value to False, assume that user just want to update data.
            if you have no data in local path, pls set this argument to True.
        subset: data subset to download.
            pls choose type in ['test10', 'train40', 'smpl_depth', 'pretrained_models'].
    """
    parse = argparse.ArgumentParser(description='Download MVImgNet data')
    parse.add_argument('--download_root', type=str, required=True, help='path to store download data')
    parse.add_argument('--force', type=bool, default=False, help='wheather force to download data')
    # parse.add_argument('--subset', type=str, required=True, help='data subset to download')

    args = parse.parse_args()
    
    return args

def newSession():
    s = requests.session()
    retries = Retry(total=5, backoff_factor=0.1)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    return s

def save_hash(path, code):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)

def read_hash(path):
    with open(path, 'r', encoding='utf-8') as f:
        str = f.read()
    return str

def checkHashes(localfile, cloud_hash, localroot, force):
    """
    Synchronize local file with cloud file by hash checking
    (For MVImgNet, the file is on Onedrive for Bussiness, only "quickXorHash" is avalible)
    ref: https://docs.microsoft.com/en-us/onedrive/developer/rest-api/resources/hashes?view=odsp-graph-online
    Args:
        localfile: local file path
        cloud_hash: cloud hash of cloud file 
    Output:
        matched: [True, False], whether local file matches with cloud file
    """
    if not os.path.exists(os.path.dirname(localfile)):
        os.makedirs(os.path.dirname(localfile), exist_ok=True)
    if localfile.split('/')[1] == 'pretrained_models':
        local_hash_bkup = os.path.join(localroot, '.hash', os.path.join(localfile.split('/')[2], localfile.split('/')[3].split('.')[0]+'.txt'))
    else:
        local_hash_bkup = os.path.join(localroot, '.hash', os.path.join(localfile.split('/')[-1].split('.')[0]+'.txt'))
    if not os.path.exists(os.path.dirname(local_hash_bkup)):
        os.makedirs(os.path.dirname(local_hash_bkup), exist_ok=True)    

    if force:
        save_hash(local_hash_bkup, cloud_hash["quickXorHash"])
        tqdm.write(f"force to download data")
        return False

    # if local file is not deleted
    if os.path.exists(localfile):
        with open(localfile, 'rb') as lf:
            content = lf.read()
            hash = quickxorhash.quickxorhash()
            hash.update(content)
            hashoutput = base64.b64encode(hash.digest()).decode('ascii')
            # # write local hash backup
            save_hash(local_hash_bkup, cloud_hash["quickXorHash"])
            if hashoutput == cloud_hash["quickXorHash"]:
                tqdm.write(f"[{os.path.relpath(localfile, localroot)}] local file is up-to-date, skip downloading")
                return True
            else:
                tqdm.write(f"[{os.path.relpath(localfile, localroot)}] local file is out-of-date, updating")
                return False
    else:
        if os.path.isfile(local_hash_bkup):
            # read hashcode and compare
            hashoutput = read_hash(local_hash_bkup)
            if hashoutput == cloud_hash["quickXorHash"]:
                tqdm.write(f"[{os.path.relpath(localfile, localroot)}] local file is up-to-date, skip downloading")
                return True
            else:
                save_hash(local_hash_bkup, cloud_hash["quickXorHash"])
                tqdm.write(f"[{os.path.relpath(localfile, localroot)}] local file is out-of-date, updating")
                return False

        else:
            # write and record hashcode in txt file
            save_hash(local_hash_bkup, cloud_hash["quickXorHash"])
            tqdm.write(f"[{os.path.basename(localfile)}] no local file or local file is missing, downloading")
            # sys.stdout.flush()
            return False
        

def getFiles(originalUrl, download_path, force, download_root=None, req=None, layers=0, _id=0):
    """
    Get file from folder share link (with "-my" share point url)
    ref: https://docs.microsoft.com/en-us/graph/use-the-api

    Args:
        originalUrl: share link
        download_path: path to download
        req: request None
    """
    isSharepoint = False
    if "-my" not in originalUrl:
        isSharepoint = True
    if req == None:
        req = newSession()
    reqf = req.get(originalUrl, headers=header)
    if ',"FirstRow"' not in reqf.text:
        print("\t"*layers, "No file in this folder")
        return 0
    if download_root is None:
        download_root = download_path

    filesData = []
    redirectURL = reqf.url

    query = dict(urllib.parse.parse_qsl(
        urllib.parse.urlsplit(redirectURL).query))
    redirectSplitURL = redirectURL.split("/")

    relativeFolder = ""
    rootFolder = query["id"]
    for i in rootFolder.split("/"):
        if isSharepoint:
            if i != "Shared Documents":
                relativeFolder += i+"/"
            else:
                relativeFolder += i
                break
        else:
            if i != "Documents":
                relativeFolder += i+"/"
            else:
                relativeFolder += i
                break
    relativeUrl = parse.quote(relativeFolder).replace(
        "/", "%2F").replace("_", "%5F").replace("-", "%2D")
    rootFolderUrl = parse.quote(rootFolder).replace(
        "/", "%2F").replace("_", "%5F").replace("-", "%2D")

    graphqlVar = '{"query":"query (\n        $listServerRelativeUrl: String!,$renderListDataAsStreamParameters: RenderListDataAsStreamParameters!,$renderListDataAsStreamQueryString: String!\n        )\n      {\n      \n      legacy {\n      \n      renderListDataAsStream(\n      listServerRelativeUrl: $listServerRelativeUrl,\n      parameters: $renderListDataAsStreamParameters,\n      queryString: $renderListDataAsStreamQueryString\n      )\n    }\n      \n      \n  perf {\n    executionTime\n    overheadTime\n    parsingTime\n    queryCount\n    validationTime\n    resolvers {\n      name\n      queryCount\n      resolveTime\n      waitTime\n    }\n  }\n    }","variables":{"listServerRelativeUrl":"%s","renderListDataAsStreamParameters":{"renderOptions":5707527,"allowMultipleValueFilterForTaxonomyFields":true,"addRequiredFields":true,"folderServerRelativeUrl":"%s"},"renderListDataAsStreamQueryString":"@a1=\'%s\'&RootFolder=%s&TryNewExperienceSingle=TRUE"}}' % (relativeFolder, rootFolder, relativeUrl, rootFolderUrl)

    s2 = urllib.parse.urlparse(redirectURL)
    tempHeader = copy.deepcopy(header)
    tempHeader["referer"] = redirectURL
    tempHeader["cookie"] = reqf.headers["set-cookie"]
    tempHeader["authority"] = s2.netloc
    tempHeader["content-type"] = "application/json;odata=verbose"

    graphqlReq = req.post(
        "/".join(redirectSplitURL[:-3])+"/_api/v2.1/graphql", data=graphqlVar.encode('utf-8'), headers=tempHeader)
    graphqlReq = json.loads(graphqlReq.text)
    if "NextHref" in graphqlReq["data"]["legacy"]["renderListDataAsStream"]["ListData"]:
        nextHref = graphqlReq[
            "data"]["legacy"]["renderListDataAsStream"]["ListData"]["NextHref"]+"&@a1=%s&TryNewExperienceSingle=TRUE" % (
            "%27"+relativeUrl+"%27")
        filesData.extend(graphqlReq[
            "data"]["legacy"]["renderListDataAsStream"]["ListData"]["Row"])

        listViewXml = graphqlReq[
            "data"]["legacy"]["renderListDataAsStream"]["ViewMetadata"]["ListViewXml"]
        renderListDataAsStreamVar = '{"parameters":{"__metadata":{"type":"SP.RenderListDataParameters"},"RenderOptions":1216519,"ViewXml":"%s","AllowMultipleValueFilterForTaxonomyFields":true,"AddRequiredFields":true}}' % (
            listViewXml).replace('"', '\\"')

        graphqlReq = req.post(
            "/".join(redirectSplitURL[:-3])+"/_api/web/GetListUsingPath(DecodedUrl=@a1)/RenderListDataAsStream"+nextHref, data=renderListDataAsStreamVar.encode('utf-8'), headers=tempHeader)
        graphqlReq = json.loads(graphqlReq.text)

        while "NextHref" in graphqlReq["ListData"]:
            nextHref = graphqlReq["ListData"]["NextHref"]+"&@a1=%s&TryNewExperienceSingle=TRUE" % (
                "%27"+relativeUrl+"%27")
            filesData.extend(graphqlReq["ListData"]["Row"])
            graphqlReq = req.post(
                "/".join(redirectSplitURL[:-3])+"/_api/web/GetListUsingPath(DecodedUrl=@a1)/RenderListDataAsStream"+nextHref, data=renderListDataAsStreamVar.encode('utf-8'), headers=tempHeader)
            graphqlReq = json.loads(graphqlReq.text)
        filesData.extend(graphqlReq["ListData"]["Row"])
    else:
        filesData.extend(graphqlReq[
            "data"]["legacy"]["renderListDataAsStream"]["ListData"]["Row"])

    filesData = sorted(filesData, key=lambda x: x['FileLeafRef'])
    for i in filesData:
        # if is a folder, download recursively
        if i['FSObjType'] == "1":
            _query = query.copy()
            _query['id'] = os.path.join(_query['id'],  i['FileLeafRef']).replace("\\", "/")
            if not isSharepoint:
                originalPath = "/".join(redirectSplitURL[:-1]) + \
                    "/onedrive.aspx?" + urllib.parse.urlencode(_query)
            else:
                originalPath = "/".join(redirectSplitURL[:-1]) + \
                    "/AllItems.aspx?" + urllib.parse.urlencode(_query)
            getFiles(originalPath, os.path.join(download_path, i['FileLeafRef']), force, download_root, req=req, layers=layers+1)
        # if is a file, download directly
        else:
            reqf = req.get(i[".spItemUrl"], headers=header)
            filemeta = json.loads(reqf.text)

            url, name, hash = filemeta["@content.downloadUrl"], filemeta["name"], filemeta["file"]["hashes"]
            r = requests.get(url, stream = True) 
            total_length = int(r.headers.get('content-length', 0))
            local_file = os.path.join(download_path, name)
            
            # Check hash code of local file and cloud file
            if not checkHashes(local_file, hash, download_root, force):            
                with open(os.path.join(download_path, name), 'wb') as f, \
                    tqdm(desc=os.path.relpath(local_file, download_root),total=total_length,
                         unit='iB',unit_scale=True,unit_divisor=1024) as bar:
                    for chunk in r.iter_content(chunk_size = 1024): 
                        if chunk: 
                            size = f.write(chunk)
                            bar.update(size)


pheader = {}
url = ""

async def fetch_with_pwd(iurl, password):
    """
    Fetch data with data password

    Args:
        iurl: input share folder url
        password: password of the share folder
    """
    global pheader, url
    browser = await launch(options={'args': ['--no-sandbox']})
    page = await browser.newPage()
    await page.goto(iurl, {'waitUntil': 'networkidle0'})
    await page.focus("input[id='txtPassword']")
    await page.keyboard.type(password)
    verityElem = await page.querySelector("input[id='btnSubmitPassword']")
    print("Password input complete, jumping")

    await asyncio.gather(
        page.waitForNavigation(),
        verityElem.click(),
    )
    url = await page.evaluate('window.location.href', force_expr=True)
    await page.screenshot({'path': 'example.png'})
    print("Fetching cookies")
    _cookie = await page.cookies()
    pheader = ""
    for __cookie in _cookie:
        coo = "{}={};".format(__cookie.get("name"), __cookie.get("value"))
        pheader += coo
    await browser.close()

def havePwdGetFiles(iurl, password, download_path, force):
    global header
    asyncio.get_event_loop().run_until_complete(fetch_with_pwd(iurl, password))
    header['cookie'] = pheader
    getFiles(url, download_path, force)


if __name__ == "__main__":
    args = parse_args()
    download_root = args.download_root
    force = args.force
    pwd = input("Please input MVImgNet password, or contact with the author for data access: \n")
    havePwdGetFiles( urls["mvimgnet"], pwd, download_root , force )
