# git-ls-tree

Browse the file tree of a git repository **across all branches** in a local webpage.

Run it inside any git repository and it opens an interactive viewer showing the union of all file paths on every branch (names only, no content). Click a file to see which branches carry it, filter the tree by branch, or search by path.

## Install from a release

Each [release](https://github.com/Wadjinny/git-ls-tree/releases/latest) has a wheel you can install directly:

```sh
uv tool install https://github.com/Wadjinny/git-ls-tree/releases/download/v0.1.0/git_ls_tree-0.1.0-py3-none-any.whl
```

## Run locally

From this repo (browses this project's own branches):

```sh
uv sync
uv run git-ls-tree
```

Or install the tool and run it inside any other git repo:

```sh
uv tool install .        # or: pip install .
cd some-git-repo
git-ls-tree
```

This collects the file listing of every local branch, writes it to a temporary JSON file, and serves a viewer page on localhost (opened in the browser automatically). Press `Ctrl+C` to stop. The temporary file is deleted on exit.

Note: invoke it with the dash (`git-ls-tree`); `git ls-tree` runs the git builtin.

### Options

| Flag        | Effect                                                  |
| ----------- | ------------------------------------------------------- |
| `--remotes` | also include remote-tracking branches (`origin/...`)    |
| `--port N`  | serve on a fixed port (default: OS picks a free one)    |
| `--no-open` | don't open the browser automatically                    |

### The viewer

- **Tree** — collapsible folders; each file shows per-branch presence dots and an `N/M` ratio. Files missing from some branches are flagged in amber.
- **Detail panel** — click a file to list the branches it is present on and missing from.
- **Branch filter** — checkboxes per branch; a file stays visible while it exists on at least one selected branch.
- **Path filter** — substring search (`/` focuses the box, `Esc` clears).

## How it works

`git for-each-ref` discovers branches, `git ls-tree -r --name-only` lists each branch's files, and the result is served as `/data.json` by a small stdlib HTTP server alongside a self-contained HTML page. No dependencies beyond Python 3.13 and git.
