from datetime import date, datetime, timedelta
from typing import Optional, Tuple, Union

from odmantic.field import FieldProxy


def hints_date_range(field: Union[str, FieldProxy], at: Optional[Tuple[date, date]]):
    result = {}
    if at:
        if at[0]:
            result["$gte"] = datetime(year=at[0].year, month=at[0].month, day=at[0].day)
        if at[1]:
            result["$lt"] = datetime(
                year=at[1].year, month=at[1].month, day=at[1].day
            ) + timedelta(days=1)

    if not result:
        if isinstance(field, FieldProxy):
            return {+field: result}
        return {field: result}

    return result
