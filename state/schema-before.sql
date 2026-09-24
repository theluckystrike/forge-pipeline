CREATE TABLE contributions(
  id INTEGER PRIMARY KEY, ts TEXT, repo TEXT, issue INTEGER, pr INTEGER,
  category TEXT, score INTEGER, status TEXT, pr_url TEXT, notes TEXT);
CREATE TABLE runs(
  id INTEGER PRIMARY KEY, ts TEXT, layer TEXT, discovered INTEGER, verified INTEGER,
  perfect INTEGER, best_score INTEGER, best_repo TEXT, notes TEXT);
CREATE TABLE kpi(
  metric TEXT PRIMARY KEY, value TEXT, updated TEXT);
