from irs990lib import *
from argparse import ArgumentParser

def parse_input():
    ap = ArgumentParser()
    ap.add_argument("ein", help="Employer ID Number of nonprofit, omit '-'", type=int)
    ap.add_argument("year", help="990 report year", default=2024, type=int)
    # ap.add_argument("--path", "-p", help="Output file path", default="./", type=str)  # worry about this later
    args = ap.parse_args()
    return args

def main():
    args = parse_input()
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