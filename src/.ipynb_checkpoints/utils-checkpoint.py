from datetime import timedelta, date, datetime

# a generator for the dates
def daterange(start_date: str, end_date: str) -> str:
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

    for i in range(int((end_datetime - start_datetime).days)):
        this_date = start_datetime + timedelta(i)
        yield datetime.strftime(this_date, '%Y-%m-%d')


def is_weekday(date: str) -> bool:
    """
    Is the market open on this day
    """
    formatted_date = datetime.strptime(date, '%Y-%m-%d')
    day = formatted_date.weekday()
    #monday is zero, sunday is 6
    if (day == 5 or day == 6):
        return False
    else:
        return True
    
def date_n_day_from(date: str, delta: int):
    """
    utility function to find the date n days from now
    """
    formatted_date = datetime.strptime(date, '%Y-%m-%d')
    new_date = formatted_date + timedelta(days=delta)
    new_date_str = datetime.strftime(new_date, '%Y-%m-%d')

    return new_date_str