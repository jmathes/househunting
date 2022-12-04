#!/usr/bin/env python

import math
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tinker import dump as tdump

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
# https://docs.google.com/spreadsheets/d/1CAZ9f7KJ5pHpuwvbkddo2DsazQFuXMF8lRi8rNh_leE/edit?usp=sharing
# https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms' # Sample
SAMPLE_SPREADSHEET_ID = '1CAZ9f7KJ5pHpuwvbkddo2DsazQFuXMF8lRi8rNh_leE' # Househunting
SAMPLE_RANGE_NAME = 'Sheet1!A1:AZ100'

COLSTATS_ROWS = 4


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                    range=SAMPLE_RANGE_NAME).execute()

        values = result.get('values', [])

        def transform(value, format):
            if format == "number":
                return float(value.replace(",", "")) if not isinstance(value, float) else value
            elif format == "money":
                return float(value.replace("$", "").replace(",", "")) if not isinstance(value, float) else value
            elif format == "duration":
                hours, minutes, seconds = value.split(":")
                return float(3600 * int(hours) + 60 * int(minutes) + int(seconds)) if not isinstance(value, float) else value
            return value

        colstats = {
            title: [(row[i] if len(row) > i and len(row[i]) > 0 else None) for row in values[1:COLSTATS_ROWS + 1]]
            for i, title in enumerate(values[0])
        }
        colstats = {
            title: {
                colstats["Name"][i] : colvals[i]
                for i in range(COLSTATS_ROWS)
            }
            for (title, colvals) in colstats.items()
            if all(colval is not None for colval in colvals)
        }

        columns = {
            title: [
                (
                    transform(row[i], colstats[title]["Format"] if title in colstats else None)
                    if len(row) > i and len(row[i]) > 0 else None
                )
                for row in values[COLSTATS_ROWS + 1:]
            ]
            for i, title in enumerate(values[0])
        }

        colstats = {
            title: {
                stat : (
                    max(columns[title]) if value == "max"
                    else min(columns[title]) if value == "min"
                    else value
                )
                for stat, value in colstat.items()
            }
            for title, colstat in colstats.items()
            if title != "Name"
        }
        colstats = {
            title: {
                stat: (
                    transform(value, colstat["Format"]) if stat == "Stdev"
                    else transform(value, "number") if stat != "Format"
                    else value
                )
                for stat, value in colstat.items()
            }
            for title, colstat in colstats.items()
        }

        houses = {
            title: {
                name: (values[i] if i < len(values) else None)
                for name, values in columns.items()
            }
            for i, title in enumerate(columns["Name"])
        }

        def single_eval(actual, target, stdev, weight):
            return weight * (abs(actual - target) / stdev) ** 2 + 0.5
            return float(
                str(
                    int(
                        100 * weight * (abs(actual - target) / stdev) ** 2 + 0.5
                    )
                )
            ) / 100

        def evaluations(house, colstats):
            evals = {}
            for name, stats in colstats.items():
                if any(stat is None for stat in stats):
                    continue
                evals[name] = 10 - single_eval(house[name], stats["Target"], stats["Stdev"], stats["Weight"])
            return evals

        def evaluate(house, colstats):
            numerator = 0
            denominator = 0
            for name, stats in colstats.items():
                if any(stat is None for stat in stats):
                    continue
                denominator += stats["Weight"]
                numerator += single_eval(house[name], stats["Target"], stats["Stdev"], stats["Weight"])
            return math.sqrt(numerator)


        def strf(s):
            if isinstance(s, str):
                return s
            return str(int(100 * s) / 100)




        finals = (sorted([
            (
                evaluate(house, colstats),
                name,
                evaluations(house, colstats),
            )
            for name, house in houses.items()
        ]))
        mfr = max(max(len(strf(final[0])) for final in finals), 8)
        mhc = max(max(len(strf(final[1])) for final in finals), 8)
        max_factors = {
            factor_name: max(max(len(strf(final[2][factor_name])), 7) for final in finals)
            for factor_name in finals[0][2]
        }

        def ml(s, l):
            return strf(s) + " " * (l - len(strf(s)))

        def print_row(codename, final_rating, individual_ratings):
            ratings = " ".join([
                ml(evaluation_factor, max_factors[factname]) for factname, evaluation_factor in individual_ratings.items()
            ])
            print(f"{ml(codename, mhc)}: {ml(final_rating, mfr)} {ratings}")


        print_row("house", "rating", {name: name for name in finals[0][2]})
        for final_rating, house_codename, evaluation_factors in finals:
            print_row(house_codename, 10 - final_rating, evaluation_factors)


    except HttpError as err:
        print(err)


if __name__ == '__main__':
    main()