#include <iostream>
#include <algorithm>
#include <vector>
#include <queue>
#include <climits>

using namespace std;

bool BFS(const vector<vector<int>> &rGraph, int s, int e, vector<int> &parent, int vToken, vector<int> &visited)
{
    int N = rGraph.size();
    queue<int> q;
    q.push(s);
    visited[s] = vToken;
    parent[s] = -1;

    while (!q.empty())
    {
        int curr = q.front();
        q.pop();
        for (int i = 0; i < N; i++)
        {
            if (rGraph[curr][i] > 0 && visited[i] != vToken)
            {
                visited[i] = vToken;
                parent[i] = curr;
                q.push(i);
                if (i == e)
                {
                    return true;
                }
            }
        }
    }
    return false;
}

void fordFulkerson(const vector<vector<pair<int, int>>> &g, int s, int e)
{
    int N = g.size();
    int maxFlow = 0;
    vector<int> parent(N);
    vector<vector<int>> rGraph(N, vector<int>(N, 0));
    vector<vector<int>> validPaths;

    // build residual graph from adjacency list
    for (int i = 0; i < N; i++)
    {
        for (auto &nei : g[i])
        {
            int dst = nei.first;
            int cap = nei.second;
            rGraph[i][dst] = cap;
        }
    }

    vector<int> visited(N, 0);
    int vToken = 1;
    while (BFS(rGraph, s, e, parent, vToken, visited))
    {
        int bottleKneck = INT_MAX;

        // find min flow in the path using parent
        int node = e;
        while (parent[node] != -1)
        {
            int par = parent[node];
            bottleKneck = min(bottleKneck, rGraph[par][node]);
            node = par;
        }

        // subtract bottlekneck from the path in residual
        node = e;
        while (parent[node] != -1)
        {
            int par = parent[node];
            rGraph[par][node] -= bottleKneck;
            rGraph[node][par] += bottleKneck;
            node = par;
        }
        maxFlow += bottleKneck;
        vToken++;

        // build valid path
        vector<int> revPath;
        node = e;
        while (parent[node] != -1)
        {
            int par = parent[node];
            revPath.push_back(node);
            node = par;
        }
        revPath.push_back(node);
        reverse(revPath.begin(), revPath.end());
        validPaths.push_back(revPath);
    }

    cout << maxFlow << "\n";
    // print all paths

    for (auto &vec : validPaths)
    {
        for (auto &node : vec)
        {
            cout << node << " ";
        }
        cout << "\n";
    }
}

// This algorithm is to find max flow in a network
int main()
{

    int N, E;
    cin >> N >> E;

    vector<vector<pair<int, int>>> g(N);
    for (int i = 0; i < E; i++)
    {
        int src, dst, capacity;
        cin >> src >> dst >> capacity;
        // src--,dst--;
        g[src].emplace_back(dst, capacity);
    }
    int s, e;
    cin >> s >> e;
    fordFulkerson(g, s, e);

    return 0;
}

// g++ -std=c++17 -O2 -Wall -Wextra fordfulkerson.cpp -o fordfulkerson
// Get-Content input.txt -Raw | .\fordfulkerson.exe