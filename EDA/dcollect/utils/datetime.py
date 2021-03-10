import datetime

def year_range(year, datetime_o = datetime.datetime):
    return (
        datetime_o.min.replace(year = year),
        datetime_o.max.replace(year = year)
    )
