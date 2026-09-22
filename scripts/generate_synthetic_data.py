"""Generate the entirely fictional multi-format survey ecosystem."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import numpy as np
import pandas as pd
import pyreadstat


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "synthetic" / "sources"
N = 24


def normalize_sav_creation_stamp(path: Path) -> None:
    """Replace writer clock metadata so regenerated synthetic SAV bytes are stable."""
    data = bytearray(path.read_bytes())
    match = re.search(rb"\d{2} [A-Z][a-z]{2} \d{2}\d{2}:\d{2}:\d{2}", bytes(data[:220]))
    if match is None:
        raise RuntimeError(f"SPSS creation stamp not found in {path.name}")
    replacement = b"01 Jan 2600:00:00"
    data[match.start() : match.end()] = replacement
    path.write_bytes(data)


def base(offset: int = 0) -> dict[str, list[float | int]]:
    employment = [1 if i % 6 < 4 else (2 if i % 6 == 4 else 3) for i in range(N)]
    return {
        "age": [18 + ((i * 3 + offset) % 58) for i in range(N)],
        "employment": employment,
        "route": [1 if value == 1 else 0 for value in employment],
        "income": [24000 + ((i * 7300 + offset * 1100) % 116000) for i in range(N)],
        "weight": [round(0.72 + ((i + offset) % 9) * 0.07, 3) for i in range(N)],
    }


def routed_scale(route: list[int], offset: int, minimum: int = 1) -> list[float]:
    values: list[float] = []
    for i, eligible in enumerate(route):
        values.append(float(minimum + ((i + offset) % 5)) if eligible else np.nan)
    return values


def write_civiclife() -> None:
    b = base(0)
    auto = routed_scale(b["route"], 0)
    auto[8] = -8
    income = list(b["income"])
    income[7] = -9
    trust = [1 + ((i + 2) % 5) for i in range(N)]
    trust[9] = -9
    frame = pd.DataFrame(
        {
            "case_id": [1001 + i for i in range(N)],
            "age_years": b["age"],
            "sex": [1 if i % 2 == 0 else 2 for i in range(N)],
            "educ3": [1 + (i % 3) for i in range(N)],
            "labour": b["employment"],
            "hh_income_annual": income,
            "auto_rev": auto,
            "trust_index": trust,
            "community_member": [1 if i % 3 == 0 else 2 for i in range(N)],
            "work_module": b["route"],
            "weight": b["weight"],
        }
    )
    pyreadstat.write_sav(
        frame,
        str(OUT / "civiclife_2018.sav"),
        file_label="Fictional CivicLife Survey 2018",
        column_labels={
            "case_id": "Synthetic respondent identifier",
            "age_years": "Age in completed years",
            "sex": "Gender code",
            "educ3": "Highest education group",
            "labour": "Current employment status",
            "hh_income_annual": "Annual household income in fictional credits",
            "auto_rev": "Work autonomy, reverse direction",
            "trust_index": "Trust in public institutions",
            "community_member": "Community activity participation",
            "work_module": "Eligible for work module",
            "weight": "Synthetic survey weight",
        },
        variable_value_labels={
            "sex": {1: "Man", 2: "Woman"},
            "educ3": {1: "Lower secondary or less", 2: "Upper secondary", 3: "Tertiary"},
            "labour": {1: "Employed", 2: "Unemployed", 3: "Not in labor force"},
            "community_member": {1: "Yes", 2: "No"},
            "work_module": {0: "Not eligible", 1: "Eligible"},
        },
    )
    normalize_sav_creation_stamp(OUT / "civiclife_2018.sav")

    b = base(2)
    autonomy = routed_scale(b["route"], 1, minimum=0)
    autonomy[14] = 98
    income = list(b["income"])
    income[5] = 999999
    trust = [1 + ((i + 1) % 5) for i in range(N)]
    trust[11] = 99
    frame = pd.DataFrame(
        {
            "respondent_id": [2001 + i for i in range(N)],
            "age": b["age"],
            "gender_code": [0 if i % 2 == 0 else 1 for i in range(N)],
            "education_code": [10 * (1 + (i % 3)) for i in range(N)],
            "employment_code": b["employment"],
            "income_year": income,
            "autonomy_0_4": autonomy,
            "trust_score": trust,
            "participated": [1 if i % 4 < 2 else 0 for i in range(N)],
            "module_flag": b["route"],
            "survey_weight": b["weight"],
        }
    )
    pyreadstat.write_sav(
        frame,
        str(OUT / "civiclife_2020.sav"),
        file_label="Fictional CivicLife Survey 2020",
        column_labels={
            "respondent_id": "Synthetic respondent identifier",
            "age": "Age in completed years",
            "gender_code": "Gender code",
            "education_code": "Highest education code",
            "employment_code": "Current employment code",
            "income_year": "Annual household income in fictional credits",
            "autonomy_0_4": "Work autonomy from zero to four",
            "trust_score": "Trust in public institutions",
            "participated": "Community activity participation",
            "module_flag": "Eligible for work module",
            "survey_weight": "Synthetic survey weight",
        },
        variable_value_labels={
            "gender_code": {0: "Woman", 1: "Man"},
            "education_code": {10: "Lower", 20: "Upper", 30: "Tertiary"},
            "employment_code": {1: "Employed", 2: "Unemployed", 3: "Not in labor force"},
            "participated": {0: "No", 1: "Yes"},
            "module_flag": {0: "Not eligible", 1: "Eligible"},
        },
    )
    normalize_sav_creation_stamp(OUT / "civiclife_2020.sav")

    b = base(4)
    control = routed_scale(b["route"], 2)
    control[20] = 97
    income = list(b["income"])
    income[13] = -99
    frame = pd.DataFrame(
        {
            "rid": [3001 + i for i in range(N)],
            "age_yrs": b["age"],
            "gender": [1 if i % 5 < 2 else (2 if i % 5 < 4 else 3) for i in range(N)],
            "edu_level": [["lower", "upper", "tertiary"][i % 3] for i in range(N)],
            "employ": [{1: 10, 2: 20, 3: 30}[value] for value in b["employment"]],
            "household_income": income,
            "control_score": control,
            "trust_index": [1 + ((i + 3) % 5) for i in range(N)],
            "community_part": [1 if i % 3 == 1 else 0 for i in range(N)],
            "work_module": b["route"],
            "weight": b["weight"],
        }
    )
    pyreadstat.write_sav(
        frame,
        str(OUT / "civiclife_2022.sav"),
        file_label="Fictional CivicLife Survey 2022",
        column_labels={
            "rid": "Synthetic respondent identifier",
            "age_yrs": "Age in completed years",
            "gender": "Gender code",
            "edu_level": "Highest education group",
            "employ": "Current employment status",
            "household_income": "Annual household income in fictional credits",
            "control_score": "Work autonomy score",
            "trust_index": "Satisfaction with local services",
            "community_part": "Community activity participation",
            "work_module": "Eligible for work module",
            "weight": "Synthetic survey weight",
        },
        variable_value_labels={
            "gender": {1: "Woman", 2: "Man", 3: "Nonbinary or other"},
            "employ": {10: "Employed", 20: "Unemployed", 30: "Not in labor force"},
            "community_part": {0: "No", 1: "Yes"},
            "work_module": {0: "Not eligible", 1: "Eligible"},
        },
    )
    normalize_sav_creation_stamp(OUT / "civiclife_2022.sav")


def write_household_paths() -> None:
    b = base(1)
    school = [8 + (i % 11) for i in range(N)]
    school[6] = -9
    income = list(b["income"])
    income[17] = -9
    control = routed_scale(b["route"], 1)
    trust = [float((i + 1) % 5) for i in range(N)]
    trust[15] = -8
    frame = pd.DataFrame(
        {
            "pid": [4001 + i for i in range(N)],
            "age": b["age"],
            "sex_code": [1 if i % 2 == 0 else 2 for i in range(N)],
            "schooling_years": school,
            "employment_code": b["employment"],
            "hh_inc_year": income,
            "job_control": control,
            "trustgov_0_4": trust,
            "work_route": b["route"],
            "pweight": b["weight"],
        }
    )
    frame.to_stata(
        OUT / "household_paths_2019.dta",
        write_index=False,
        version=118,
        time_stamp=datetime(2026, 1, 1),
        variable_labels={
            "pid": "Synthetic respondent identifier",
            "age": "Age in completed years",
            "sex_code": "Gender code",
            "schooling_years": "Completed years of education",
            "employment_code": "Current employment code",
            "hh_inc_year": "Annual household income in fictional credits",
            "job_control": "Work autonomy score",
            "trustgov_0_4": "Trust in public institutions from zero to four",
            "work_route": "Eligible for work module",
            "pweight": "Synthetic survey weight",
        },
        value_labels={
            "sex_code": {1: "Woman", 2: "Man"},
            "employment_code": {1: "Employed", 2: "Unemployed", 3: "Not in labor force"},
            "work_route": {0: "Not eligible", 1: "Eligible"},
        },
    )

    b = base(3)
    resources = list(b["income"])
    resources[4] = -7
    latitude = routed_scale(b["route"], 3)
    latitude[8] = -8
    trust = [1 + ((i + 4) % 5) for i in range(N)]
    trust[12] = -9
    frame = pd.DataFrame(
        {
            "person_key": [5001 + i for i in range(N)],
            "age_yrs": b["age"],
            "gender_text": [["W", "M", "X"][i % 3] for i in range(N)],
            "qualification": [1 + (i % 3) for i in range(N)],
            "labor_state": b["employment"],
            "annual_hh_resources": resources,
            "decision_latitude": latitude,
            "public_trust": trust,
            "volunteer": [1 if i % 5 < 2 else 0 for i in range(N)],
            "work_eligible": b["route"],
            "weight": b["weight"],
        }
    )
    frame.to_stata(
        OUT / "household_paths_2021.dta",
        write_index=False,
        version=118,
        time_stamp=datetime(2026, 1, 1),
        variable_labels={
            "person_key": "Synthetic respondent identifier",
            "age_yrs": "Age in completed years",
            "gender_text": "Gender category",
            "qualification": "Highest qualification group",
            "labor_state": "Current employment status",
            "annual_hh_resources": "Annual household income in fictional credits",
            "decision_latitude": "Work autonomy, reverse direction",
            "public_trust": "Trust in public institutions",
            "volunteer": "Community activity participation",
            "work_eligible": "Eligible for work module",
            "weight": "Synthetic survey weight",
        },
        value_labels={
            "qualification": {1: "Lower", 2: "Upper", 3: "Tertiary"},
            "labor_state": {1: "Employed", 2: "Unemployed", 3: "Not in labor force"},
            "volunteer": {0: "No", 1: "Yes"},
            "work_eligible": {0: "Not eligible", 1: "Eligible"},
        },
    )


def write_values_work() -> None:
    b = base(5)
    income: list[str | int] = list(b["income"])
    income[10] = "NA_CODE"
    control = routed_scale(b["route"], 4)
    trust = [1 + ((i + 2) % 5) for i in range(N)]
    trust[16] = 99
    frame = pd.DataFrame(
        {
            "respondent": [f"VW18-{i + 1:03d}" for i in range(N)],
            "age_years": b["age"],
            "gender_text": [["woman", "man", "nonbinary"][i % 3] for i in range(N)],
            "edu_code": [1 + (i % 3) for i in range(N)],
            "employment_text": [{1: "working", 2: "seeking", 3: "outside"}[value] for value in b["employment"]],
            "annual_household_income": income,
            "decision_control": control,
            "trust_score": trust,
            "community_flag": ["yes" if i % 4 == 0 else "no" for i in range(N)],
            "module_work": b["route"],
            "sample_weight": b["weight"],
        }
    )
    frame.to_csv(OUT / "values_work_2018.csv", index=False, lineterminator="\n", float_format="%.3f")

    b = base(7)
    autonomy = routed_scale(b["route"], 2)
    autonomy[14] = 98
    trust = [1 + ((i + 3) % 5) for i in range(N)]
    trust[18] = 99
    frame = pd.DataFrame(
        {
            "id": [f"VW21-{i + 1:03d}" for i in range(N)],
            "respondent_age": b["age"],
            "gender_code": [[10, 20, 30][i % 3] for i in range(N)],
            "qualification": [["basic", "upper", "degree"][i % 3] for i in range(N)],
            "employment_code": b["employment"],
            "monthly_personal_earnings": [1800 + (i * 240) for i in range(N)],
            "autonomy_score": autonomy,
            "institution_score": trust,
            "community_activity": [1 if i % 3 == 0 else 0 for i in range(N)],
            "work_route": ["eligible" if value else "not_eligible" for value in b["route"]],
        }
    )
    frame.to_csv(OUT / "values_work_2021.csv", index=False, lineterminator="\n", float_format="%.3f")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_civiclife()
    write_household_paths()
    write_values_work()
    print(f"generated 7 synthetic survey files in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
