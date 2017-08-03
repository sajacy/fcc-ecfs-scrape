# fcc-ecfs-scrape

Code used to extract FCC ECFS filings (Express Comments) into [BigQuery](https://bigquery.cloud.google.com).

The resulting dataset demonstrates the self-reported PII (personally-identifiable information) exposed via the FCC ECFS API.

## Dataset and Background

FCC proceeding 17-108, Restoring Internet Freedom, has made headlines as the FCC reconsiders the regulations around "net neutrality". It attracted over 22 million comments.

For those looking for a full analysis and write-up of the data, [Emprata](http://www.emprata.com/reports/fcc-restoring-internet-freedom-docket/) has a nice 25-page report.

While net neutrality is a truly important topic, I actually am motivated by a somewhat different aspect of this dataset: PII (personally-identifiable information).
Specifically, I find this dataset is an interesting instance of large-scale, highly-structured, fully-open, self-reported PII. This is a relatively rare find.  This information
can be used to cross-tabulate with other datasets such as voter registration and census data.  But - the first step was to extract the FCC comment filings themselves.

This dataset only contains the "meat" of the API data.  There are many status flags and other embedded references in the actual API responses that are omitted, 
although you could recreate the Emprata report from this dataset. That report goes into detail on the validity, strength, and direction of sentiment in the comments, whereas I am primarily
interested in the metadata: name, address, zip, and email. So, this dataset contains all the `addressentity` fields available from the FCC ECFS API, 
along with the `filer` name and `contact_email` fields. The `date_submission` and `id_submission` fields serve to order and uniquely identify each record.

One notable phenomenon in the data is the presence of "throwaway" email addresses. I want to be able to identify these records, since the vast majority are most likely robo-submitted, 
and thus, unlikely to actually be "self-reported" (they are likely from another database of PII, or worse, garbage data).  I've included a convenience table of email domains
that identify a "throwaway" email. See this [quick summary](https://bigquery.cloud.google.com/table/jyang:fcc_ecfs.frequency_and_unique_comment_by_domain) 
of the number of individual submissions and the number of unique comments (many are form letters) by email domain. Notice the "throwaway" domains have extremely similar statistics.

Please feel free to use this dataset in your own research.  If it's not already obvious, the dataset is licensed [CC0](http://creativecommons.org/about/cc0).

[BigQuery Dataset: jyang.fcc_ecfs](https://bigquery.cloud.google.com/dataset/jyang:fcc_ecfs)

## Extraction Tools / Method

BigQuery was the chosen target database, since it is a native component of the Google Cloud Platform (GCP) suite of data-processing tools.  
Based on previous experience, GCP has a valuable ecosystem for my intended research goals.

Python command-line scripts are fast to write and easy to test (though granted, I didn't write any formal unit tests)

I originally wrote one big script, but refactored into two modules:

1. A fetcher that writes JSON to STDOUT.
2. A streaming BQ loader that reads each JSON from STDIN and streams it into a given BigQuery table.

I thought maybe a BigQuery streamer might be generalized enough to be useful to someone else.

### Prerequisites to Run

You'll need to setup two accounts:

1. A [data.gov](https://api.data.gov/signup/) API key
2. A [GCP project](https://cloud.google.com/free/), free trial (and Always Free Tier)

### Usage

These scripts most easily run on a GCP Compute Engine instance, since all permissions and project settings are provided transparently. 
See [here for more info](https://cloud.google.com/bigquery/docs/reference/libraries#client-libraries-install-python) on the Python SDK.

For example, if you create a new Compute Engine instance and open the browser-based SSH window, you can download this repo and run it:

```
wget -O fcc.zip [repository tag 0.1 here]
gunzip fcc.zip

export APIKEY=[your data.gov API key]
# example: APIKEY=Taba893Gjq3rgqu3rkaj1kjbafk

# Just read a couple comments:
./fetch.py --limit 2 --paging 2 --startdate 2017-08-05 17-108

# Pipe the comments to BigQuery (streaming mode):
./fetch.py -l 2 -p 2 -sd 2017-08-05 17-108 | ./bqstream.py -d mydataset -t mytable redux-schema.json
```

