'''
Filter articles based on a list of keywords. If the headline contains one of the keywords, take it and store all valid in a csv file `<name>_filtered.csv`.
'''

import pandas as pd
def filter_articles(input_file, keywords, output_file):
    """
    Filter articles based on keywords in the headline.

    :param input_file: Path to the input CSV file containing articles.
    :param keywords: List of keywords to filter headlines.
    :param output_file: Path to save the filtered articles.
    """
    # Read the input CSV file
    df = pd.read_csv(input_file)

    # Filter articles where 'headline' contains any of the keywords
    filtered_df = df[df['headline'].str.contains('|'.join(keywords), case=False, na=False)]

    # Save the filtered DataFrame to a new CSV file
    filtered_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    # Example usage
    input_file = 'truy_quet_buon_lau_hang_gia.csv'  # Replace with your input file path
    keywords = ['thuốc', 'dược phẩm', 'thuốc chữa bệnh', 'thực phẩm chức năng', 'y tế', 'mỹ phẩm']
    output_file = 'truy_quet_buon_lau_hang_gia_filtered.csv'  # Replace with your desired output file path

    filter_articles(input_file, keywords, output_file)
    print(f"Filtered articles saved to {output_file}")
    