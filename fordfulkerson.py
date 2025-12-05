#!/usr/bin/env python3
from collections import deque
import sys

def bfs(rgraph, s, e, parent):
    n = len(rgraph)
    visited = [False] * n
    q = deque()
    q.append(s)
    visited[s] = True
    parent[s] = -1

    while q:
        curr = q.popleft()
        for i in range(n):
            if rgraph[curr][i] > 0 and not visited[i]:
                visited[i] = True
                parent[i] = curr
                q.append(i)
                if i == e:
                    return True
    return False

def ford_fulkerson(g, s, e):
    n = len(g)
    max_flow = 0
    parent = [-1] * n
    # build residual graph as n x n matrix
    rgraph = [[0] * n for _ in range(n)]
    for u in range(n):
        for (v, cap) in g[u]:
            rgraph[u][v] = cap

    valid_paths = []

    while bfs(rgraph, s, e, parent):
        # find bottleneck
        node = e
        bottleneck = float('inf')
        while parent[node] != -1:
            par = parent[node]
            bottleneck = min(bottleneck, rgraph[par][node])
            node = par

        # update residual graph along path
        node = e
        while parent[node] != -1:
            par = parent[node]
            rgraph[par][node] -= bottleneck
            rgraph[node][par] += bottleneck
            node = par

        max_flow += bottleneck

        # build path (forward order)
        rev_path = []
        node = e
        while parent[node] != -1:
            rev_path.append(node)
            node = parent[node]
        rev_path.append(node)
        rev_path.reverse()
        valid_paths.append(rev_path)

        # reset parent for next BFS (bfs will set it again)
        parent = [-1] * n

    # print results to stdout
    print(int(max_flow))
    for path in valid_paths:
        print(" ".join(str(x) for x in path))

def main():
    # read from filename arg if provided, otherwise from stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            data = f.read().strip().split()
    else:
        data = sys.stdin.read().strip().split()

    if not data:
        return

    it = iter(data)
    try:
        N = int(next(it))
    except StopIteration:
        return
    E = int(next(it))
    g = [[] for _ in range(N)]
    for _ in range(E):
        src = int(next(it))
        dst = int(next(it))
        capacity = int(next(it))
        g[src].append((dst, capacity))
    s = int(next(it))
    e = int(next(it))
    ford_fulkerson(g, s, e)

if __name__ == "__main__":
    main()

# python3 fordfulkerson.py input.txt