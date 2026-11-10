import os
import pandas as pd
import subprocess as sp
import xmltodict as x2d

from argparse import ArgumentParser
from urllib.request import urlretrieve
from zipfile import ZipFile

DATA_DIR = "./data"
XBI_URL_ROOT = "https://apps.irs.gov/pub/epostcard/990/xml/" # append .../<year>/<xbi>.zip
VERBOSE = True  # set to false in any production, maybe?

def get_index_row_from_ein( index_df: pd.DataFrame, ein: int) -> dict:
    ein_index_df = index_df[index_df.EIN == ein].reset_index()
    if len(ein_index_df) > 0:
        if len(ein_index_df) > 1:
            disp_col = ["TAXPAYER_NAME", "TAX_PERIOD", "OBJECT_ID"]
            print(f"Available 990s filed by {ein}:")
            print(ein_index_df[disp_col])
            row_idx = int(input("row no.: ")) # this is going to break
        else:
            row_idx = 0
        return ein_index_df.iloc[row_idx].to_dict()
    else:
        return {}

def unzip_990_xml( zip_file: str, xml_file: str ) -> dict:
    try:
        with ZipFile(zip_file, 'r') as zf:
            np_990_dict = x2d.parse(zf.read(xml_file))
    except NotImplementedError:
        EncodingWarning("Compression type 9 (deflate64) not supported. Running `unzip` externally:")
        uz_proc = sp.Popen(f"unzip -p {zip_file} {xml_file}", stdout=sp.PIPE, shell=True)
        (uz_out, uz_err) = uz_proc.communicate()
        np_990_dict = x2d.parse(uz_out)
    return np_990_dict

def read_np_990_file( object_id: str, xml_batch_id: str, data_root_dir: str = DATA_DIR ) -> dict:
    zip_path = os.path.join(data_root_dir, f"{xml_batch_id}.zip")
    file_name = f"{object_id}_public.xml"
    if not os.path.exists(zip_path):
        download_xml_batch_zip(xml_batch_id)
    return unzip_990_xml(zip_path, file_name)

def download_xml_batch_zip( xml_batch_id: str, xbi_url_root: str = XBI_URL_ROOT, data_dir: str = DATA_DIR, verbose: bool = VERBOSE) -> None:
    year = xml_batch_id.split("_")[0]
    file_name = f"{xml_batch_id}.zip"
    file_save_path = os.path.join(data_dir, file_name)
    file_url = os.path.join(xbi_url_root, year, file_name)
    if verbose:
        print(f"Downloading XML batch archive: {xml_batch_id}")
        print(f"Saving archive to: {file_save_path}")
    urlretrieve(file_url, file_save_path)

def get_director_df( np_990_dict: dict ) -> pd.DataFrame:
    return pd.DataFrame(np_990_dict["Return"]["ReturnData"]["IRS990"]["Form990PartVIISectionAGrp"]) # is there a way to do this without separate strings?

def main():
    ap = ArgumentParser()
    ap.add_argument("ein", help="Employer ID Number of nonprofit, omit '-'", type=int)
    ap.add_argument("year", help="990 report year", default=2024, type=int)
    # ap.add_argument("--path", "-p", help="Output file path", default="./", type=str)  # worry about this later
    args = ap.parse_args()
    index_df = pd.read_csv(os.path.join(DATA_DIR,f"index_{args.year}.csv"))
    print(f"Searching for EIN {args.ein}:")
    ein_match_dict = get_index_row_from_ein(index_df, args.ein)
    print("Match found.")
    print(f"XML Batch: {ein_match_dict['XML_BATCH_ID']}")
    print(f"Object ID: {ein_match_dict['OBJECT_ID']}")
    np_990_dict = read_np_990_file(ein_match_dict["OBJECT_ID"], ein_match_dict["XML_BATCH_ID"])
    np_990_director_df = get_director_df(np_990_dict)
    dir_df_file_path = os.path.join("./",f"{ein_match_dict['TAXPAYER_NAME']} - IRS 990 {args.year}.csv")
    print(f"Saving director table to: {dir_df_file_path}")
    np_990_director_df.to_csv(f"{dir_df_file_path}", index=False)

if __name__ == "__main__":
    main()