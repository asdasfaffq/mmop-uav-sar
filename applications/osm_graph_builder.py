"""Build a real, projected city flight-graph from OpenStreetMap (Phase 10).

Downloads the street network for a city/point via OSMnx, projects it to metres,
and returns a simple undirected graph with node (x,y) coordinates and edge
`length` weights. UAVs are modelled as following low-altitude street corridors
(realistic for dense urban SAR while avoiding building collisions). Results are
cached on disk; everything is code/data-driven (no AI-generated maps).

CITY_PRESETS give reproducible (lat, lon, radius) anchors for the candidate cities.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import numpy as np

CACHE = Path(__file__).resolve().parent / ".osm_cache"

CITY_PRESETS = {
    "Macau":        dict(point=(22.1987, 113.5439), dist=1200),
    "Guangzhou":    dict(point=(23.1291, 113.2644), dist=1200),
    "Shenzhen":     dict(point=(22.5431, 114.0579), dist=1200),
    "HongKong":     dict(point=(22.2799, 114.1588), dist=1200),
    "SanFrancisco": dict(point=(37.7793, -122.4192), dist=1200),
}


@dataclass
class FlightGraph:
    name: str
    G: nx.Graph                 # simple undirected, 'length' weights
    nodes: np.ndarray           # (N, 2) projected xy in metres, indexed 0..N-1
    node_ids: list              # graph node id per index
    id_to_idx: dict
    bbox: tuple                 # (xmin, ymin, xmax, ymax)
    crs: object = None          # projected CRS (for real basemap alignment)

    def nearest_node(self, xy) -> int:
        d = np.linalg.norm(self.nodes - np.asarray(xy, float), axis=1)
        return int(np.argmin(d))

    def shortest_path_idx(self, i: int, j: int):
        """Return (length, [node-index path]) between two node indices."""
        si, sj = self.node_ids[i], self.node_ids[j]
        try:
            length = nx.shortest_path_length(self.G, si, sj, weight="length")
            path = nx.shortest_path(self.G, si, sj, weight="length")
            return float(length), [self.id_to_idx[n] for n in path]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float("inf"), [i, j]


def build_flight_graph(city: str = "Macau", use_cache: bool = True) -> FlightGraph:
    import osmnx as ox
    ox.settings.use_cache = use_cache
    ox.settings.cache_folder = str(CACHE)
    preset = CITY_PRESETS.get(city, CITY_PRESETS["Macau"])
    G = ox.graph_from_point(preset["point"], dist=preset["dist"], network_type="drive")
    G = ox.project_graph(G)
    # to simple undirected graph with length weights
    UG = nx.Graph()
    for u, v, data in G.edges(data=True):
        w = float(data.get("length", 1.0))
        if UG.has_edge(u, v):
            if w < UG[u][v]["length"]:
                UG[u][v]["length"] = w
        else:
            UG.add_edge(u, v, length=w)
    # keep the largest connected component (navigable)
    comps = sorted(nx.connected_components(UG), key=len, reverse=True)
    UG = UG.subgraph(comps[0]).copy()
    node_ids = list(UG.nodes())
    xy = np.array([[G.nodes[n]["x"], G.nodes[n]["y"]] for n in node_ids], float)
    id_to_idx = {n: i for i, n in enumerate(node_ids)}
    bbox = (xy[:, 0].min(), xy[:, 1].min(), xy[:, 0].max(), xy[:, 1].max())
    crs = G.graph.get("crs")
    return FlightGraph(city, UG, xy, node_ids, id_to_idx, bbox, crs=crs)


def synthetic_flight_graph(name="Synthetic", n=20, seed=0) -> FlightGraph:
    """Deterministic grid-like graph for offline tests (no network)."""
    rng = np.random.default_rng(seed)
    xs = np.linspace(0, 1000, n); ys = np.linspace(0, 1000, n)
    G = nx.Graph(); xy = []; ids = []
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            nid = i * n + j; ids.append(nid); xy.append([x, y]); G.add_node(nid)
    for i in range(n):
        for j in range(n):
            nid = i * n + j
            for di, dj in [(1, 0), (0, 1)]:
                if i + di < n and j + dj < n:
                    m = (i + di) * n + (j + dj)
                    G.add_edge(nid, m, length=float(np.hypot(xs[1] - xs[0], ys[1] - ys[0])))
    xy = np.array(xy, float)
    id_to_idx = {nid: k for k, nid in enumerate(ids)}
    bbox = (0, 0, 1000, 1000)
    return FlightGraph(name, G, xy, ids, id_to_idx, bbox)
