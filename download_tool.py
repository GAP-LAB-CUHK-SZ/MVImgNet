# Script is modified from https://github.com/generalizable-neural-performer/gnr of Wei Cheng from HKUST

# python download_tool_mvhuman.py --data_name MVHumanNet_0_samples --url https://cuhko365.sharepoint.com/:f:/s/SSE_GAP-Lab/Eh25k6jjh0NIvxLLBKP7U4EBFcuNrYy3Gf34ZfEjdFDgGQ?e=36Pe2X --download_folder ./test_mvhuman_data



import argparse
import base64
import json
import os
import re

import pip
from tqdm import tqdm


def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(["install", package])
# Ensure necessary packages are available
import_or_install("urllib")
import_or_install("requests")
import_or_install("quickxorhash")
import_or_install("asyncio")  # Kept as per original script
import_or_install("pyppeteer")  # Kept as per original script

import urllib.request
from urllib import parse
import requests
from requests.adapters import HTTPAdapter, Retry

# simulate browser
header = {
    "sec-ch-ua-mobile": "?0",
    "upgrade-insecure-requests": "1",
    "dnt": "1",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51"
    ),
    "accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.9"
    ),
    "service-worker-navigation-preload": "true",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "navigate",
    "sec-fetch-dest": "iframe",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
}

def get_file_size(file_path):
    size_bytes = os.path.getsize(file_path)
    size_kb = size_bytes / 1024
    return size_kb

def parse_args():
    """
    Parses command-line arguments for the download script.
    """
    parser = argparse.ArgumentParser(description="Download MVImgNet data")
    parser.add_argument(
        "--data_name",
        type=str,
        required=True,
        help="input the folder name you want to download. [MVImgNet_origin, MVImgNet_category, MVImgNet_mask]",
    )
    # parser.add_argument(
    #     "--url", type=str, required=True, help="Download link from SharePoint"
    # )
    parser.add_argument(
        "--download_folder",
        type=str,
        required=True,
        help="Path to store downloaded data",
    )
    parser.add_argument(
        "--force",
        type=bool,
        default=False,
        help="Whether to force download data, even if it seems to exist",
    )
    parser.add_argument(
        "--file_list",
        type=str,
        default=None,
        help="Path to a text file listing specific files to download.",
    )
    parser.add_argument(
        "--skip_first_n",
        type=int,
        default=0,
        help="Skip the first N files/folders in the SharePoint listing.",
    )
    return parser.parse_args()

def newSession():
    s = requests.session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def save_hash(path, code):
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)

def read_hash(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def checkHashes(localfile, cloud_hash_data, localroot, force_download):
    """
    Synchronize local file with cloud file by hash checking.
    (Note: This function is defined but not currently used in getFiles)
    """
    if not os.path.exists(os.path.dirname(localfile)):
        os.makedirs(os.path.dirname(localfile), exist_ok=True)

    # Simplified hash backup path logic from original
    hash_filename = os.path.splitext(os.path.basename(localfile))[0] + ".txt"
    local_hash_bkup_dir = os.path.join(localroot, ".hash")
    if localfile.split(os.sep)[1] == "pretrained_models":  # Original logic
        # This path construction seems very specific, ensure it matches your structure if used
        local_hash_bkup_dir = os.path.join(
            localroot, ".hash", localfile.split(os.sep)[2]
        )
    local_hash_bkup = os.path.join(local_hash_bkup_dir, hash_filename)

    if not os.path.exists(os.path.dirname(local_hash_bkup)):
        os.makedirs(os.path.dirname(local_hash_bkup), exist_ok=True)

    cloud_quickxor_hash = cloud_hash_data.get("quickXorHash")
    if not cloud_quickxor_hash:
        tqdm.write(
            f"Warning: No quickXorHash found for {localfile}. Skipping hash check."
        )
        return False  # Cannot verify, assume download is needed

    if force_download:
        save_hash(local_hash_bkup, cloud_quickxor_hash)
        tqdm.write(f"Force download for {os.path.basename(localfile)}")
        return False

    if os.path.exists(localfile):
        with open(localfile, "rb") as lf:
            content = lf.read()
            hasher = quickxorhash.quickxorhash()
            hasher.update(content)
            local_quickxor_hash = base64.b64encode(hasher.digest()).decode("ascii")
            save_hash(local_hash_bkup, cloud_quickxor_hash)  # Update stored cloud hash
            if local_quickxor_hash == cloud_quickxor_hash:
                tqdm.write(
                    f"[{os.path.relpath(localfile, localroot)}] local file is up-to-date."
                )
                return True
            else:
                tqdm.write(
                    f"[{os.path.relpath(localfile, localroot)}] local file is out-of-date."
                )
                return False
    else:  # Local file does not exist
        if os.path.isfile(local_hash_bkup):
            stored_cloud_hash = read_hash(local_hash_bkup)
            if stored_cloud_hash == cloud_quickxor_hash:
                # This case is tricky: local file missing, but hash matches.
                # Could mean file was deleted after a successful download.
                # For safety, better to re-download if file is missing.
                tqdm.write(
                    f"[{os.path.relpath(localfile, localroot)}] local file missing, but stored hash matches. Re-downloading."
                )
                save_hash(local_hash_bkup, cloud_quickxor_hash)  # Ensure it's current
                return False
            else:
                # Stored hash is outdated, or no hash was stored.
                save_hash(local_hash_bkup, cloud_quickxor_hash)
                tqdm.write(
                    f"[{os.path.relpath(localfile, localroot)}] local file missing or hash outdated."
                )
                return False
        else:
            save_hash(local_hash_bkup, cloud_quickxor_hash)
            tqdm.write(f"[{os.path.basename(localfile)}] no local file or hash record.")
            return False

def getFiles(
    # originalUrl,
    data_name,
    download_path,
    force,
    file_list_path,
    skip_first_n=0,
    download_root=None,
    req=None,
    layers=0,
):
    """
    Get files from a SharePoint folder share link.
    """
    if req is None:
        req = newSession()
    urlList = {
            "MVImgNet_origin":  "https://cuhko365.sharepoint.com/:f:/s/GAP_Lab_MVImgNet/Eqr0CanUxwhMqCuEqgZ7ZlgBq96EGddlT_WrgLIlZWhyWA?e=p31m4o" ,
            "MVImgNet_category" : "https://cuhko365.sharepoint.com/:f:/s/GAP_Lab_MVImgNet/EhbyhYOrEgxJqnanJ1CJko4BtH4bSUHEmhswDwWDc4Id0g?e=I9fh2H" ,
            "MVImgNet_mask" : "https://cuhko365.sharepoint.com/:f:/s/GAP_Lab_MVImgNet/Em4XOkt_zAlGvXlAgoqb9nYBTmCMjVUVnTEuAf2IX7I9_w?e=5l3D3m"
        }
    originalUrl = urlList[data_name]
    print(f"LAYER {layers}: Fetching initial URL: {originalUrl}")
    try:

        reqf = req.get(originalUrl, headers=header, timeout=30)
        reqf.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"LAYER {layers}: Failed to fetch initial URL {originalUrl}: {e}")
        return 0

    redirectURL = reqf.url
    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(redirectURL).query))

    print(f"LAYER {layers}: Redirect URL: {redirectURL}")
    print(f"LAYER {layers}: Query parameters: {query}")

    context_info = None
    form_digest_value = None
    site_absolute_url = None
    list_url_from_context = None

    match_context = re.search(
        r"var _spPageContextInfo\s*=\s*({.*?});", reqf.text, re.DOTALL
    )
    if match_context:
        try:
            context_info_json_str = match_context.group(1)
            context_info_json_str_cleaned = re.sub(
                r",\s*([}\]])", r"\1", context_info_json_str
            )
            context_info = json.loads(context_info_json_str_cleaned)

            form_digest_value = context_info.get("formDigestValue")
            site_absolute_url = context_info.get("webAbsoluteUrl")
            list_url_from_context = context_info.get("listUrl")

            print(f"LAYER {layers}: Extracted siteAbsoluteUrl: {site_absolute_url}")
            print(f"LAYER {layers}: Extracted listUrl: {list_url_from_context}")
            print(
                f"LAYER {layers}: Extracted formDigestValue: "
                f"{'Present' if form_digest_value else 'Not Present'}"
            )
        except json.JSONDecodeError as e:
            print(f"LAYER {layers}: Warning - Failed to parse _spPageContextInfo: {e}")
        except Exception as e_ctx:
            print(
                f"LAYER {layers}: Warning - Error processing _spPageContextInfo: {e_ctx}"
            )
    else:
        print(
            f"LAYER {layers}: Warning - _spPageContextInfo not found. "
            "Critical for API calls."
        )

    if download_root is None:
        download_root = download_path

    current_folder_server_relative_url = query.get("id")
    if not current_folder_server_relative_url:
        print(
            f"LAYER {layers}: Error - 'id' parameter missing in query. "
            "Cannot determine folder path."
        )
        return 0

    list_server_relative_url_for_gql = list_url_from_context
    if not list_server_relative_url_for_gql:
        path_parts = current_folder_server_relative_url.strip("/").split("/")
        if len(path_parts) >= 3 and path_parts[0].lower() == "sites":
            list_server_relative_url_for_gql = "/" + "/".join(path_parts[:3])
        elif len(path_parts) > 1:
            list_server_relative_url_for_gql = os.path.dirname(
                current_folder_server_relative_url
            )
        else:
            list_server_relative_url_for_gql = current_folder_server_relative_url
        print(
            f"LAYER {layers}: Warning - Inferred "
            f"list_server_relative_url_for_gql as: "
            f"{list_server_relative_url_for_gql}"
        )

    if not list_server_relative_url_for_gql:
        print(
            f"LAYER {layers}: Error - Could not determine "
            "list_server_relative_url_for_gql."
        )
        return 0

    print(
        f"LAYER {layers}: Using list_server_relative_url_for_gql: "
        f"{list_server_relative_url_for_gql}"
    )
    print(
        f"LAYER {layers}: Using current_folder_server_relative_url: "
        f"{current_folder_server_relative_url}"
    )

    encoded_list_for_querystring = parse.quote(list_server_relative_url_for_gql)
    encoded_folder_for_querystring = parse.quote(current_folder_server_relative_url)

    graphql_query_string_part = (
        f"@a1='{encoded_list_for_querystring}'"
        f"&RootFolder={encoded_folder_for_querystring}"
        "&TryNewExperienceSingle=TRUE"
    )
    graphql_query_template = (
        "query ($listServerRelativeUrl: String!, "
        "$renderListDataAsStreamParameters: RenderListDataAsStreamParameters!, "
        "$renderListDataAsStreamQueryString: String!) { "
        "legacy { renderListDataAsStream("
        "listServerRelativeUrl: $listServerRelativeUrl, "
        "parameters: $renderListDataAsStreamParameters, "
        "queryString: $renderListDataAsStreamQueryString) } "
        "perf { executionTime overheadTime parsingTime queryCount "
        "validationTime resolvers { name queryCount resolveTime waitTime } } }"
    )
    graphql_payload_dict = {
        "query": graphql_query_template,
        "variables": {
            "listServerRelativeUrl": list_server_relative_url_for_gql,
            "renderListDataAsStreamParameters": {
                "renderOptions": 5707527,
                "allowMultipleValueFilterForTaxonomyFields": True,
                "addRequiredFields": True,
                "folderServerRelativeUrl": current_folder_server_relative_url,
            },
            "renderListDataAsStreamQueryString": graphql_query_string_part,
        },
    }
    graphql_post_data = json.dumps(graphql_payload_dict)

    graphql_headers = {
        "Accept": "application/json;odata=verbose",
        "Content-Type": "application/json;odata=verbose",
        "User-Agent": header["user-agent"],
        "Referer": redirectURL,
    }
    if form_digest_value:
        graphql_headers["X-RequestDigest"] = form_digest_value
    else:
        print(
            f"LAYER {layers}: Warning - formDigestValue not available. "
            "X-RequestDigest header will be missing."
        )

    graphql_api_endpoint = None
    if site_absolute_url:
        graphql_api_endpoint = f"{site_absolute_url.rstrip('/')}/_api/v2.1/graphql"
    else:
        url_parts = urllib.parse.urlparse(redirectURL)
        path_segments = url_parts.path.strip("/").split("/")
        if len(path_segments) >= 2 and path_segments[0].lower() == "sites":
            site_base_path = "/".join(path_segments[:2])
            graphql_api_endpoint = (
                f"{url_parts.scheme}://{url_parts.netloc}/"
                f"{site_base_path}/_api/v2.1/graphql"
            )
        else:
            redirectSplitURL = redirectURL.split("/")
            graphql_api_endpoint = (
                "/".join(redirectSplitURL[:-3]).rstrip("/") + "/_api/v2.1/graphql"
            )
        print(
            f"LAYER {layers}: Warning - Using fallback GraphQL endpoint "
            f"construction: {graphql_api_endpoint}"
        )

    if not graphql_api_endpoint:
        print(f"LAYER {layers}: Error - Could not determine GraphQL API endpoint.")
        return 0

    print(f"LAYER {layers}: GraphQL API Endpoint: {graphql_api_endpoint}")

    try:
        response_graphql = req.post(
            graphql_api_endpoint,
            data=graphql_post_data.encode("utf-8"),
            headers=graphql_headers,
            timeout=30,
        )
        graphql_response_data = response_graphql.json()
    except requests.exceptions.RequestException as e_req:
        print(f"LAYER {layers}: GraphQL request failed with RequestException: {e_req}")
        return 0
    except json.JSONDecodeError:
        status_code = (
            response_graphql.status_code
            if "response_graphql" in locals()
            else "Unknown"
        )
        resp_text = (
            (response_graphql.text[:500] + "...")
            if "response_graphql" in locals()
            else "No response object"
        )
        print(
            f"LAYER {layers}: Failed to decode JSON response from GraphQL. "
            f"Status: {status_code}. Response: {resp_text}"
        )
        return 0

    if "errors" in graphql_response_data and graphql_response_data["errors"]:
        print(f"LAYER {layers}: GraphQL response contains errors:")
        for err_idx, err_item in enumerate(graphql_response_data["errors"]):
            err_code = err_item.get("extensions", {}).get("code")
            print(
                f"  Error {err_idx + 1}: {err_item.get('message')} (Code: {err_code})"
            )
        if any(
            e.get("extensions", {}).get("code") == "unauthenticated"
            for e in graphql_response_data["errors"]
        ):
            print(
                f"LAYER {layers}: CRITICAL - Unauthenticated error from GraphQL. "
                "Cannot proceed for this folder."
            )
            return 0

    legacy_data = graphql_response_data.get("data", {}).get("legacy", {})
    render_list_data = legacy_data.get("renderListDataAsStream")

    if render_list_data is None:
        print(
            f"LAYER {layers}: renderListDataAsStream is null. Cannot list files "
            f"for {current_folder_server_relative_url}."
        )
        return 0

    all_items_from_gql = []
    current_list_data_node = render_list_data.get("ListData")

    if not current_list_data_node:
        print(
            f"LAYER {layers}: ListData node not found for "
            f"{current_folder_server_relative_url}."
        )
        return 0

    if "Row" in current_list_data_node:
        all_items_from_gql.extend(current_list_data_node["Row"])

    while "NextHref" in current_list_data_node:
        nextHref_raw = current_list_data_node["NextHref"]
        next_page_query_params = (
            f"{nextHref_raw}&@a1='{encoded_list_for_querystring}'"
            "&TryNewExperienceSingle=TRUE"
        )

        listViewXml = render_list_data.get("ViewMetadata", {}).get("ListViewXml", "")
        listViewXml_escaped = listViewXml.replace('"', '\\"')

        pagination_post_payload_dict = {
            "parameters": {
                "__metadata": {"type": "SP.RenderListDataParameters"},
                "RenderOptions": 1216519,
                "ViewXml": listViewXml_escaped,
                "AllowMultipleValueFilterForTaxonomyFields": True,
                "AddRequiredFields": True,
            }
        }
        pagination_post_data_str = json.dumps(pagination_post_payload_dict)

        if not site_absolute_url:
            print(
                f"LAYER {layers}: Error - site_absolute_url not available "
                "for pagination. Cannot proceed."
            )
            break

        pagination_api_url = (
            f"{site_absolute_url.rstrip('/')}/_api/web/"
            f"GetListUsingPath(DecodedUrl='{list_server_relative_url_for_gql}')"
            f"/RenderListDataAsStream{next_page_query_params}"
        )

        print(
            f"LAYER {layers}: Pagination request URL (first 150): "
            f"{pagination_api_url[:150]}"
        )
        try:
            response_pagination = req.post(
                pagination_api_url,
                data=pagination_post_data_str.encode("utf-8"),
                headers=graphql_headers,
                timeout=30,
            )
            pagination_response_json = response_pagination.json()

            if pagination_response_json.get("error") or pagination_response_json.get(
                "errors"
            ):
                err_msg = json.dumps(
                    pagination_response_json.get("error")
                    or pagination_response_json.get("errors")
                )
                print(f"LAYER {layers}: Error in pagination response: {err_msg}")
                break

            current_list_data_node = pagination_response_json.get("ListData")
            if not current_list_data_node or "Row" not in current_list_data_node:
                print(
                    f"LAYER {layers}: Unexpected pagination response or no 'Row' data."
                )
                break
            all_items_from_gql.extend(current_list_data_node["Row"])

        except requests.exceptions.RequestException as e_req_page:
            print(f"LAYER {layers}: Pagination request failed: {e_req_page}")
            break
        except json.JSONDecodeError:
            status = (
                response_pagination.status_code
                if "response_pagination" in locals()
                else "Unknown"
            )
            resp_text = (
                (response_pagination.text[:200] + "...")
                if "response_pagination" in locals()
                else ""
            )
            print(
                f"LAYER {layers}: Failed to decode JSON from pagination. "
                f"Status: {status}. Response: {resp_text}"
            )
            break

    if not os.path.exists(download_path):
        os.makedirs(download_path, exist_ok=True)

    selected_files_basenames = None
    if file_list_path is not None:
        try:
            with open(file_list_path, "r", encoding="utf-8") as f_selected:
                selected_files_raw = f_selected.read().splitlines()
            selected_files_basenames = [
                os.path.basename(item) for item in selected_files_raw if item.strip()
            ]
            print(
                f"LAYER {layers}: Will only download files from list: "
                f"{selected_files_basenames}"
            )
        except FileNotFoundError:
            print(
                f"LAYER {layers}: Warning - File list not found at "
                f"{file_list_path}. Will download all files."
            )

    all_items_from_gql_sorted = sorted(
        all_items_from_gql, key=lambda x: x.get("FileLeafRef", "")
    )

    for item_idx, item_data in enumerate(all_items_from_gql_sorted):
        file_leaf_ref = item_data.get("FileLeafRef")
        if not file_leaf_ref:
            print(f"LAYER {layers}: Skipping item with no FileLeafRef: {item_data}")
            continue

        item_is_folder = item_data.get("FSObjType") == "1"

        if item_idx < skip_first_n:
            continue

        if item_is_folder:
            print(f"\nLAYER {layers}: Processing subfolder: {file_leaf_ref}")
            subfolder_server_relative_path = os.path.join(
                current_folder_server_relative_url, file_leaf_ref
            ).replace("\\", "/")

            base_page_url_for_recursion = redirectURL.split("?")[0]
            new_query_params_for_recursion = query.copy()
            new_query_params_for_recursion["id"] = subfolder_server_relative_path

            subfolder_original_url_for_recursion = (
                f"{base_page_url_for_recursion}?"
                f"{urllib.parse.urlencode(new_query_params_for_recursion)}"
            )

            getFiles(
                subfolder_original_url_for_recursion,
                os.path.join(download_path, file_leaf_ref),
                force,
                file_list_path,
                0,  # skip_first_n is per-level
                download_root,
                req=req,
                layers=layers + 1,
            )
        else:  # It's a file
            if (
                selected_files_basenames is not None
                and file_leaf_ref not in selected_files_basenames
            ):
                continue

            download_url_from_gql = item_data.get("@content.downloadUrl")
            if not download_url_from_gql:
                sp_item_url_for_meta = item_data.get(".spItemUrl")
                if sp_item_url_for_meta:
                    print(
                        f"LAYER {layers}: No direct @content.downloadUrl for "
                        f"{file_leaf_ref}, fetching .spItemUrl: "
                        f"{sp_item_url_for_meta}"
                    )
                    try:
                        meta_resp = req.get(
                            sp_item_url_for_meta, headers=header, timeout=10
                        )
                        meta_resp.raise_for_status()
                        filemeta_json = meta_resp.json()
                        download_url_from_gql = filemeta_json.get(
                            "@content.downloadUrl"
                        )
                    except Exception as e_meta_fetch:
                        print(
                            f"LAYER {layers}: Error fetching/parsing metadata "
                            f"from .spItemUrl for {file_leaf_ref}: {e_meta_fetch}"
                        )
                        continue
                else:
                    print(
                        f"LAYER {layers}: Cannot get download URL for file: "
                        f"{file_leaf_ref} (no @content.downloadUrl or .spItemUrl)"
                    )
                    continue

            if not download_url_from_gql:
                print(
                    f"LAYER {layers}: Still no download_url for {file_leaf_ref} "
                    "after checks. Skipping."
                )
                continue

            local_file_path = os.path.join(download_path, file_leaf_ref)
            extracted_archive_folder_path = os.path.join(
                download_path, os.path.splitext(file_leaf_ref)[0]
            )

            if os.path.exists(extracted_archive_folder_path) and not force:
                print(
                    f"LAYER {layers}: Extracted folder for {file_leaf_ref} "
                    "already exists. Skipping download."
                )
                continue
            elif os.path.exists(local_file_path) and not force:
                try:
                    arch_size_kb = get_file_size(local_file_path)
                    if arch_size_kb > 300:
                        print(
                            f"LAYER {layers}: Archive {file_leaf_ref} already "
                            "downloaded (>300KB) and not forcing. Skipping."
                        )
                        continue
                    else:
                        print(
                            f"LAYER {layers}: Archive {file_leaf_ref} exists "
                            f"but is small ({arch_size_kb:.2f}KB). Re-downloading."
                        )
                except OSError:
                    print(
                        f"LAYER {layers}: Could not get size of existing file "
                        f"{local_file_path}. Will attempt download."
                    )

            print(
                f"LAYER {layers}: Attempting to download: {file_leaf_ref} "
                f"to {local_file_path}"
            )
            try:
                r_download = requests.get(
                    download_url_from_gql, stream=True, timeout=60
                )
                r_download.raise_for_status()
                total_length = int(r_download.headers.get("content-length", 0))

                with (
                    open(local_file_path, "wb") as f_dl,
                    tqdm(
                        desc=os.path.relpath(local_file_path, download_root),
                        total=total_length,
                        unit="iB",
                        unit_scale=True,
                        unit_divisor=1024,
                        leave=(layers == 0),
                    ) as bar,
                ):
                    for chunk in r_download.iter_content(chunk_size=8192):
                        if chunk:
                            size = f_dl.write(chunk)
                            bar.update(size)
                print(f"LAYER {layers}: Successfully downloaded {file_leaf_ref}")
            except requests.exceptions.RequestException as e_dl_final:
                print(
                    f"LAYER {layers}: Error during download for "
                    f"{file_leaf_ref}: {e_dl_final}"
                )
                if os.path.exists(local_file_path):
                    try:
                        os.remove(local_file_path)
                    except OSError as e_rm:
                        print(
                            f"LAYER {layers}: Error removing partial file "
                            f"{local_file_path}: {e_rm}"
                        )
            except Exception as e_generic_dl:
                print(
                    f"LAYER {layers}: Generic error during download for "
                    f"{file_leaf_ref}: {e_generic_dl}"
                )
                if os.path.exists(local_file_path):
                    try:
                        os.remove(local_file_path)
                    except OSError as e_rm:
                        print(
                            f"LAYER {layers}: Error removing partial file "
                            f"{local_file_path}: {e_rm}"
                        )
    return 1

if __name__ == "__main__":
    cli_args = parse_args()
    getFiles(
        # cli_args.url,
        cli_args.data_name,
        cli_args.download_folder,
        cli_args.force,
        cli_args.file_list,
        cli_args.skip_first_n,
    )