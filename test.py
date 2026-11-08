from ingestion.raw import to_rows
from processing.extract_transforme import pattern, pattern_success, pattern_failed, pattern_repeated

rows = to_rows('./data')

total = len(rows)
general = ok = ko = rep = 0
not_matched = []

for row in rows:
    m = pattern.match(row.strip())
    if not m:
        not_matched.append(row)
        continue
    general += 1

    message = m['message']
    r = pattern_repeated.match(message)
    if r:
        rep += 1
        message = r['inner']

    if pattern_success.match(message):
        ok += 1
    elif pattern_failed.match(message):
        ko += 1

print('rows               :', total)
print('general pattern    :', general, '| not matched:', len(not_matched))
print('repeated pattern   :', rep)
print('success pattern    :', ok)
print('failed pattern     :', ko)
print(not_matched[:5])