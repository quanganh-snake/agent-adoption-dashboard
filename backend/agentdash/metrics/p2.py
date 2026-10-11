"""Metric calculations for the Agentic Much replication."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import median
from typing import Any
def adoption_estimate(
    all_file_level: int,
    commit_use_all_files: int,
    commit_only: int,
    total_repositories: int,
) -> dict[str, float]:
    """Reproduce the conservative and high estimates from paper [2], Table 1."""
    conservative_count = all_file_level + commit_only
    detection_rate = commit_use_all_files / all_file_level
    high_count = all_file_level + commit_only / detection_rate
    return {
        "conservative_pct": conservative_count * 100 / total_repositories,
        "high_pct": high_count * 100 / total_repositories,
    }


def histogram_median(histogram: dict[int, int]) -> int | float | None:
    total = sum(histogram.values())
    if total == 0:
        return None
    positions = ((total - 1) // 2, total // 2)
    values: list[int] = []
    cumulative = 0
    for value, count in sorted(histogram.items()):
        previous = cumulative
        cumulative += count
        for position in positions:
            if previous <= position < cumulative:
                values.append(value)
    return sum(values) / len(values)


def histogram_bin(value: int) -> int:
    import math
    return value if value <= 1000 else 1000 + math.floor(math.log2(value))




def _rows(db, sql: str, args=()):
    return [dict(row) for row in db.execute(sql, args).fetchall()]


def _pct(n, d):
    return round(n * 100 / d, 4) if d else None


def _month_end(month: str, current: date) -> str:
    year, number = map(int, month.split("-"))
    if year == current.year and number == current.month:
        return f"{month}-01"
    if number == 12:
        return date(year, 12, 31).isoformat()
    return date.fromordinal(date(year, number + 1, 1).toordinal() - 1).isoformat()


def series(db, months: list[str], ytd_until: date) -> dict[str, Any]:
    repos = _rows(db, "SELECT repo, as_of, adoption_date FROM p2_repo WHERE is_dotfiles=0 AND COALESCE(error,'')='' ")
    tools = _rows(db, "SELECT tool, adoption_date FROM p2_tool_adoption")
    commits = _rows(db, "SELECT month, auth_type, SUM(n) n FROM p2_commit_month GROUP BY month, auth_type")
    by_month = defaultdict(lambda: defaultdict(int))
    for row in commits: by_month[row['month']][row['auth_type']] += row['n']
    denominator=[]; adopters=[]; rates=[]; shares=[]
    for month in months:
        end = _month_end(month, ytd_until)
        sample = {r['repo'] for r in repos if r['as_of'] and r['as_of'][:10] >= end}
        adopted = sum(1 for r in repos if r['repo'] in sample and r['adoption_date'] and r['adoption_date'][:10] <= end)
        denominator.append(len(sample)); adopters.append(adopted); rates.append(_pct(adopted, len(sample)))
        counts=by_month[month]; shares.append(_pct(counts['AI'], counts['AI'] + counts['Human']))
    known_tools=sorted({r['tool'] for r in tools if r['tool']})
    return {'denominator': denominator, 'cumulative_adopters': adopters, 'adoption_rate_pct': rates,
            'new_adopters_by_tool': {tool:[sum(1 for r in tools if r['tool']==tool and (r['adoption_date'] or '')[:7]==m) for m in months] for tool in known_tools},
            'ai_commit_share_pct': shares}


def yearly(db, years: list[int], ytd_until: date) -> dict[str, Any]:
    months=[f'{year}-{month:02d}' for year in years for month in range(1, 13) if date(year, month, 1) <= ytd_until.replace(day=1)]
    data=series(db, months, ytd_until)
    result={'new_adopters':{}, 'adoption_rate_pct_year_end':{}, 'new_adopters_by_tool':{}, 'ai_commit_share_pct':{}, 'ratio_categories':{}, 'size_median':{}}
    for year in years:
        indexes=[i for i,m in enumerate(months) if m.startswith(str(year))]
        result['new_adopters'][str(year)] = (data['cumulative_adopters'][indexes[-1]] - (data['cumulative_adopters'][indexes[0]-1] if indexes[0] else 0)) if indexes else None
        result['adoption_rate_pct_year_end'][str(year)] = data['adoption_rate_pct'][indexes[-1]] if indexes else None
        result['ai_commit_share_pct'][str(year)] = _pct(sum((data['ai_commit_share_pct'][i] or 0)*data['denominator'][i] for i in indexes), sum(data['denominator'][i] for i in indexes)) if indexes else None
        result['new_adopters_by_tool'] = {t: {str(y): sum(v[i] for i,m in enumerate(months) if m.startswith(str(y))) for y in years} for t,v in data['new_adopters_by_tool'].items()}
    ratios=defaultdict(lambda: defaultdict(lambda: [0,0]))
    for row in _rows(db, "SELECT repo, month, auth_type, SUM(n) n FROM p2_commit_month GROUP BY repo, month, auth_type"):
        ratios[(row['repo'], row['month'][:4])][row['auth_type']][0] += row['n']
    cats=['None','Experimental','Limited','Consistent','Pervasive']
    for year in years:
        values=defaultdict(int)
        for (_, y), types in ratios.items():
            if y != str(year): continue
            ai, human=types['AI'][0], types['Human'][0]
            if ai+human < 10: continue
            p=100*ai/(ai+human); values['None' if p == 0 else 'Experimental' if p < 1 else 'Limited' if p < 5 else 'Consistent' if p < 20 else 'Pervasive'] += 1
        total=sum(values.values()); result['ratio_categories'][str(year)]={c:_pct(values[c],total) for c in cats}
    histogram=_rows(db,"SELECT year,auth_type,metric,bin,n FROM p2_commit_size")
    for year in years:
        result['size_median'][str(year)]={}
        for auth in ('AI','Human','Bot'):
            result['size_median'][str(year)][auth]={}
            for metric in ('added','deleted','files'):
                bins=[]
                for r in histogram:
                    if r['year']==year and r['auth_type']==auth and r['metric']==metric: bins.extend([r['bin']]*r['n'])
                result['size_median'][str(year)][auth][metric]=median(bins) if bins else None
    return result
