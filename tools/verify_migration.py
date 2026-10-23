"""Migration continuity checks (operating model §8.1) for the macsmsf/hio -> hio subtree split."""
import re, subprocess, sys, posixpath, json
REPO, SRC, SPLIT = sys.argv[1], sys.argv[2], sys.argv[3]
def git(*a): return subprocess.run(["git","-C",REPO,*a],capture_output=True,text=True,check=True).stdout
def try_git(*a):
    r=subprocess.run(["git","-C",REPO,*a],capture_output=True,text=True); return r.stdout.strip() if r.returncode==0 else None
problems=[]

# 1. commit provenance map: match on author date + author + subject + body
fmt="%H%x1f%an%x1f%aI%x1f%B%x1e"
def commits(rev, *paths): 
    out=git("log","--format="+fmt,rev,*(["--",*paths] if paths else []))
    return [c.strip("\n").split("\x1f") for c in out.split("\x1e") if c.strip()]
src=commits(SRC,"hio"); new=commits(SPLIT)
key=lambda c:(c[1],c[2],c[3].strip())
srcmap={key(c):c[0] for c in src}
cmap={}
for c in new:
    k=key(c)
    if k not in srcmap: problems.append(f"split commit {c[0][:7]} has no source match")
    else: cmap[srcmap[k]]=c[0]
if len(cmap)!=len(new) or len(new)!=len(src): problems.append(f"commit count mismatch src={len(src)} new={len(new)} mapped={len(cmap)}")
print(f"[1] commits: source {len(src)}, split {len(new)}, mapped {len(cmap)}")

# 2. tree identity
st, nt = git("rev-parse",f"{SRC}:hio").strip(), git("rev-parse",f"{SPLIT}^{{tree}}").strip()
print(f"[2] tree: source {st} split {nt} -> {'IDENTICAL' if st==nt else 'DIFFERENT'}")
if st!=nt: problems.append("tree differs")

# 3. ids and states (front matter id/status/record_status) on both sides
files=[f for f in git("ls-tree","-r","--name-only",SPLIT).split() if f.endswith((".md",".yaml"))]
def fm(rev,path):
    t=try_git("show",f"{rev}:{path}") or ""
    m=re.match(r"---\n(.*?)\n---",t,re.S)
    if not m: return None
    d={}
    for line in m.group(1).splitlines():
        mm=re.match(r"(id|status|record_status|decision|accepted_by|approved_by):\s*(.*?)\s*(#.*)?$",line)
        if mm: d[mm.group(1)]=mm.group(2)
    return d or None
ids_src={f:fm(SRC,"hio/"+f) for f in files}; ids_new={f:fm(SPLIT,f) for f in files}
ids=[v for v in ids_new.values() if v and "id" in v]
diff=[f for f in files if ids_src[f]!=ids_new[f]]
print(f"[3] ids/states: {len(ids)} identified documents; differences: {len(diff)}")
if diff: problems.append(f"id/state differences: {diff}")

# 4. approved/accepted content at its approved revision, via the commit map
ods=[f for f in files if f.startswith("docs/decisions/owner/OD-")]
checked=0; skipped=[]
for f in ods:
    t=git("show",f"{SPLIT}:{f}")
    m=re.search(r"applies_to:\n(.*?)\n(?:related|---)",t,re.S)
    if not m: continue
    for path,rev in re.findall(r"- path:\s*(\S+)\s*\n\s*revision:\s*\"?([0-9a-f]{7,40})",m.group(1)):
        full=try_git("rev-parse",rev+"^{commit}")
        if not full: problems.append(f"{f}: revision {rev} not found"); continue
        if path.rstrip("/")=="hio":  # whole-directory instruction: compare the tree at that revision
            a=try_git("rev-parse",f"{full}:hio")
            nr=cmap.get(full)
            if nr is None:  # revision may be a commit not touching hio; use the nearest mapped ancestor
                anc=git("rev-list",full,"--","hio").split()[0]; nr=cmap.get(anc)
            b=try_git("rev-parse",f"{nr}^{{tree}}")
        else:
            rel=path[4:] if path.startswith("hio/") else None
            if rel is None: skipped.append(f"{f}: {path}"); continue
            a=try_git("rev-parse",f"{full}:{path}")
            nr=cmap.get(full) or cmap.get(git("rev-list",full,"--","hio").split()[0])
            b=try_git("rev-parse",f"{nr}:{rel}")
        checked+=1
        if a!=b: problems.append(f"{f}: {path}@{rev} source {a} vs split {b}")
print(f"[4] OD applies_to targets checked: {checked}; outside hio/ (not migrated, kept as macsmsf refs): {len(skipped)}")
for s in skipped: print("      ", s)

# 5. relative links resolve inside the split tree
tree=set(git("ls-tree","-r","--name-only",SPLIT).split())
dirs={posixpath.dirname(p) for p in tree}; 
alld=set()
for d in dirs:
    while d: alld.add(d); d=posixpath.dirname(d)
broken=[]
for f in [x for x in tree if x.endswith(".md")]:
    text=git("show",f"{SPLIT}:{f}")
    text=re.sub(r"```.*?```","",text,flags=re.S)
    for target in re.findall(r"\]\(([^)\s]+)\)",text):
        if re.match(r"[a-z]+:",target) or target.startswith("#"): continue
        p=target.split("#")[0]
        if not p: continue
        r=posixpath.normpath(posixpath.join(posixpath.dirname(f),p))
        if r not in tree and r not in alld: broken.append(f"{f} -> {target}")
print(f"[5] relative links: {len(broken)} unresolved")
for b in broken: print("      ", b)
if broken: problems.append(f"{len(broken)} unresolved links")

print("\nRESULT:", "PASS" if not problems else "DISCREPANCIES"); [print(" -",p) for p in problems]
json.dump({"commit_map":cmap},open(sys.argv[4],"w"),indent=1)
