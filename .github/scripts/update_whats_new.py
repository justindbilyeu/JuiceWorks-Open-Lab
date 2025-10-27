#!/usr/bin/env python3
import os, requests, datetime
from dateutil import parser as dtparser
from dateutil.tz import UTC

OWNER = "justindbilyeu"
EXCLUDE = {"JuiceWorks-Open-Lab", "juiceworks-open-lab", "JuiceWorks"}

NOW = datetime.datetime.now(tz=UTC)
SINCE = NOW - datetime.timedelta(days=14)

def gh(url, params=None):
    h={"Accept":"application/vnd.github+json"}
    tok=os.environ.get("GITHUB_TOKEN")
    if tok: h["Authorization"]=f"Bearer {tok}"
    r=requests.get(url,headers=h,params=params,timeout=30)
    r.raise_for_status()
    return r.json()

def public_repos(owner):
    out=[]; page=1
    while True:
        data=gh(f"https://api.github.com/users/{owner}/repos",{"per_page":100,"page":page,"sort":"updated"})
        if not data: break
        out+= [r for r in data if not r.get("private")]
        page+=1
    return [r for r in out if r["name"] not in EXCLUDE]

def recent_commits(repo):
    name=repo["name"]
    data=gh(f"https://api.github.com/repos/{OWNER}/{name}/commits",{"since":SINCE.isoformat(),"per_page":100})
    commits=[]
    for c in data:
        msg=(c.get("commit",{}).get("message") or "").splitlines()[0]
        date_str=c.get("commit",{}).get("author",{}).get("date") or c.get("commit",{}).get("committer",{}).get("date")
        dt=dtparser.parse(date_str).astimezone(UTC) if date_str else None
        commits.append({"sha":(c.get("sha") or "")[:7],"msg":msg,"url":c.get("html_url") or "", "date":dt})
    commits=[x for x in commits if x["date"] and x["date"]>=SINCE]
    commits.sort(key=lambda x:x["date"], reverse=True)
    return commits

def render(updates):
    lines=["# What's New (Auto-Updated)\n",
           f"_Window: last 14 days; generated {NOW.strftime('%Y-%m-%d %H:%M UTC')}._\n"]
    if not any(updates.values()):
        lines.append("> No updates in the last 14 days.\n")
        return "\n".join(lines)
    for repo, cs in updates.items():
        if not cs: continue
        lines.append(f"## {repo}\n")
        for c in cs[:20]:
            when=c["date"].strftime("%Y-%m-%d")
            lines.append(f"- {when} · [{c['sha']}]({c['url']}) — {c['msg']}")
        lines.append("")
    return "\n".join(lines)

def main():
    updates={}
    for r in public_repos(OWNER):
        updates[r["name"]] = recent_commits(r)
    os.makedirs("docs", exist_ok=True)
    with open("docs/whats-new.md","w",encoding="utf-8") as f:
        f.write(render(updates))

if __name__=="__main__": main()
